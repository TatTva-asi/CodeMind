from collections import deque

from app.graph.relationships import RelationshipType


class GraphTraversal:

    # ---------------- DIRECT DEPENDENCIES ----------------

    def get_direct_dependencies(
        self,
        graph,
        node_id,
        relationship=None
    ):

        if relationship is None:
            return set(graph.adjacency.get(node_id, set()))

        return {
            edge.target
            for edge in graph.edges
            if (
                edge.source == node_id
                and edge.relationship == relationship
            )
        }

    # ---------------- INDIRECT DEPENDENCIES ----------------

    def get_all_dependencies(
        self,
        graph,
        node_id,
        relationship=None
    ):

        visited = set()
        queue = deque(
            self.get_direct_dependencies(
                graph,
                node_id,
                relationship
            )
        )

        while queue:

            current = queue.popleft()

            if current in visited:
                continue

            visited.add(current)

            queue.extend(
                self.get_direct_dependencies(
                    graph,
                    current,
                    relationship
                ) - visited
            )

        return visited

    # ---------------- DIRECT DEPENDENTS ----------------

    def get_direct_dependents(
        self,
        graph,
        node_id,
        relationship=None
    ):

        if relationship is None:
            return set(
                graph.reverse_adjacency.get(node_id, set())
            )

        return {
            edge.source
            for edge in graph.edges
            if (
                edge.target == node_id
                and edge.relationship == relationship
            )
        }

    # ---------------- INDIRECT DEPENDENTS ----------------

    def get_all_dependents(
        self,
        graph,
        node_id,
        relationship=None
    ):

        visited = set()
        queue = deque(
            self.get_direct_dependents(
                graph,
                node_id,
                relationship
            )
        )

        while queue:

            current = queue.popleft()

            if current in visited:
                continue

            visited.add(current)

            queue.extend(
                self.get_direct_dependents(
                    graph,
                    current,
                    relationship
                ) - visited
            )

        return visited