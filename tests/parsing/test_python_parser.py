
import unittest

from app.parsing.python_parser import PythonParser


class TestPythonParser(unittest.TestCase):

    def setUp(self):
        self.parser = PythonParser()

    def test_extract_symbols(self):

        source = """
class Calculator:

    def add(self, a, b):
        return a + b

def multiply(a, b):
    return a * b
"""

        result = self.parser.parse("test.py", source)

        names = [
            symbol.qualified_name
            for symbol in result.symbols
        ]

        self.assertIn("Calculator", names)
        self.assertIn("Calculator.add", names)
        self.assertIn("multiply", names)

    def test_extract_imports(self):

        source = """
import pandas as pd
from pathlib import Path
from .models import User
"""

        result = self.parser.parse("test.py", source)

        self.assertEqual(len(result.imports), 3)

        self.assertEqual(
            result.imports[0].module,
            "pandas"
        )

        self.assertTrue(
            result.imports[2].is_relative
        )

    def test_syntax_error(self):

        result = self.parser.parse(
            "broken.py",
            "def broken(:"
        )

        self.assertEqual(
            result.status,
            "syntax_error"
        )


if __name__ == "__main__":
    unittest.main()
