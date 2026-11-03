
import ast

from app.parsing.parser_models import Symbol


class SymbolExtractor(ast.NodeVisitor):

    def __init__(self):
        self.symbols = []
        self.scope = []

    def _qualified_name(self, name):
        return ".".join(self.scope + [name])

    def _get_decorators(self, node):
        return [
            ast.unparse(decorator)
            for decorator in node.decorator_list
        ]

    def visit_ClassDef(self, node):

        self.symbols.append(
            Symbol(
                name=node.name,
                qualified_name=self._qualified_name(node.name),
                kind="class",
                start_line=node.lineno,
                end_line=node.end_lineno,
                signature=f"class {node.name}",
                docstring=ast.get_docstring(node),
                decorators=self._get_decorators(node)
            )
        )

        self.scope.append(node.name)

        self.generic_visit(node)

        self.scope.pop()

    def _visit_function(self, node, kind):

        arguments = ast.unparse(node.args)

        prefix = (
            "async def"
            if kind.startswith("async")
            else "def"
        )

        return_annotation = (
            f" -> {ast.unparse(node.returns)}"
            if node.returns else ""
        )

        signature = (
            f"{prefix} {node.name}"
            f"({arguments}){return_annotation}"
        )

        self.symbols.append(
            Symbol(
                name=node.name,
                qualified_name=self._qualified_name(node.name),
                kind=kind,
                start_line=node.lineno,
                end_line=node.end_lineno,
                signature=signature,
                docstring=ast.get_docstring(node),
                decorators=self._get_decorators(node)
            )
        )

        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node):

        kind = "method" if self.scope and self._inside_class() else "function"

        self._visit_function(node, kind)

    def visit_AsyncFunctionDef(self, node):

        kind = (
            "async_method"
            if self.scope and self._inside_class()
            else "async_function"
        )

        self._visit_function(node, kind)

    def _inside_class(self):

        if not self.symbols:
            return False

        current_scope = ".".join(self.scope)

        return any(
            symbol.qualified_name == current_scope
            and symbol.kind == "class"
            for symbol in self.symbols
        )

    def extract(self, tree):

        self.visit(tree)

        return self.symbols
