import ast
from pathlib import Path
from collections import defaultdict

from app.parsing.semantic_models import (
    ImportReference,
    CallReference,
    InheritanceReference,
    TypeFact,
    ExecutionEvent,
    SemanticAnalysisResult
)


def get_module_name(file_path):

    path = Path(file_path)

    parts = list(path.with_suffix("").parts)

    if parts and parts[-1] == "__init__":
        parts.pop()

    return ".".join(parts)


class PythonSemanticAnalyzer:

    def analyze(self, sources: dict[str, str]):

        result = SemanticAnalysisResult()

        trees = {}
        module_index = {}

        # 1. Parse repository files
        for file_path, source in sources.items():

            if Path(file_path).suffix.lower() != ".py":
                continue

            try:
                tree = ast.parse(
                    source,
                    filename=file_path
                )

                trees[file_path] = tree

                module_index[
                    get_module_name(file_path)
                ] = file_path

            except SyntaxError as exc:

                result.errors.append(
                    f"{file_path}: syntax error at "
                    f"line {exc.lineno}: {exc.msg}"
                )

        # 2. Build class and function indexes
        class_index = defaultdict(list)
        function_index = defaultdict(list)

        for file_path, tree in trees.items():

            module = get_module_name(file_path)

            for node, scope in self._get_definitions(tree):

                qualified_name = ".".join(
                    [module] + scope + [node.name]
                )

                if isinstance(node, ast.ClassDef):
                    class_index[node.name].append(
                        qualified_name
                    )

                else:
                    function_index[node.name].append(
                        qualified_name
                    )

        # 3. Analyze each file
        for file_path, tree in trees.items():

            analyzer = _FileAnalyzer(
                file_path=file_path,
                module=get_module_name(file_path),
                module_index=module_index,
                class_index=class_index,
                function_index=function_index
            )

            analyzer.analyze_tree(tree)

            result.imports.extend(analyzer.imports)
            result.calls.extend(analyzer.calls)
            result.inheritance.extend(analyzer.inheritance)
            result.types.extend(analyzer.types)

            result.execution_events.extend(
                analyzer.execution_events
            )

        return result

    def _get_definitions(self, tree):
        """
        Extract definitions with their enclosing scope.
        """

        def walk(body, scope):

            for node in body:

                if isinstance(node, ast.ClassDef):

                    yield node, scope

                    yield from walk(
                        node.body,
                        scope + [node.name]
                    )

                elif isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef)
                ):

                    yield node, scope

                    yield from walk(
                        node.body,
                        scope + [node.name]
                    )

        yield from walk(tree.body, [])


