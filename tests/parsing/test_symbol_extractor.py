import ast

from app.parsing.symbol_extractor import SymbolExtractor


def test_extract_function_parameters():
    source = """
def calculate(a, b: int = 10, /, c: str = "hello",
              *args, enabled=True, **kwargs) -> float:
    return 1.0
"""

    tree = ast.parse(source)
    symbols = SymbolExtractor().extract(tree)

    function = symbols[0]

    assert function.name == "calculate"
    assert function.kind == "function"
    assert function.return_annotation == "float"

    params = {
        parameter.name: parameter
        for parameter in function.parameters
    }

    assert params["a"].kind == "positional_only"
    assert params["b"].annotation == "int"
    assert params["b"].default == "10"
    assert params["c"].kind == "positional_or_keyword"
    assert params["args"].kind == "var_positional"
    assert params["enabled"].kind == "keyword_only"
    assert params["kwargs"].kind == "var_keyword"


def test_extract_class_and_method():
    source = """
class Calculator:
    def add(self, a, b):
        return a + b
"""

    symbols = SymbolExtractor().extract(
        ast.parse(source)
    )

    assert symbols[0].kind == "class"
    assert symbols[1].kind == "method"
    assert symbols[1].qualified_name == "Calculator.add"