from flask import jsonify
from database import execute_query
from datetime import datetime


def check_balance_hardened(current_user, account_number):
    """Hardened against BOLA.

    Checks current logged in user.
    Otherwise just a copy of the original check_balance() logic.
    """
    try:
        # Vulnerability: SQL Injection possible
        user = execute_query(
            # BOLA mitigation: confirm current logged-in user.
            "SELECT username, balance FROM users WHERE account_number = %s AND id = %s",
            (account_number, current_user['user_id'])
        )

        if user:
            # Vulnerability: Information disclosure
            return jsonify({
                'status': 'success',
                'username': user[0][0],
                'balance': float(user[0][1]),
                'account_number': account_number
            })
        return jsonify({
            'status': 'error',
            'message': 'Account not found or access denied'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def get_transaction_history_hardened(current_user, account_number):
    """Hardened against BOLA.

    Checks current logged in user.
    Otherwise just a copy of the original get_transaction_history() logic.
    """
    try:
        # Modified psql query verifies currently logged-in user by account number.
        query = """
            SELECT
                id,
                from_account,
                to_account,
                amount,
                timestamp,
                transaction_type,
                description
            FROM transactions
            WHERE (from_account = %s OR to_account = %s)
            AND (from_account IN (SELECT account_number FROM users WHERE id = %s)
                 OR to_account IN (SELECT account_number FROM users WHERE id = %s))
            ORDER BY timestamp DESC
            """

        params = (account_number, account_number, current_user['user_id'], current_user['user_id'])

        transactions = execute_query(query, params)

        # Vulnerability: Information disclosure
        transaction_list = [{
            'id': t[0],
            'from_account': t[1],
            'to_account': t[2],
            'amount': float(t[3]),
            'timestamp': str(t[4]),
            'type': t[5],
            'description': t[6]
            # 'query_used': query  # Vulnerability: Exposing SQL query
        } for t in transactions]

        return jsonify({
            'status': 'success',
            'account_number': account_number,
            'transactions': transaction_list,
            'server_time': str(datetime.now())  # Vulnerability: Server information disclosure
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'query': query,  # Vulnerability: Query exposure
            'account_number': account_number
        }), 500


def toggle_card_freeze_hardened(current_user, card_id):
    """Hardened for BOLA.

    Current user ID check added to psql query.
    """
    try:
        # Vulnerability: No CSRF protection
        query = """
            UPDATE virtual_cards
            SET is_frozen = NOT is_frozen
            WHERE id = %s AND user_id = %s
            RETURNING is_frozen
        """

        result = execute_query(query, (card_id, current_user['user_id']))

        if result:
            return jsonify({
                'status': 'success',
                'message': f"Card {'frozen' if result[0][0] else 'unfrozen'} successfully"
            })

        # 403 used to make forbidden status obvious.    
        return jsonify({
            'status': 'error',
            'message': 'Card not found or access denied'
        }), 403

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
