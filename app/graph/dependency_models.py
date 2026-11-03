from dataclasses import dataclass, field

from app.graph.relationships import RelationshipType


@dataclass
class GraphNode:
    id: str
    name: str
    node_type: str
    file_path: str


@dataclass
class GraphEdge:
    source: str
    target: str
    relationship: RelationshipType
    line: int | None = None


@dataclass
class DependencyGraph:

    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    adjacency: dict[str, set[str]] = field(default_factory=dict)
    reverse_adjacency: dict[str, set[str]] = field(default_factory=dict)

    def add_node(self, node: GraphNode):

        self.nodes[node.id] = node

        self.adjacency.setdefault(node.id, set())
        self.reverse_adjacency.setdefault(node.id, set())

    def add_edge(self, edge: GraphEdge):

        if edge.source not in self.nodes:
            raise ValueError(f"Unknown source node: {edge.source}")

        if edge.target not in self.nodes:
            raise ValueError(f"Unknown target node: {edge.target}")

        if edge not in self.edges:
            self.edges.append(edge)

        self.adjacency[edge.source].add(edge.target)
        self.reverse_adjacency[edge.target].add(edge.source)

    def get_node(self, node_id: str):
        return self.nodes.get(node_id)

    def get_edges(self, node_id: str):

        return [
            edge for edge in self.edges
            if edge.source == node_id or edge.target == node_id
        ]