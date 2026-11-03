from dataclasses import dataclass, field


@dataclass
class ImportReference:
    source_file: str
    module: str
    names: list[str] = field(default_factory=list)
    resolved_file: str | None = None
    status: str = "unresolved"
    aliases: dict[str, str] = field(default_factory=dict)


@dataclass
class CallReference:
    source_file: str
    caller: str
    expression: str
    line: int
    candidate_targets: list[str] = field(default_factory=list)
    status: str = "unresolved"


@dataclass
class InheritanceReference:
    source_file: str
    child_class: str
    base_class: str
    resolved_base: str | None = None
    status: str = "unresolved"


@dataclass
class TypeFact:
    source_file: str
    scope: str
    variable: str
    inferred_type: str
    confidence: str
    evidence: str


@dataclass
class ExecutionEvent:
    source_file: str
    line: int
    scope: str
    event_type: str
    description: str
    source_order: int


@dataclass
class SemanticAnalysisResult:
    imports: list[ImportReference] = field(default_factory=list)
    calls: list[CallReference] = field(default_factory=list)
    inheritance: list[InheritanceReference] = field(default_factory=list)
    types: list[TypeFact] = field(default_factory=list)
    execution_events: list[ExecutionEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)