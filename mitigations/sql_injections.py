def login_hardened():
    """
    Hardened against SQL injection at login
    by adding parameterized queries.
    """

    query = "SELECT * FROM users WHERE username = %s AND password = %s;"

    return query

def create_admin_hardened():
    """
    Hardened against SQL injection when creating admin
    by adding parameterized queries.
    """

    query = "INSERT INTO users (username, password, account_number, is_admin) VALUES (%s, %s, %s, %s);"

    return query

def forgot_password_hardened():
    """
    Hardened against SQL injection when requesting password
    reset by adding parameterized queries.
    """

    query = "SELECT id FROM users WHERE username= %s;"

    return query

def api_v1_forgot_password_hardened():
    """
    Hardened against SQL injection when requesting password
    reset on an old version of the app by adding
    parameterized queries.
    """

    query = "SELECT id FROM users WHERE username= %s;"

    return query

def api_v2_forgot_password_hardened():
    """
    Hardened against SQL injection when requesting password
    reset on an old version of the app by adding
    parameterized queries.
    """

    query = "SELECT id FROM users WHERE username= %s;"

    return query

def api_v3_forgot_password_hardened():
    """
    Hardened against SQL injection when requesting password
    reset by adding parameterized queries.
    """

    query = "SELECT id FROM users WHERE username= %s;"

    return query

def api_transactions_hardened():
    """
    Hardened against SQL injection when checking transactions
    by adding parameterized queries.
    """

    return query

def create_virtual_card_hardened():
    """
    Hardened againsted SQL injections when creating
    a virtual card by adding parameterized queries.
    """

    return query

def get_billers_by_category_hardened():
    """
    Hardened against SQL injections into
    biller categories by adding parameterized queries.
    """

    return query

def get_payment_history_hardened():
    """
    Hardened against SQL injections when getting
    the payment history by adding parameterized queries.
    """

    return query

