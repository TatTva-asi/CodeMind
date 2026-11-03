
import ast
from pathlib import Path
from collections import defaultdict

from app.parsing.semantic_models import (
    ImportReference,
    CallReference,
    InheritanceReference,
    TypeFact,
    ExecutionEvent,
    SemanticAnalysisResult,
)


class PythonSemanticAnalyzer:

    def analyze(self, sources: dict[str, str]):

        result = SemanticAnalysisResult()

        trees = {}
        module_index = {}
        class_index = defaultdict(list)
        function_index = defaultdict(list)

        # 1. Parse all repository Python files.
        for file_path, source in sources.items():

            path = Path(file_path)

            if path.suffix != ".py":
                continue

            try:
                tree = ast.parse(source, filename=file_path)
                trees[file_path] = tree

            except SyntaxError as exc:
                result.errors.append(
                    f"{file_path}: syntax error at line {exc.lineno}"
                )

        # 2. Build a repository module index.
        for file_path, tree in trees.items():

            path = Path(file_path)

            if path.name == "__init__.py":
                module = ".".join(path.parent.parts)
            else:
                module = ".".join(
                    path.with_suffix("").parts
                )

            module_index[module] = file_path

            # Build class and function indexes.
            for node in ast.walk(tree):

                if isinstance(node, ast.ClassDef):
                    class_index[node.name].append(
                        f"{module}.{node.name}"
                    )

                elif isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    function_index[node.name].append(
                        f"{module}.{node.name}"
                    )

        # 3. Analyze every parsed file.
        for file_path, tree in trees.items():

            analyzer = _FileAnalyzer(
                file_path=file_path,
                module_index=module_index,
                class_index=class_index,
                function_index=function_index,
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


class _FileAnalyzer(ast.NodeVisitor):

    def __init__(
        self,
        file_path,
        module_index,
        class_index,
        function_index
    ):

        self.file_path = file_path
        self.module_index = module_index
        self.class_index = class_index
        self.function_index = function_index

        self.imports = []
        self.calls = []
        self.inheritance = []
        self.types = []
        self.execution_events = []

        self.scope = []
        self.source_order = 0

    def current_scope(self):
        return ".".join(self.scope) or "<module>"

    # ---------- IMPORT RESOLUTION ----------

    def resolve_module(self, module):

        if module in self.module_index:
            return self.module_index[module]

        # Also support package imports.
        package_init = f"{module}.__init__"

        return self.module_index.get(package_init)

    def visit_Import(self, node):

        for alias in node.names:

            resolved = self.resolve_module(alias.name)

            self.imports.append(
                ImportReference(
                    source_file=self.file_path,
                    module=alias.name,
                    names=[alias.asname or alias.name],
                    resolved_file=resolved,
                    status=(
                        "resolved" if resolved else "unresolved"
                    )
                )
            )

    def visit_ImportFrom(self, node):

        module = node.module or ""

        for alias in node.names:

            resolved_module = module

            # Handle relative imports.
            if node.level > 0:
                current = Path(self.file_path).parent

                package_parts = list(current.parts)

                if Path(self.file_path).name == "__init__.py":
                    package_parts = list(Path(self.file_path).parent.parts)

                remove_count = node.level - 1

                if remove_count:
                    package_parts = package_parts[:-remove_count]

                resolved_module = ".".join(
                    package_parts + ([module] if module else [])
                )

            target = self.resolve_module(resolved_module)

            # For "from package import module", try the submodule.
            if target is None and module:
                target = self.resolve_module(
                    f"{resolved_module}.{alias.name}"
                )

            self.imports.append(
                ImportReference(
                    source_file=self.file_path,
                    module=resolved_module,
                    names=[alias.name],
                    resolved_file=target,
                    status="resolved" if target else "unresolved"
                )
            )

    # ---------- INHERITANCE ----------

    def visit_ClassDef(self, node):

        qualified_name = ".".join(
            self.scope + [node.name]
        )

        for base in node.bases:

            base_name = ast.unparse(base)

            candidates = self.class_index.get(
                base_name.split(".")[-1],
                []
            )

            resolved = candidates[0] if len(candidates) == 1 else None

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
        self.generic_visit(node)
        self.scope.pop()

    # ---------- FUNCTION DEFINITIONS ----------

    def visit_FunctionDef(self, node):

        self._extract_function_types(node)

        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_AsyncFunctionDef(self, node):

        self._extract_function_types(node)

        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def _extract_function_types(self, node):

        scope = ".".join(self.scope + [node.name])

        arguments = (
            node.args.posonlyargs
            + node.args.args
            + node.args.kwonlyargs
        )

        for argument in arguments:

            if argument.annotation is not None:

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

        if node.args.vararg and node.args.vararg.annotation:
            self.types.append(
                TypeFact(
                    self.file_path,
                    scope,
                    node.args.vararg.arg,
                    ast.unparse(node.args.vararg.annotation),
                    "declared",
                    "Variadic parameter annotation"
                )
            )

        if node.args.kwarg and node.args.kwarg.annotation:
            self.types.append(
                TypeFact(
                    self.file_path,
                    scope,
                    node.args.kwarg.arg,
                    ast.unparse(node.args.kwarg.annotation),
                    "declared",
                    "Keyword parameter annotation"
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

    # ---------- BASIC TYPE INFERENCE ----------

    def _infer_value_type(self, value):

        if isinstance(value, ast.Constant):
            return type(value.value).__name__

        if isinstance(value, ast.List):
            return "list"

        if isinstance(value, ast.Tuple):
            return "tuple"

        if isinstance(value, ast.Set):
            return "set"

        if isinstance(value, ast.Dict):
            return "dict"

        if isinstance(value, ast.Lambda):
            return "callable"

        if isinstance(value, ast.Call):
            if isinstance(value.func, ast.Name):
                return value.func.id

            if isinstance(value.func, ast.Attribute):
                return value.func.attr

        return None

    def visit_AnnAssign(self, node):

        if isinstance(node.target, ast.Name):

            self.types.append(
                TypeFact(
                    source_file=self.file_path,
                    scope=self.current_scope(),
                    variable=node.target.id,
                    inferred_type=ast.unparse(node.annotation),
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

    # ---------- FUNCTION CALL ANALYSIS ----------

    def visit_Call(self, node):

        expression = ast.unparse(node.func)

        candidates = []

        if isinstance(node.func, ast.Name):

            candidates = self.function_index.get(
                node.func.id, []
            )

        elif isinstance(node.func, ast.Attribute):

            if isinstance(node.func.value, ast.Name):

                if node.func.value.id in ("self", "cls"):
                    class_scope = self.scope[-1] if self.scope else ""

                    candidates = [
                        f"{self.file_path}:{class_scope}.{node.func.attr}"
                    ]

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
                expression=expression,
                line=node.lineno,
                candidate_targets=candidates,
                status=status
            )
        )

        self.generic_visit(node)

    # ---------- TOP-LEVEL EXECUTION ORDER ----------

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

            # Collect direct calls in module-level statements.
            # Do not descend into function or class definitions.
            for node in ast.walk(statement):

                if node is not statement and isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                        ast.Lambda
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
