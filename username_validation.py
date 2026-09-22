import re


USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')


def username_validation_error(username):
    if not isinstance(username, str):
        return 'Username is required'

    if not USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH:
        return (
            f'Username must be between {USERNAME_MIN_LENGTH} and '
            f'{USERNAME_MAX_LENGTH} characters'
        )

    if not USERNAME_PATTERN.fullmatch(username):
        return 'Username may only contain letters, numbers, underscores, and hyphens'

    return None
