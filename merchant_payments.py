from datetime import datetime, timezone
from functools import wraps
import hashlib
import hmac
import logging
import secrets
import random
import string
import time

from flask import jsonify, redirect, render_template, request
import jwt

import auth
from auth import verify_token
from database import execute_query

logger = logging.getLogger(__name__)


def mask_card_number(card_number):
    """
    Mask a card number, keeping only the last four digits.

    Full PAN and CVV must never leave the server (PCI-DSS 3.4 / CWE-359).
    """
    if not card_number:
        return None
    card_number = str(card_number)
    if len(card_number) <= 4:
        return '*' * len(card_number)
    return '*' * (len(card_number) - 4) + card_number[-4:]


def generate_merchant_api_key():
    """
    Generate a merchant API key.

    The key is 256 bits of output from a cryptographically secure source.
    The previous version derived it from a four-digit code, which left only
    10,000 possible keys and made every merchant key enumerable
    (CWE-330, CWE-321).
    """
    return f"vk_{secrets.token_hex(32)}"


def generate_authorization_code():
    """
    Generate a payment authorization code.

    The previous version combined a Unix timestamp with three random digits,
    which is trivially guessable. This uses the secrets module so the code
    cannot be predicted from the request time (CWE-330).
    """
    return f"AUTH{secrets.token_hex(8).upper()}"


def generate_merchant_token(merchant):
    """
    Generate a weak merchant JWT.
    merchant tuple shape: id, name, email, api_key, is_active, created_at
    """
    payload = {
        'merchant_id': merchant[0],
        'merchant_name': merchant[1],
        'merchant_email': merchant[2],
        'is_merchant': True,
        'iat': datetime.now(timezone.utc),
        # Tokens must expire (CWE-613). verify_token() requires this claim.
        'exp': datetime.now(timezone.utc) + auth.TOKEN_TTL,
    }
    return jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')


def merchant_tuple_to_dict(merchant):
    return {
        'id': merchant[0],
        'name': merchant[1],
        'email': merchant[2],
        'api_key': merchant[3],
        'is_active': merchant[4],
        'created_at': str(merchant[5]) if len(merchant) > 5 else None
    }


def get_merchant_from_request():
    """
    Resolve merchant identity from either a plaintext API key or weak JWT.
    """
    api_key = request.headers.get('X-Merchant-Api-Key')
    if api_key:
        # Parameterized query: the API key is bound, never interpolated (CWE-89).
        query = """
            SELECT id, name, email, api_key, is_active, created_at
            FROM merchants
            WHERE api_key = %s
        """
        merchants = execute_query(query, (api_key,))
        if merchants:
            return merchant_tuple_to_dict(merchants[0]), 'api_key'

    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if payload and payload.get('is_merchant'):
            merchant_id = payload.get('merchant_id')
            query = """
                SELECT id, name, email, api_key, is_active, created_at
                FROM merchants
                WHERE id = %s
            """
            merchants = execute_query(query, (merchant_id,))
            if merchants:
                return merchant_tuple_to_dict(merchants[0]), 'jwt'

    return None, None


def merchant_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            merchant, auth_method = get_merchant_from_request()
            if not merchant:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing or invalid merchant credentials',
                    'accepted_auth_methods': [
                        'X-Merchant-Api-Key',
                        'Authorization: Bearer <merchant_jwt>'
                    ]
                }), 401

            if not merchant.get('is_active'):
                return jsonify({
                    'status': 'error',
                    'message': 'Merchant account is inactive',
                    'merchant_id': merchant.get('id')
                }), 403

            merchant['auth_method'] = auth_method
            return f(merchant, *args, **kwargs)
        except Exception as e:
            logger.exception('Merchant API request failed')
            return jsonify({
                'status': 'error',
                'message': 'Request failed'
            }), 500
    return decorated


