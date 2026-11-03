
from app.parsing.python_parser import PythonParser


class ParserRegistry:

    def __init__(self):
        self.parsers = {}

        # Register supported parsers.
        self.register("Python", PythonParser())

    def register(self, language, parser):
        self.parsers[language.lower()] = parser

    def get_parser(self, language):
        parser = self.parsers.get(language.lower())

        if parser is None:
            raise ValueError(
                f"No parser registered for language: {language}"
            )

        return parser

    def parse(self, language, file_path, source_code):
        parser = self.get_parser(language)

        return parser.parse(file_path, source_code)
