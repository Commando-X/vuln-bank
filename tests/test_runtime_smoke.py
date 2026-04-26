import importlib
import os
import subprocess
import sys
import tempfile
import textwrap
import types
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]


class HealthEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._install_fake_psycopg2()
        import database

        cls._original_init_connection_pool = database.init_connection_pool
        database.init_connection_pool = lambda *args, **kwargs: None

        if "app" in sys.modules:
            del sys.modules["app"]

        try:
            cls.app_module = importlib.import_module("app")
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest(f"App dependencies are not installed locally: {exc.name}") from exc

        cls.client = cls.app_module.app.test_client()

        database.init_connection_pool = cls._original_init_connection_pool

    @classmethod
    def _install_fake_psycopg2(cls):
        if "psycopg2" in sys.modules:
            return

        fake_psycopg2 = types.ModuleType("psycopg2")
        fake_pool_module = types.ModuleType("psycopg2.pool")
        fake_pool_module.SimpleConnectionPool = object
        fake_psycopg2.pool = fake_pool_module

        sys.modules["psycopg2"] = fake_psycopg2
        sys.modules["psycopg2.pool"] = fake_pool_module

    def test_healthz_returns_ok_when_database_is_available(self):
        with patch.object(self.app_module, "check_database_connection", return_value=True):
            response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok", "database": "up"})

    def test_healthz_returns_503_when_database_is_unavailable(self):
        with patch.object(self.app_module, "check_database_connection", return_value=False):
            response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"status": "error", "database": "down"})


class StartScriptTests(unittest.TestCase):
    def test_start_script_waits_for_db_initializes_schema_and_execs_gunicorn(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bin_dir = tmp_path / "bin"
            bin_dir.mkdir()

            self._write_fake_executable(
                bin_dir / "pg_isready",
                """
                #!/bin/sh
                COUNT_FILE="${TEST_TMPDIR}/pg_isready.count"
                count=0
                if [ -f "$COUNT_FILE" ]; then
                  count=$(cat "$COUNT_FILE")
                fi
                count=$((count + 1))
                printf '%s' "$count" > "$COUNT_FILE"
                if [ "$count" -lt 3 ]; then
                  exit 1
                fi
                exit 0
                """,
            )
            self._write_fake_executable(
                bin_dir / "sleep",
                """
                #!/bin/sh
                exit 0
                """,
            )
            self._write_fake_executable(
                bin_dir / "python",
                """
                #!/bin/sh
                printf '%s\n' "$@" > "${TEST_TMPDIR}/python.args"
                exit 0
                """,
            )
            self._write_fake_executable(
                bin_dir / "gunicorn",
                """
                #!/bin/sh
                printf '%s\n' "$@" > "${TEST_TMPDIR}/gunicorn.args"
                exit 0
                """,
            )

            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
                    "TEST_TMPDIR": tmp_dir,
                    "DB_HOST": "db",
                    "DB_PORT": "5432",
                    "DB_USER": "postgres",
                    "DB_NAME": "vulnerable_bank",
                    "PORT": "5100",
                    "WEB_CONCURRENCY": "3",
                    "GUNICORN_THREADS": "5",
                    "GUNICORN_TIMEOUT": "90",
                }
            )

            result = subprocess.run(
                ["sh", str(REPO_ROOT / "start.sh")],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertEqual((tmp_path / "pg_isready.count").read_text(), "3")

            python_args = (tmp_path / "python.args").read_text().splitlines()
            gunicorn_args = (tmp_path / "gunicorn.args").read_text().splitlines()

            self.assertEqual(python_args[0], "-c")
            self.assertIn("init_connection_pool(max_retries=30, retry_delay=2); init_db()", python_args[1])

            self.assertIn("--bind", gunicorn_args)
            self.assertIn("0.0.0.0:5100", gunicorn_args)
            self.assertIn("--workers", gunicorn_args)
            self.assertIn("3", gunicorn_args)
            self.assertIn("--threads", gunicorn_args)
            self.assertIn("5", gunicorn_args)
            self.assertIn("--timeout", gunicorn_args)
            self.assertIn("90", gunicorn_args)
            self.assertEqual(gunicorn_args[-1], "app:app")

    def _write_fake_executable(self, path, script):
        path.write_text(textwrap.dedent(script).lstrip())
        path.chmod(0o755)


if __name__ == "__main__":
    unittest.main()
