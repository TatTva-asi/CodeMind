
import os
from dataclasses import dataclass, field
from pathlib import Path

from app.ingestion.ignore_rules import IgnoreRules


@dataclass
class ScanResult:
    files: list[Path] = field(default_factory=list)
    directories: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class FileScanner:

    def __init__(
        self,
        repository_path: str | Path,
        ignore_rules: IgnoreRules | None = None
    ):
        self.root = Path(repository_path).resolve()

        if not self.root.exists():
            raise FileNotFoundError(
                f"Repository does not exist: {self.root}"
            )

        if not self.root.is_dir():
            raise NotADirectoryError(
                f"Expected a directory: {self.root}"
            )

        self.ignore_rules = ignore_rules or IgnoreRules()

    def scan(self) -> ScanResult:

        result = ScanResult()

        # Stack for iterative directory traversal.
        stack = [self.root]

        while stack:

            current_dir = stack.pop()

            try:
                with os.scandir(current_dir) as entries:

                    for entry in entries:

                        path = Path(entry.path)

                        relative_path = path.relative_to(
                            self.root
                        )

                        # Skip symbolic links.
                        if entry.is_symlink():
                            continue

                        try:
                            is_dir = entry.is_dir(
                                follow_symlinks=False
                            )

                            is_file = entry.is_file(
                                follow_symlinks=False
                            )

                        except OSError as exc:
                            result.errors.append(
                                f"{relative_path}: {exc}"
                            )
                            continue

                        # Apply ignore rules before processing.
                        if self.ignore_rules.should_ignore(
                            relative_path.as_posix(),
                            is_dir=is_dir
                        ):
                            continue

                        if is_dir:
                            result.directories.append(relative_path)
                            stack.append(path)

                        elif is_file:
                            result.files.append(relative_path)

            except OSError as exc:
                result.errors.append(
                    f"{current_dir}: {exc}"
                )

        # Ensure deterministic output ordering.
        result.files.sort()
        result.directories.sort()

        return result
