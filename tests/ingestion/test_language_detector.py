
import unittest

from app.ingestion.language_detector import LanguageDetector


class TestLanguageDetector(unittest.TestCase):

    def setUp(self):
        self.detector = LanguageDetector()

    def test_python(self):
        result = self.detector.detect("main.py")
        self.assertEqual(result.language, "Python")
        self.assertTrue(result.is_programming_language)

    def test_javascript(self):
        result = self.detector.detect("App.jsx")
        self.assertEqual(result.language, "JavaScript")

    def test_documentation(self):
        result = self.detector.detect("README.md")
        self.assertEqual(result.category, "documentation")

    def test_unknown(self):
        result = self.detector.detect("unknown.xyz")
        self.assertEqual(result.language, "Unknown")


if __name__ == "__main__":
    unittest.main()
