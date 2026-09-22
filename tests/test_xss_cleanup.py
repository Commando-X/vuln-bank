import importlib
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]


def install_fake_psycopg2():
    try:
        import psycopg2  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    fake_psycopg2 = types.ModuleType("psycopg2")
    fake_psycopg2.connect = lambda **kwargs: None
    fake_pool_module = types.ModuleType("psycopg2.pool")
    fake_pool_module.PoolError = Exception
    fake_pool_module.ThreadedConnectionPool = object
    fake_psycopg2.pool = fake_pool_module
    sys.modules["psycopg2"] = fake_psycopg2
    sys.modules["psycopg2.pool"] = fake_pool_module


class FakeCursor:
    def __init__(self, rowcounts):
        self._rowcounts = iter(rowcounts)
        self.rowcount = 0
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params):
        self.calls.append((" ".join(query.split()), params))
        self.rowcount = next(self._rowcounts)


class FakeConnection:
    def __init__(self, rowcounts):
        self.cursor_instance = FakeCursor(rowcounts)
        self.commits = 0

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commits += 1


class XssCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install_fake_psycopg2()
        cls.cleanup = importlib.import_module("xss_cleanup")

    def test_cleanup_only_neutralizes_expired_stored_values(self):
        connection = FakeConnection([2, 3, 4])

        counts = self.cleanup.cleanup_expired_xss_payloads(connection, 15)

        self.assertEqual(counts, (2, 3, 4))
        self.assertEqual(connection.commits, 1)
        self.assertEqual(len(connection.cursor_instance.calls), 3)

        username_query, username_params = connection.cursor_instance.calls[0]
        bio_query, bio_params = connection.cursor_instance.calls[1]
        description_query, description_params = connection.cursor_instance.calls[2]

        self.assertIn("SET username = CONCAT", username_query)
        self.assertIn("WHERE username_xss_detected_at <=", username_query)
        self.assertIn("SET bio = NULL", bio_query)
        self.assertIn("WHERE bio_xss_detected_at <=", bio_query)
        self.assertIn("SET description = NULL", description_query)
        self.assertIn("WHERE description_xss_detected_at <=", description_query)
        self.assertEqual(username_params, (15,))
        self.assertEqual(bio_params, (15,))
        self.assertEqual(description_params, (15,))

    def test_cleanup_configuration_has_safe_numeric_fallbacks(self):
        with patch.dict(os.environ, {"TEST_XSS_SETTING": "invalid"}):
            self.assertEqual(
                self.cleanup.positive_int_from_env("TEST_XSS_SETTING", 15),
                15,
            )

        with patch.dict(os.environ, {"TEST_XSS_SETTING": "1"}):
            self.assertEqual(
                self.cleanup.positive_int_from_env(
                    "TEST_XSS_SETTING",
                    60,
                    minimum=5,
                ),
                5,
            )

    def test_intentional_xss_sinks_remain_vulnerable(self):
        admin_template = (REPO_ROOT / "templates" / "admin.html").read_text()
        dashboard_script = (REPO_ROOT / "static" / "dashboard.js").read_text()

        self.assertIn("{{ user[1]|safe }}", admin_template)
        self.assertIn("${user.username || 'N/A'}", admin_template)
        self.assertIn("${user.bio ? user.bio", admin_template)
        self.assertIn("bioDisplay.innerHTML = bio", dashboard_script)
        self.assertIn("${t.description}", dashboard_script)


if __name__ == "__main__":
    unittest.main()
