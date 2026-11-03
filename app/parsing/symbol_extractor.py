import ast

from app.parsing.parser_models import Parameter, Symbol


class SymbolExtractor(ast.NodeVisitor):

    def __init__(self):
        self.symbols = []
        self.scope = []
        self.class_depth = 0

    def _decorators(self, node):
        return [
            ast.unparse(item)
            for item in node.decorator_list
        ]

    def _parameters(self, args):
        parameters = []

        # Positional-only and positional-or-keyword arguments
        positional = args.posonlyargs + args.args

        defaults = (
            [None] * (len(positional) - len(args.defaults))
            + list(args.defaults)
        )

        for index, (arg, default) in enumerate(
            zip(positional, defaults)
        ):
            kind = (
                "positional_only"
                if index < len(args.posonlyargs)
                else "positional_or_keyword"
            )

            parameters.append(
                self._create_parameter(arg, kind, default)
            )

        # *args
        if args.vararg:
            parameters.append(
                self._create_parameter(
                    args.vararg,
                    "var_positional"
                )
            )

        # Keyword-only arguments
        for arg, default in zip(
            args.kwonlyargs,
            args.kw_defaults
        ):
            parameters.append(
                self._create_parameter(
                    arg,
                    "keyword_only",
                    default
                )
            )

        # **kwargs
        if args.kwarg:
            parameters.append(
                self._create_parameter(
                    args.kwarg,
                    "var_keyword"
                )
            )

        return parameters

    @staticmethod
    def _create_parameter(arg, kind, default=None):
        return Parameter(
            name=arg.arg,
            kind=kind,
            annotation=(
                ast.unparse(arg.annotation)
                if arg.annotation else None
            ),
            default=(
                ast.unparse(default)
                if default is not None else None
            )
        )

    def visit_ClassDef(self, node):

        qualified_name = ".".join(
            self.scope + [node.name]
        )

        self.symbols.append(
            Symbol(
                name=node.name,
                qualified_name=qualified_name,
                kind="class",
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                signature=f"class {node.name}",
                docstring=ast.get_docstring(node),
                decorators=self._decorators(node)
            )
        )

        self.scope.append(node.name)
        self.class_depth += 1

        self.generic_visit(node)

        self.class_depth -= 1
        self.scope.pop()

    def _visit_function(self, node, is_async=False):

        kind = (
            "async_method" if is_async and self.class_depth
            else "async_function" if is_async
            else "method" if self.class_depth
            else "function"
        )

        parameters = self._parameters(node.args)

        prefix = "async def" if is_async else "def"

        signature = (
            f"{prefix} {node.name}"
            f"({ast.unparse(node.args)})"
        )

        return_annotation = (
            ast.unparse(node.returns)
            if node.returns else None
        )

        if return_annotation:
            signature += f" -> {return_annotation}"

        self.symbols.append(
            Symbol(
                name=node.name,
                qualified_name=".".join(
                    self.scope + [node.name]
                ),
                kind=kind,
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                signature=signature,
                docstring=ast.get_docstring(node),
                decorators=self._decorators(node),
                parameters=parameters,
                return_annotation=return_annotation
            )
        )

        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node, is_async=True)

    def extract(self, tree):
        self.symbols = []
        self.scope = []
        self.class_depth = 0

        self.visit(tree)

        return self.symbols