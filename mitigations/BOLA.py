from database import execute_query

def check_balance_hardened(current_user, account_number):
    """
    Hardened against BOLA. Checks current logged in user.
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
