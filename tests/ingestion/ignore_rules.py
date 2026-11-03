
import unittest

from app.ingestion.ignore_rules import IgnoreRules


class TestIgnoreRules(unittest.TestCase):

    def setUp(self):
        self.rules = IgnoreRules()

    def test_normal_file_is_included(self):
        self.assertFalse(
            self.rules.should_ignore("app/main.py")
        )

    def test_virtual_environment_is_ignored(self):
        self.assertTrue(
            self.rules.should_ignore(
                ".venv/Lib/example.py"
            )
        )

    def test_pycache_is_ignored(self):
        self.assertTrue(
            self.rules.should_ignore(
                "app/__pycache__/main.pyc"
            )
        )

    def test_log_file_is_ignored(self):
        self.assertTrue(
            self.rules.should_ignore("app/debug.log")
        )

    def test_readme_is_included(self):
        self.assertFalse(
            self.rules.should_ignore("README.md")
        )

    def test_env_file_is_ignored(self):
        self.assertTrue(
            self.rules.should_ignore(".env")
        )

    def test_env_example_is_included(self):
        self.assertFalse(
            self.rules.should_ignore(".env.example")
        )

    def test_custom_directory_is_ignored(self):
        rules = IgnoreRules(
            extra_patterns=["generated/"]
        )

        self.assertTrue(
            rules.should_ignore("generated/output.py")
        )

    def test_windows_path_is_normalized(self):
        self.assertTrue(
            self.rules.should_ignore(
                ".venv\\Lib\\example.py"
            )
        )


if __name__ == "__main__":
    unittest.main()
