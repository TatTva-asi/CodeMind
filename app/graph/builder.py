from app.graph.dependency_models import (
    DependencyGraph,
    GraphNode,
    GraphEdge
)

from app.graph.relationships import RelationshipType


class DependencyGraphBuilder:

    def build(self, semantic_result, symbols=None):

        graph = DependencyGraph()

        self._add_file_nodes(graph, semantic_result)

        self._add_symbol_nodes(graph, symbols or [])

        self._add_import_edges(graph, semantic_result.imports)

        self._add_call_edges(graph, semantic_result.calls)

        self._add_inheritance_edges(
            graph,
            semantic_result.inheritance
        )

        return graph

    # ---------------- FILE NODES ----------------

    def _add_file_nodes(self, graph, semantic_result):

        file_paths = set()

        for reference in semantic_result.imports:
            file_paths.add(reference.source_file)

            if reference.resolved_file:
                file_paths.add(reference.resolved_file)

        for reference in semantic_result.calls:
            file_paths.add(reference.source_file)

        for reference in semantic_result.inheritance:
            file_paths.add(reference.source_file)

        for file_path in file_paths:

            graph.add_node(
                GraphNode(
                    id=f"file::{file_path}",
                    name=file_path,
                    node_type="file",
                    file_path=file_path
                )
            )

    # ---------------- SYMBOL NODES ----------------

    def _add_symbol_nodes(self, graph, symbols):

        for symbol in symbols:

            qualified_name = symbol.qualified_name
            file_path = symbol.file_path
            symbol_type = symbol.symbol_type

            node_id = f"symbol::{file_path}::{qualified_name}"

            graph.add_node(
                GraphNode(
                    id=node_id,
                    name=qualified_name,
                    node_type=symbol_type,
                    file_path=file_path
                )
            )

    # ---------------- IMPORT EDGES ----------------

    def _add_import_edges(self, graph, imports):

        for reference in imports:

            if reference.status != "resolved":
                continue

            if not reference.resolved_file:
                continue

            source = f"file::{reference.source_file}"
            target = f"file::{reference.resolved_file}"

            if source not in graph.nodes or target not in graph.nodes:
                continue

            graph.add_edge(
                GraphEdge(
                    source=source,
                    target=target,
                    relationship=RelationshipType.IMPORTS
                )
            )

    # ---------------- CALL EDGES ----------------

    def _add_call_edges(self, graph, calls):

        for reference in calls:

            if reference.status != "resolved":
                continue

            if len(reference.candidate_targets) != 1:
                continue

            source = (
                f"symbol::{reference.source_file}::"
                f"{reference.caller}"
            )

            target_name = reference.candidate_targets[0]

            target_file = self._find_symbol_file(
                graph,
                target_name
            )

            if target_file is None:
                continue

            target = (
                f"symbol::{target_file}::{target_name}"
            )

            if source not in graph.nodes:
                continue

            if target not in graph.nodes:
                continue

            graph.add_edge(
                GraphEdge(
                    source=source,
                    target=target,
                    relationship=RelationshipType.CALLS,
                    line=reference.line
                )
            )

    # ---------------- INHERITANCE EDGES ----------------

    def _add_inheritance_edges(self, graph, inheritance):

        for reference in inheritance:

            if reference.status != "resolved":
                continue

            if not reference.resolved_base:
                continue

            source_file = reference.source_file

            source = (
                f"symbol::{source_file}::"
                f"{reference.child_class}"
            )

            target_file = self._find_symbol_file(
                graph,
                reference.resolved_base
            )

            if target_file is None:
                continue

            target = (
                f"symbol::{target_file}::"
                f"{reference.resolved_base}"
            )

            if source not in graph.nodes or target not in graph.nodes:
                continue

            graph.add_edge(
                GraphEdge(
                    source=source,
                    target=target,
                    relationship=RelationshipType.INHERITS
                )
            )

    # ---------------- SYMBOL FILE LOOKUP ----------------

    def _find_symbol_file(self, graph, qualified_name):

        matches = [
            node.file_path
            for node in graph.nodes.values()
            if (
                node.node_type in ("function", "class", "method")
                and node.name == qualified_name
            )
        ]

        if len(matches) == 1:
            return matches[0]

        return None