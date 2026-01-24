def login_hardened():
    """
    Hardened against SQL injection at login
    by adding parameterized queries.
    """

    query = "SELECT * FROM users WHERE username = %s AND password = %s;"
    print(f"Debug - Login query: {query}")  # Debug print

    return query

def create_admin_hardened():
    """
    Hardened against SQL injection when creating admin
    by adding parameterized queries.
    """

    query = "INSERT INTO users (username, password, account_number, is_admin) VALUES (%s, %s, %s, %s);"

    return query

