from flask import jsonify, request
import datetime
import decimal
import hmac
import jwt
import logging
import os
import sqlite3  
from functools import wraps

logger = logging.getLogger(__name__)

# JWT signing key. Loaded from the environment so it is never committed.
# In production a missing key must fail closed, not fall back to a default.
_jwt_secret = os.environ.get('JWT_SECRET')
if not _jwt_secret:
    raise RuntimeError(
        'JWT_SECRET environment variable is required. Generate one with: '
        "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )
if len(_jwt_secret) < 32:
    raise RuntimeError('JWT_SECRET must be at least 32 characters long.')

# Narrowed to str for static analysis after the fail-closed checks above.
JWT_SECRET: str = _jwt_secret

# Only the algorithm actually used for signing is accepted for verification.
# Accepting 'none' enables algorithm-confusion attacks (CWE-347).
ALGORITHMS = ['HS256']

# Token lifetime. Tokens are short-lived so a leak has a bounded window.
TOKEN_TTL = datetime.timedelta(hours=1)

# Maximum time a transfer may take, used to bound the race window (CWE-362).
TRANSFER_TIMEOUT = 30


def generate_token(user_id, username, is_admin=False):
    """
    Generate a signed JWT with an enforced expiration (CWE-613).
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'user_id': user_id,
        'username': username,
        'is_admin': is_admin,
        'iat': now,
        'exp': now + TOKEN_TTL,
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token


def verify_token(token):
    """
    Verify a JWT strictly: signature, algorithm and expiry are all enforced.

    A token with a bad signature is rejected outright - there is no fallback
    to unsigned decoding, because that fallback made every signature check
    optional (CWE-347, CWE-287).
    """
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=ALGORITHMS,
            options={'require': ['exp', 'iat']},
        )
    except jwt.exceptions.ExpiredSignatureError:
        logger.info('Token verification failed: token expired')
        return None
    except jwt.exceptions.InvalidSignatureError:
        logger.info('Token verification failed: invalid signature')
        return None
    except jwt.exceptions.InvalidTokenError as e:
        # Log server-side only - never echo token internals to the client.
        logger.info('Token verification failed: %s', type(e).__name__)
        return None
    except Exception as e:
        logger.exception('Unexpected error during token verification')
        return None


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # The bearer credential is accepted from the Authorization header only.
        # Accepting it from the query string, form body or cookies leaks it into
        # access logs, browser history, Referer headers and proxy logs (CWE-598).
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Token is missing'}), 401

        scheme, _, credentials = auth_header.partition(' ')
        if scheme.lower() != 'bearer' or not credentials.strip():
            return jsonify({'error': 'Invalid authorization header'}), 401

        token = credentials.strip()

        current_user = verify_token(token)
        if current_user is None:
            return jsonify({'error': 'Invalid token'}), 401

        # The view runs outside the verification try/except so that a genuine
        # error inside the view surfaces as a 500 instead of a misleading 401.
        return f(current_user, *args, **kwargs)

    return decorated

# New API endpoints with JWT authentication
def init_auth_routes(app):
    @app.route('/api/login', methods=['POST'])
    def api_login():
        auth = request.get_json(silent=True)
        suspension_message = 'Your account has been suspended, contact support or walk in to any of our branch to resolve the issue'

        if not isinstance(auth, dict) or not auth.get('username') or not auth.get('password'):
            return jsonify({'error': 'Missing credentials'}), 401

        # Parameterized query: user input is bound, never interpolated (CWE-89).
        conn = sqlite3.connect('bank.db')
        try:
            c = conn.cursor()
            c.execute(
                "SELECT id, username, password, account_number, is_admin, is_suspended "
                "FROM users WHERE username = ?",
                (auth.get('username'),)
            )
            user = c.fetchone()
        finally:
            conn.close()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        # Passwords are stored in plaintext in this schema; compare them in
        # constant time so the comparison does not leak length or prefix
        # information through timing (CWE-256).
        if not hmac.compare_digest(str(user[2]), str(auth.get('password'))):
            return jsonify({'error': 'Invalid credentials'}), 401

        if len(user) > 5 and user[5]:
            return jsonify({'error': suspension_message}), 403

        token = generate_token(user[0], user[1], user[4])

        # Only the fields the client actually needs are returned. The previous
        # response leaked the internal account number, client IP and User-Agent
        # (CWE-200).
        return jsonify({
            'token': token,
            'user_id': user[0],
            'username': user[1],
            'is_admin': bool(user[4]),
        })

    @app.route('/api/check_balance', methods=['GET'])
    @token_required
    def api_check_balance(current_user):
        # Object-level authorization: a caller may only read their own account
        # unless they are an administrator (CWE-639).
        account_number = request.args.get('account_number')
        if not account_number:
            return jsonify({'error': 'Account number required'}), 400

        conn = sqlite3.connect('bank.db')
        try:
            c = conn.cursor()
            c.execute(
                "SELECT id, username, balance, account_number FROM users "
                "WHERE account_number = ?",
                (account_number,)
            )
            user = c.fetchone()
        finally:
            conn.close()

        if not user:
            return jsonify({'error': 'Account not found'}), 404

        if not current_user.get('is_admin') and user[0] != current_user.get('user_id'):
            return jsonify({'error': 'Forbidden'}), 403

        return jsonify({
            'username': user[1],
            'balance': user[2],
            'checked_by': current_user['username']
        })

    @app.route('/api/transfer', methods=['POST'])
    @token_required
    def api_transfer(current_user):
        data = request.get_json(silent=True)

        if not isinstance(data, dict) or not data.get('to_account') or data.get('amount') is None:
            return jsonify({'error': 'Missing transfer details'}), 400

        # Amount must be a positive, finite value. A negative amount previously
        # increased the sender's balance while decreasing the recipient's
        # (CWE-20, CWE-682).
        try:
            amount = decimal.Decimal(str(data.get('amount')))
        except (decimal.InvalidOperation, TypeError, ValueError):
            return jsonify({'error': 'Invalid amount'}), 400

        if not amount.is_finite() or amount <= 0:
            return jsonify({'error': 'Amount must be a positive, finite number'}), 400
        if amount > decimal.Decimal('1000000'):
            return jsonify({'error': 'Amount exceeds the maximum transfer limit'}), 400

        to_account = data.get('to_account')
        user_id = current_user['user_id']

        conn = sqlite3.connect('bank.db')
        try:
            c = conn.cursor()

            # The recipient must exist before any money is moved, otherwise the
            # debit silently succeeds with no credit.
            c.execute(
                "SELECT username, balance FROM users WHERE account_number = ?",
                (to_account,)
            )
            recipient = c.fetchone()
            if recipient is None:
                conn.rollback()
                return jsonify({'error': 'Recipient account not found'}), 404

            # The debit is a single conditional UPDATE, so the balance check
            # and the debit cannot be interleaved by a concurrent request
            # (CWE-362). rowcount tells us whether the guard held.
            c.execute(
                "UPDATE users SET balance = balance - ? "
                "WHERE id = ? AND balance >= ?",
                (float(amount), user_id, float(amount))
            )
            if c.rowcount != 1:
                conn.rollback()
                return jsonify({'error': 'Insufficient funds'}), 400

            c.execute(
                "UPDATE users SET balance = balance + ? WHERE account_number = ?",
                (float(amount), to_account)
            )
            conn.commit()

            c.execute(
                "SELECT username, balance FROM users WHERE account_number = ?",
                (to_account,)
            )
            recipient = c.fetchone()
            new_balance = c.execute(
                "SELECT balance FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()[0]
        finally:
            conn.close()

        return jsonify({
            'status': 'success',
            'new_balance': new_balance,
            'recipient': recipient[0],
            'recipient_new_balance': recipient[1]
        })
