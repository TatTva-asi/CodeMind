import ast

from app.parsing.parser_models import Import


class ImportExtractor(ast.NodeVisitor):

    def __init__(self):
        self.imports = []

    def visit_Import(self, node):

        for alias in node.names:

            bound_name = (
                alias.asname
                or alias.name.split(".")[0]
            )

            self.imports.append(
                Import(
                    module=alias.name,
                    names=[bound_name],
                    line=node.lineno,
                    aliases={
                        bound_name: alias.name
                    }
                )
            )

    def visit_ImportFrom(self, node):

        names = [
            alias.name
            for alias in node.names
        ]

        aliases = {
            alias.asname or alias.name: alias.name
            for alias in node.names
            if alias.name != "*"
        }

        self.imports.append(
            Import(
                module=node.module,
                names=names,
                line=node.lineno,
                is_relative=node.level > 0,
                relative_level=node.level,
                aliases=aliases
            )
        )

    def extract(self, tree):
        self.imports = []
        self.visit(tree)

        return self.imports