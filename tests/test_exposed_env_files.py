import unittest

from exposed_env_files import EXPOSED_ENV_FILES


class ExposedEnvironmentFileTests(unittest.TestCase):
    def test_both_environment_files_are_available(self):
        self.assertEqual(set(EXPOSED_ENV_FILES), {'.env', '.env.bak'})

        for filename, contents in EXPOSED_ENV_FILES.items():
            with self.subTest(filename=filename):
                self.assertIn('APP_ENV=production', contents)
                self.assertIn('SECRET_KEY=', contents)
                self.assertIn('JWT_SECRET=', contents)
                self.assertIn('DB_PASSWORD=', contents)
                self.assertIn('DATABASE_URL=', contents)

    def test_current_and_backup_files_have_different_values(self):
        self.assertNotEqual(EXPOSED_ENV_FILES['.env'], EXPOSED_ENV_FILES['.env.bak'])


if __name__ == '__main__':
    unittest.main()
