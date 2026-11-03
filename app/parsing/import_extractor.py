
import ast

from app.parsing.parser_models import Import


class ImportExtractor(ast.NodeVisitor):

    def __init__(self):
        self.imports = []

    def visit_Import(self, node):

        for alias in node.names:

            self.imports.append(
                Import(
                    module=alias.name,
                    names=[alias.asname or alias.name],
                    line=node.lineno
                )
            )

    def visit_ImportFrom(self, node):

        self.imports.append(
            Import(
                module=node.module,
                names=[
                    alias.asname or alias.name
                    for alias in node.names
                ],
                line=node.lineno,
                is_relative=node.level > 0,
                relative_level=node.level
            )
        )

    def extract(self, tree):

        self.visit(tree)

        return self.imports
