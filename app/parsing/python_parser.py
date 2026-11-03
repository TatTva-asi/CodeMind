
import ast
from pathlib import Path

from app.parsing.parser_models import ParsedFile
from app.parsing.symbol_extractor import SymbolExtractor
from app.parsing.import_extractor import ImportExtractor


class PythonParser:

    def parse(self, file_path: str | Path, source_code: str):

        result = ParsedFile(
            file_path=str(file_path),
            language="Python"
        )

        try:
            # Convert source code into an AST.
            tree = ast.parse(
                source_code,
                filename=str(file_path)
            )

            # Extract symbols.
            symbol_extractor = SymbolExtractor()

            result.symbols = symbol_extractor.extract(tree)

            # Extract imports.
            import_extractor = ImportExtractor()

            result.imports = import_extractor.extract(tree)

        except SyntaxError as exc:

            result.status = "syntax_error"

            result.error = (
                f"Line {exc.lineno}: {exc.msg}"
            )

        return result