def record_merchant_payment(merchant_id, card_id, amount, currency, status, merchant_order_id, authorization_code=None, failure_reason=None):
    result = execute_query(
        """
        INSERT INTO merchant_payments
        (merchant_id, card_id, amount, currency, status, merchant_order_id, authorization_code, failure_reason)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (merchant_id, card_id, amount, currency, status, merchant_order_id, authorization_code, failure_reason)
    )
    return result[0][0] if result else None


def init_merchant_payment_routes(app):
    @app.route('/merchant')
    def merchant_home():
        return redirect('/merchant/login')

    @app.route('/merchant/register', methods=['GET'])
    def merchant_register_page():
        return render_template('merchant_register.html')

    @app.route('/merchant/login', methods=['GET'])
    def merchant_login_page():
        return render_template('merchant_login.html')

    @app.route('/merchant/dashboard', methods=['GET'])
    def merchant_dashboard_page():
        return render_template('merchant_dashboard.html')

    @app.route('/api/v1/merchants/register', methods=['POST'])
    def register_merchant():
        try:
            data = request.get_json() or {}
            name = data.get('name')
            email = data.get('email')
            password = data.get('password')
            api_key = generate_merchant_api_key()

            # Parameterized query: no user input is interpolated (CWE-89).
            query = """
                INSERT INTO merchants (name, email, password, api_key)
                VALUES (%s, %s, %s, %s)
                RETURNING id, name, email, api_key, is_active, created_at
            """
            result = execute_query(query, (name, email, password, api_key))

            if not result:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to register merchant'
                }), 500

            merchant = merchant_tuple_to_dict(result[0])
            token = generate_merchant_token(result[0])

            # The password is never echoed back, and the raw request is not
            # returned to the client (CWE-200, CWE-532).
            return jsonify({
                'status': 'success',
                'message': 'Merchant registered successfully',
                'merchant': merchant,
                'api_key': api_key,
                'token': token,
            })

        except Exception as e:
            logger.exception('Merchant registration failed')
            return jsonify({
                'status': 'error',
                'message': 'Failed to register merchant'
            }), 500

    @app.route('/api/v1/merchants/login', methods=['POST'])
    def login_merchant():
        try:
            data = request.get_json() or {}
            email = data.get('email')
            password = data.get('password')

            # Parameterized query: no user input is interpolated (CWE-89).
            # The stored password is selected so it can be compared in constant
            # time; it is never interpolated into the statement.
            query = """
                SELECT id, name, email, password, api_key, is_active, created_at
                FROM merchants
                WHERE email = %s
            """
            result = execute_query(query, (email,))

            if not result:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid merchant credentials'
                }), 401

            # Passwords are stored in plaintext in this schema; compare them in
            # constant time so timing does not leak the value (CWE-256).
            if not hmac.compare_digest(str(result[0][3]), str(password)):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid merchant credentials'
                }), 401

            # Drop the password column before the row is turned into a response.
            row = result[0]
            merchant = merchant_tuple_to_dict(row[:3] + row[4:])
            token = generate_merchant_token(row)

            return jsonify({
                'status': 'success',
                'message': 'Merchant login successful',
                'token': token,
                'api_key': merchant['api_key'],
                'merchant': merchant
            })

        except Exception as e:
            logger.exception('Merchant login failed')
            return jsonify({
                'status': 'error',
                'message': 'Merchant login failed'
            }), 500

    @app.route('/api/v1/merchants/me', methods=['GET'])
    @merchant_required
    def get_current_merchant(current_merchant):
        return jsonify({
            'status': 'success',
            # The merchant record is rebuilt without the API key, which is a
            # credential (CWE-200, CWE-532).
            'merchant': {
                k: v for k, v in current_merchant.items() if k != 'api_key'
            },
            'debug_info': {
                'auth_method': current_merchant.get('auth_method'),
                # The API key is a credential and is never echoed back
                # (CWE-200, CWE-532).
                'server_time': str(datetime.now())
            }
        })

    @app.route('/api/v1/payments/charge', methods=['POST'])
    @merchant_required
    def charge_card(current_merchant):
        try:
            data = request.get_json() or {}
            amount = float(data.get('amount'))
            currency = data.get('currency', 'USD')
            card_number = data.get('card_number')
            cvv = data.get('cvv')
            expiry_date = data.get('expiry_date')
            merchant_order_id = data.get('merchant_order_id')
            description = data.get('description', 'Merchant payment')

            # Parameterized query: the card number is bound, never interpolated
            # (CWE-89). CVV is selected for the authorization check only.
            card_query = """
                SELECT
                    vc.id,
                    vc.user_id,
                    vc.card_number,
                    vc.cvv,
                    vc.expiry_date,
                    vc.current_balance,
                    vc.is_frozen,
                    vc.is_active,
                    vc.currency,
                    vc.card_type,
                    vc.card_limit,
                    u.account_number,
                    u.username
                FROM virtual_cards vc
                JOIN users u ON vc.user_id = u.id
                WHERE vc.card_number = %s
            """
            card_result = execute_query(card_query, (card_number,))

            if not card_result:
                payment_id = record_merchant_payment(
                    current_merchant['id'], None, amount, currency, 'failed',
                    merchant_order_id, None, 'invalid_card_number'
                )
                return jsonify({
                    'status': 'error',
                    'message': 'Payment declined',
                    'payment_id': payment_id,
                    'failure_reason': 'invalid_card_number',
                    'debug_info': {
                        'auth_method': current_merchant.get('auth_method'),
                        'merchant_id': current_merchant.get('id'),
                        'merchant_name': current_merchant.get('name'),
                        # Masked: the submitted PAN must not be echoed back
                        # even on a decline (PCI-DSS / CWE-359).
                        'submitted_card_number': mask_card_number(card_number),
                        'submitted_card_last4': str(card_number)[-4:]
                    }
                }), 400

            card = card_result[0]
            card_id = card[0]
            stored_cvv = card[3]
            stored_expiry = card[4]
            card_balance = float(card[5])
            is_frozen = card[6]
            is_active = card[7]
            card_currency = card[8]

            failure_reason = None
            if str(stored_cvv) != str(cvv):
                failure_reason = 'invalid_cvv'
            elif str(stored_expiry) != str(expiry_date):
                failure_reason = 'invalid_expiry_date'
            elif is_frozen:
                failure_reason = 'card_frozen'
            elif not is_active:
                failure_reason = 'inactive_card'
            elif amount > card_balance:
                failure_reason = 'insufficient_card_balance'

            if failure_reason:
                payment_id = record_merchant_payment(
                    current_merchant['id'], card_id, amount, currency, 'failed',
                    merchant_order_id, None, failure_reason
                )
                return jsonify({
                    'status': 'error',
                    'message': 'Payment declined',
                    'payment_id': payment_id,
                    'failure_reason': failure_reason,
                    'debug_info': {
                        'auth_method': current_merchant.get('auth_method'),
                        'merchant_id': current_merchant.get('id'),
                        'merchant_name': current_merchant.get('name'),
                        'card_id': card_id,
                        'card_currency': card_currency,
                        'card_balance': card_balance,
                        'is_frozen': is_frozen,
                        'is_active': is_active
                    }
                }), 400

            authorization_code = generate_authorization_code()

            # Vulnerability: No idempotency, replay protection, amount limits, or transaction locking
            execute_query(
                """
                UPDATE virtual_cards
                SET current_balance = current_balance - %s, last_used_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (amount, card_id),
                fetch=False
            )

            execute_query(
                """
                INSERT INTO card_transactions
                (card_id, amount, merchant_name, transaction_type, status, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    card_id,
                    amount,
                    current_merchant['name'],
                    'merchant_payment',
                    'completed',
                    description
                ),
                fetch=False
            )

            payment_id = record_merchant_payment(
                current_merchant['id'], card_id, amount, currency, 'completed',
                merchant_order_id, authorization_code, None
            )

            return jsonify({
                'status': 'success',
                'message': 'Payment approved',
                'payment': {
                    'id': payment_id,
                    'merchant_id': current_merchant['id'],
                    'merchant_name': current_merchant['name'],
                    'merchant_order_id': merchant_order_id,
                    'authorization_code': authorization_code,
                    'amount': amount,
                    'currency': currency,
                    'status': 'completed',
                    'description': description,
                    'created_at': str(datetime.now())
                },
                'card_details': {
                    'card_id': card_id,
                    'user_id': card[1],
                    'account_number': card[11],
                    'username': card[12],
                    # Masked: the full PAN and the CVV must never be returned
                    # to a client (PCI-DSS / CWE-359).
                    'card_number': mask_card_number(card[2]),
                    'card_last4': str(card[2])[-4:],
                    'expiry_date': stored_expiry,
                    'card_currency': card_currency,
                    'requested_currency': currency,
                    'balance_before': card_balance,
                    'balance_after': card_balance - amount,
                    'card_type': card[9],
                    'card_limit': float(card[10])
                },
                'debug_info': {
                    'auth_method': current_merchant.get('auth_method'),
                    'merchant_id': current_merchant.get('id'),
                    'merchant_name': current_merchant.get('name'),
                    'processed_at': str(datetime.now())
                }
            })

        except Exception as e:
            logger.exception('Merchant payment lookup failed')
            return jsonify({
                'status': 'error',
                'message': 'Request failed',
                'debug_info': {
                    'auth_method': current_merchant.get('auth_method'),
                    'merchant_id': current_merchant.get('id'),
                    'merchant_name': current_merchant.get('name')
                }
            }), 500

    @app.route('/api/v1/payments/<int:payment_id>', methods=['GET'])
    @merchant_required
    def get_merchant_payment(current_merchant, payment_id):
        try:
            query = """
                SELECT
                    mp.id,
                    mp.merchant_id,
                    m.name,
                    m.email,
                    mp.card_id,
                    vc.card_number,
                    vc.cvv,
                    mp.amount,
                    mp.currency,
                    mp.status,
                    mp.merchant_order_id,
                    mp.authorization_code,
                    mp.failure_reason,
                    mp.created_at
                FROM merchant_payments mp
                JOIN merchants m ON mp.merchant_id = m.id
                LEFT JOIN virtual_cards vc ON mp.card_id = vc.id
                WHERE mp.id = %s
                AND mp.merchant_id = %s
            """
            result = execute_query(query, (payment_id, current_merchant['id']))

            if not result:
                return jsonify({
                    'status': 'error',
                    'message': 'Payment not found',
                    'payment_id': payment_id
                }), 404

            payment = result[0]
            return jsonify({
                'status': 'success',
                'payment': {
                    'id': payment[0],
                    'merchant_id': payment[1],
                    'merchant_name': payment[2],
                    'merchant_email': payment[3],
                    'card_id': payment[4],
                    # Masked: the full PAN must never be returned (PCI-DSS / CWE-359).
                    'card_number': mask_card_number(payment[5]),
                    'card_last4': str(payment[5])[-4:],
                    # The CVV is never returned by the API (PCI-DSS / CWE-359).
                    'amount': float(payment[7]),
                    'currency': payment[8],
                    'payment_status': payment[9],
                    'merchant_order_id': payment[10],
                    'authorization_code': payment[11],
                    'failure_reason': payment[12],
                    'created_at': str(payment[13])
                },
                'debug_info': {
                    'looked_up_by_merchant': current_merchant
                }
            })

        except Exception as e:
            logger.exception('Merchant API request failed')
            return jsonify({
                'status': 'error',
                'message': 'Request failed'
            }), 500

    @app.route('/api/v1/payments', methods=['GET'])
    @merchant_required
    def list_merchant_payments(current_merchant):
        try:
            query = """
                SELECT
                    mp.id,
                    mp.merchant_id,
                    m.name,
                    mp.card_id,
                    vc.card_number,
                    mp.amount,
                    mp.currency,
                    mp.status,
                    mp.merchant_order_id,
                    mp.authorization_code,
                    mp.failure_reason,
                    mp.created_at
                FROM merchant_payments mp
                JOIN merchants m ON mp.merchant_id = m.id
                LEFT JOIN virtual_cards vc ON mp.card_id = vc.id
                WHERE mp.merchant_id = %s
                ORDER BY mp.created_at DESC
            """
            payments = execute_query(query, (current_merchant['id'],))

            return jsonify({
                'status': 'success',
                'payments': [{
                    'id': payment[0],
                    'merchant_id': payment[1],
                    'merchant_name': payment[2],
                    'card_id': payment[3],
                    # Masked: the full PAN must never be returned (PCI-DSS / CWE-359).
                    'card_number': mask_card_number(payment[4]),
                    'card_last4': str(payment[4])[-4:],
                    'amount': float(payment[5]),
                    'currency': payment[6],
                    'payment_status': payment[7],
                    'merchant_order_id': payment[8],
                    'authorization_code': payment[9],
                    'failure_reason': payment[10],
                    'created_at': str(payment[11])
                } for payment in payments],
                'debug_info': {
                    'looked_up_by_merchant': current_merchant
                }
            })

        except Exception as e:
            logger.exception('Merchant API request failed')
            return jsonify({
                'status': 'error',
                'message': 'Request failed'
            }), 500

    @app.route('/api/v1/payments/merchant_id/<int:merchant_id>', methods=['GET'])
    @merchant_required
    def list_payments_by_merchant_id(current_merchant, merchant_id):
        try:
            # Object-level authorization: a merchant may only list its own
            # payments. Previously any authenticated merchant could read any
            # other merchant's transactions (CWE-639).
            if merchant_id != current_merchant.get('id'):
                return jsonify({
                    'status': 'error',
                    'message': 'Forbidden'
                }), 403

            query = """
                SELECT
                    mp.id,
                    mp.merchant_id,
                    m.name,
                    mp.card_id,
                    vc.card_number,
                    mp.amount,
                    mp.currency,
                    mp.status,
                    mp.merchant_order_id,
                    mp.authorization_code,
                    mp.failure_reason,
                    mp.created_at
                FROM merchant_payments mp
                JOIN merchants m ON mp.merchant_id = m.id
                LEFT JOIN virtual_cards vc ON mp.card_id = vc.id
                WHERE mp.merchant_id = %s
                ORDER BY mp.created_at DESC
            """
            payments = execute_query(query, (merchant_id,))

            return jsonify({
                'status': 'success',
                'merchant_id': merchant_id,
                'payments': [{
                    'id': payment[0],
                    'merchant_id': payment[1],
                    'merchant_name': payment[2],
                    'card_id': payment[3],
                    # Masked: the full PAN must never be returned (PCI-DSS / CWE-359).
                    'card_number': mask_card_number(payment[4]),
                    'card_last4': str(payment[4])[-4:],
                    'amount': float(payment[5]),
                    'currency': payment[6],
                    'payment_status': payment[7],
                    'merchant_order_id': payment[8],
                    'authorization_code': payment[9],
                    'failure_reason': payment[10],
                    'created_at': str(payment[11])
                } for payment in payments],
                'debug_info': {
                    'looked_up_by_merchant': current_merchant
                }
            })

        except Exception as e:
            logger.exception('Merchant API request failed')
            return jsonify({
                'status': 'error',
                'message': 'Request failed'
            }), 500
