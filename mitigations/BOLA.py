# from flask import jsonify
# from database import execute_query
# from datetime import datetime

def check_balance_hardened():
    """Harden for BOLA.
    Parameterize the query.
    """
    return "SELECT username, balance FROM users WHERE account_number = %s AND id = %s"


def get_transaction_history_hardened():
    """Hardened for BOLA.
    Parametrized query.
    """
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
    return query


def toggle_card_freeze_hardened():
    """Hardened for BOLA.
    Parameterized query.
    """
    query = """
            UPDATE virtual_cards
            SET is_frozen = NOT is_frozen
            WHERE id = %s AND user_id = %s
            RETURNING is_frozen
        """
    return query


def get_card_transactions_hardened():
    query = """
            SELECT ct.*, vc.card_number
            FROM card_transactions ct
            JOIN virtual_cards vc ON ct.card_id = vc.id
            WHERE ct.card_id = %s AND user_id = %s
            ORDER BY ct.timestamp DESC
        """
    return query


def update_card_limit_hardened(update_fields):
    """Hardened for BOLA.
    Parameterized query.
    """
    query = f"""
            UPDATE virtual_cards
            SET {', '.join(update_fields)}
            WHERE id = %s AND user_id = %s
            RETURNING *
        """
    return query


def create_bill_payment_hardened():
    card_query = """
                SELECT current_balance, card_limit, is_frozen
                FROM virtual_cards
                WHERE id = %s AND user_id = %s
            """
    return card_query
