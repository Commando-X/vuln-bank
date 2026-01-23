def login_hardened():
    """
    Hardened against SQL injection at login.
    Do this by adding parameterized queries.
    """

    query = "SELECT * FROM users WHERE username = %s AND password = %s;"
    print(f"Debug - Login query: {query}")  # Debug print

    return query
