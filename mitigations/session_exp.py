from datetime import datetime, timedelta

def generate_token_hardened(user_id, username, is_admin):
    return {
        'user_id': user_id,
        'username': username,
        'is_admin': is_admin,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=15)
    }

#def verify_token_hardened():
#    return jwt.decode(token, JWT_SECRET, algorithms=ALGORITHMS, options={"verify_exp": True})
