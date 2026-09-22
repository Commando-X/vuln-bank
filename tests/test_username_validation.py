import unittest

from username_validation import (
    USERNAME_MAX_LENGTH,
    username_validation_error,
)


class UsernameValidationTests(unittest.TestCase):
    def test_allows_letters_numbers_underscores_and_hyphens(self):
        for username in ('alice', 'user_123', 'security-tester', 'Admin01'):
            with self.subTest(username=username):
                self.assertIsNone(username_validation_error(username))

    def test_rejects_special_characters(self):
        for username in (
            '<script>alert(1)</script>',
            'name>',
            'first.last',
            'first last',
            "admin'--",
        ):
            with self.subTest(username=username):
                self.assertIsNotNone(username_validation_error(username))

    def test_rejects_missing_short_and_long_usernames(self):
        for username in (None, 123, '', 'ab', 'a' * (USERNAME_MAX_LENGTH + 1)):
            with self.subTest(username=username):
                self.assertIsNotNone(username_validation_error(username))


if __name__ == '__main__':
    unittest.main()
