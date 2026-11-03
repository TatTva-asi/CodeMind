from dataclasses import dataclass, field


@dataclass
class Parameter:
    name: str
    kind: str
    annotation: str | None = None
    default: str | None = None


@dataclass
class Symbol:
    name: str
    qualified_name: str
    kind: str
    start_line: int
    end_line: int
    signature: str | None = None
    docstring: str | None = None
    decorators: list[str] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    return_annotation: str | None = None


@dataclass
class Import:
    module: str | None
    names: list[str]
    line: int
    is_relative: bool = False
    relative_level: int = 0
    aliases: dict[str, str] = field(default_factory=dict)


@dataclass
class ParsedFile:
    file_path: str
    language: str
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[Import] = field(default_factory=list)
    status: str = "success"
    error: str | None = None