class _FileAnalyzer(ast.NodeVisitor):

    def __init__(
        self,
        file_path,
        module,
        module_index,
        class_index,
        function_index
    ):

        self.file_path = file_path
        self.module = module

        self.module_index = module_index
        self.class_index = class_index
        self.function_index = function_index

        self.imports = []
        self.calls = []
        self.inheritance = []
        self.types = []
        self.execution_events = []

        self.scope = []
        self.class_stack = []
        self.import_bindings = {}

        self.source_order = 0

    def current_scope(self):

        return ".".join(self.scope) or "<module>"

    # ---------------- MODULE RESOLUTION ----------------

    def resolve_module(self, module):

        return (
            self.module_index.get(module)
            or self.module_index.get(
                module + ".__init__"
            )
        )

    def _absolute_import_module(self, node):

        if node.level == 0:
            return node.module or ""

        package_parts = self.module.split(".")[:-1]

        if Path(self.file_path).name == "__init__.py":
            package_parts = self.module.split(".")

        keep = max(
            0,
            len(package_parts) - node.level + 1
        )

        base = package_parts[:keep]

        if node.module:
            base.extend(node.module.split("."))

        return ".".join(base)

    # ---------------- IMPORT ANALYSIS ----------------

    def visit_Import(self, node):

        for alias in node.names:

            target = self.resolve_module(alias.name)

            local_name = (
                alias.asname
                or alias.name.split(".")[0]
            )

            self.import_bindings[local_name] = (
                "module",
                alias.name
            )

            self.imports.append(
                ImportReference(
                    source_file=self.file_path,
                    module=alias.name,
                    names=[local_name],
                    resolved_file=target,
                    status=(
                        "resolved" if target
                        else "unresolved"
                    ),
                    aliases={
                        local_name: alias.name
                    }
                )
            )

    def visit_ImportFrom(self, node):

        module = self._absolute_import_module(node)

        for alias in node.names:

            if alias.name == "*":

                target = self.resolve_module(module)

                self.imports.append(
                    ImportReference(
                        source_file=self.file_path,
                        module=module,
                        names=["*"],
                        resolved_file=target,
                        status=(
                            "resolved" if target
                            else "unresolved"
                        )
                    )
                )

                continue

            local_name = alias.asname or alias.name

            submodule = (
                f"{module}.{alias.name}"
                if module else alias.name
            )

            target = self.resolve_module(module)
            imported_file = self.resolve_module(submodule)

            if imported_file:

                self.import_bindings[local_name] = (
                    "module",
                    submodule
                )

                resolved_file = imported_file

            else:

                self.import_bindings[local_name] = (
                    "symbol",
                    f"{module}.{alias.name}"
                )

                resolved_file = target

            self.imports.append(
                ImportReference(
                    source_file=self.file_path,
                    module=module,
                    names=[alias.name],
                    resolved_file=resolved_file,
                    status=(
                        "resolved" if resolved_file
                        else "unresolved"
                    ),
                    aliases={
                        local_name: alias.name
                    }
                )
            )

    # ---------------- INHERITANCE ANALYSIS ----------------

    def _resolve_class(self, base):

        if isinstance(base, ast.Name):

            binding = self.import_bindings.get(base.id)

            if binding and binding[0] == "symbol":

                all_classes = {
                    item
                    for values in self.class_index.values()
                    for item in values
                }

                return (
                    [binding[1]]
                    if binding[1] in all_classes
                    else []
                )

            base_name = (
                binding[1]
                if binding and binding[0] == "module"
                else base.id
            )

        elif isinstance(base, ast.Attribute):

            expression = ast.unparse(base)

            root = expression.split(".")[0]

            binding = self.import_bindings.get(root)

            if binding and binding[0] == "module":

                base_name = (
                    binding[1]
                    + expression[len(root):]
                )

            else:
                base_name = expression

        else:
            return []

        all_classes = [
            item
            for values in self.class_index.values()
            for item in values
        ]

        exact = [
            item
            for item in all_classes
            if (
                item == base_name
                or item.endswith("." + base_name)
            )
        ]

        if not exact and "." not in base_name:
            exact = self.class_index.get(base_name, [])

        return sorted(set(exact))

    def visit_ClassDef(self, node):

        qualified_name = ".".join(
            self.scope + [node.name]
        )

        for base in node.bases:

            base_name = ast.unparse(base)

            candidates = self._resolve_class(base)

            resolved = (
                candidates[0]
                if len(candidates) == 1
                else None
            )

            self.inheritance.append(
                InheritanceReference(
                    source_file=self.file_path,
                    child_class=qualified_name,
                    base_class=base_name,
                    resolved_base=resolved,
                    status=(
                        "resolved" if resolved
                        else "candidate" if candidates
                        else "unresolved"
                    )
                )
            )

        self.scope.append(node.name)
        self.class_stack.append(node.name)

        self.generic_visit(node)

        self.class_stack.pop()
        self.scope.pop()

    # ---------------- FUNCTION TYPE ANALYSIS ----------------

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node)

    def _visit_function(self, node):

        self._extract_function_types(node)

        self.scope.append(node.name)

        self.generic_visit(node)

        self.scope.pop()

    def _extract_function_types(self, node):

        scope = ".".join(
            self.scope + [node.name]
        )

        args = node.args

        parameters = (
            args.posonlyargs
            + args.args
            + args.kwonlyargs
        )

        if args.vararg:
            parameters.append(args.vararg)

        if args.kwarg:
            parameters.append(args.kwarg)

        for argument in parameters:

            if argument.annotation:

                self.types.append(
                    TypeFact(
                        source_file=self.file_path,
                        scope=scope,
                        variable=argument.arg,
                        inferred_type=ast.unparse(
                            argument.annotation
                        ),
                        confidence="declared",
                        evidence="Function parameter annotation"
                    )
                )

        if node.returns:

            self.types.append(
                TypeFact(
                    source_file=self.file_path,
                    scope=scope,
                    variable="<return>",
                    inferred_type=ast.unparse(node.returns),
                    confidence="declared",
                    evidence="Return annotation"
                )
            )

    # ---------------- BASIC TYPE INFERENCE ----------------

    def _infer_value_type(self, value):

        if isinstance(value, ast.Constant):
            return type(value.value).__name__

        if isinstance(value, (ast.List, ast.ListComp)):
            return "list"

        if isinstance(value, (ast.Tuple, ast.GeneratorExp)):
            return "tuple" if isinstance(value, ast.Tuple) else "generator"

        if isinstance(value, (ast.Set, ast.SetComp)):
            return "set"

        if isinstance(value, ast.Dict):
            return "dict"

        if isinstance(value, ast.DictComp):
            return "dict"

        if isinstance(value, ast.Lambda):
            return "callable"

        if isinstance(value, ast.Call):
            return ast.unparse(value.func)

        return None

    def visit_AnnAssign(self, node):

        if isinstance(node.target, ast.Name):

            self.types.append(
                TypeFact(
                    source_file=self.file_path,
                    scope=self.current_scope(),
                    variable=node.target.id,
                    inferred_type=ast.unparse(
                        node.annotation
                    ),
                    confidence="declared",
                    evidence="Variable annotation"
                )
            )

        self.generic_visit(node)

    def visit_Assign(self, node):

        inferred = self._infer_value_type(node.value)

        if inferred:

            for target in node.targets:

                if isinstance(target, ast.Name):

                    self.types.append(
                        TypeFact(
                            source_file=self.file_path,
                            scope=self.current_scope(),
                            variable=target.id,
                            inferred_type=inferred,
                            confidence="heuristic",
                            evidence="Assignment expression"
                        )
                    )

        self.generic_visit(node)

    # ---------------- FUNCTION CALL ANALYSIS ----------------

    def _resolve_call(self, node):

        if isinstance(node, ast.Name):

            name = node.id

            binding = self.import_bindings.get(name)

            if binding and binding[0] == "symbol":

                all_functions = {
                    item
                    for values in self.function_index.values()
                    for item in values
                }

                return (
                    [binding[1]]
                    if binding[1] in all_functions
                    else []
                )

            if binding and binding[0] == "module":
                return []

            local_prefix = self.module + "."

            local = [
                target
                for target in self.function_index.get(name, [])
                if target.startswith(local_prefix)
            ]

            return (
                local
                if local
                else self.function_index.get(name, [])
            )

        if isinstance(node, ast.Attribute):

            expression = ast.unparse(node)

            if (
                isinstance(node.value, ast.Name)
                and node.value.id in ("self", "cls")
            ):

                class_name = (
                    self.class_stack[-1]
                    if self.class_stack
                    else None
                )

                if class_name:

                    prefix = (
                        self.module
                        + "."
                        + ".".join(
                            self.scope[:-1] + [class_name]
                        )
                    )

                    return [
                        f"{prefix}.{node.attr}"
                    ]

            root = expression.split(".")[0]

            binding = self.import_bindings.get(root)

            if binding and binding[0] == "module":

                qualified = (
                    binding[1]
                    + expression[len(root):]
                )

                return [
                    target
                    for values in self.function_index.values()
                    for target in values
                    if target == qualified
                ]

        return []

    def visit_Call(self, node):

        candidates = sorted(
            set(self._resolve_call(node))
        )

        if len(candidates) == 1:
            status = "resolved"

        elif len(candidates) > 1:
            status = "candidate"

        else:
            status = "unresolved"

        self.calls.append(
            CallReference(
                source_file=self.file_path,
                caller=self.current_scope(),
                expression=ast.unparse(node.func),
                line=node.lineno,
                candidate_targets=candidates,
                status=status
            )
        )

        self.generic_visit(node)

    # ---------------- EXECUTION EVENTS ----------------

    def analyze_tree(self, tree):

        for statement in tree.body:

            self.source_order += 1

            self.execution_events.append(
                ExecutionEvent(
                    source_file=self.file_path,
                    line=statement.lineno,
                    scope="<module>",
                    event_type=type(statement).__name__,
                    description=ast.unparse(statement)[:200],
                    source_order=self.source_order
                )
            )

            for node in ast.walk(statement):

                if (
                    node is not statement
                    and isinstance(
                        node,
                        (
                            ast.FunctionDef,
                            ast.AsyncFunctionDef,
                            ast.ClassDef,
                            ast.Lambda
                        )
                    )
                ):
                    continue

                if isinstance(node, ast.Call):

                    self.execution_events.append(
                        ExecutionEvent(
                            source_file=self.file_path,
                            line=node.lineno,
                            scope="<module>",
                            event_type="call",
                            description=ast.unparse(node.func),
                            source_order=self.source_order
                        )
                    )

        self.visit(tree)