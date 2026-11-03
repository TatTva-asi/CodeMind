
from fnmatch import fnmatchcase
from pathlib import PurePosixPath
from typing import Iterable


class IgnoreRules:
    """
    Determines which repository paths should be excluded
    from CodeMind's ingestion pipeline.
    """

    DEFAULT_IGNORED_DIRS = {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "node_modules",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".idea",
        ".next",
        ".nuxt",
        "dist",
        "build",
        "coverage",
        "htmlcov",
    }

    DEFAULT_IGNORED_FILES = {
        ".DS_Store",
        "Thumbs.db",
    }

    DEFAULT_FILE_PATTERNS = {
        "*.pyc",
        "*.pyo",
        "*.log",
        "*.tmp",
        "*.swp",
        "*.swo",
        "*~",
    }

    SAFE_ENV_FILES = {
        ".env.example",
        ".env.sample",
        ".env.template",
    }

    def __init__(
        self,
        extra_patterns: Iterable[str] | None = None
    ):
        self.ignored_dirs = set(self.DEFAULT_IGNORED_DIRS)
        self.ignored_files = set(self.DEFAULT_IGNORED_FILES)
        self.file_patterns = set(self.DEFAULT_FILE_PATTERNS)

        self.extra_patterns = self._normalize_patterns(
            extra_patterns or []
        )

    @staticmethod
    def _normalize_patterns(patterns):
        normalized = []

        for pattern in patterns:
            pattern = pattern.strip().replace("\\", "/")

            if pattern:
                normalized.append(pattern)

        return normalized

    @staticmethod
    def _normalize_path(path):
        path = str(path).replace("\\", "/")

        while path.startswith("./"):
            path = path[2:]

        if path.startswith("/") or ".." in PurePosixPath(path).parts:
            raise ValueError(
                "Expected a repository-relative path without '..'"
            )

        return path

    def _matches_custom_pattern(self, path, is_dir):
        parts = PurePosixPath(path).parts

        for raw_pattern in self.extra_patterns:

            directory_only = raw_pattern.endswith("/")
            anchored = raw_pattern.startswith("/")

            pattern = raw_pattern.strip("/")

            if not pattern:
                continue

            # Patterns without slashes match path components.
            if "/" not in pattern:

                for index, part in enumerate(parts):

                    component_is_dir = (
                        index < len(parts) - 1 or is_dir
                    )

                    if directory_only and not component_is_dir:
                        continue

                    if fnmatchcase(part, pattern):
                        return True

            else:
                # Check each path prefix so ignored directories
                # also exclude their descendants.
                prefixes = [
                    "/".join(parts[:i])
                    for i in range(1, len(parts) + 1)
                ]

                candidates = (
                    prefixes[-1:]
                    if anchored
                    else prefixes
                )

                for candidate in candidates:

                    if directory_only:
                        is_candidate_dir = (
                            candidate != path or is_dir
                        )

                        if not is_candidate_dir:
                            continue

                    if PurePosixPath(candidate).match(pattern):
                        return True

        return False

    def should_ignore(self, path, is_dir=False):
        """
        Return True if a repository-relative path
        should be excluded from ingestion.
        """

        path = self._normalize_path(path)

        if not path:
            return False

        parts = PurePosixPath(path).parts
        filename = parts[-1]

        # 1. Ignore default directories.
        if any(part in self.ignored_dirs for part in parts):
            return True

        # 2. Ignore known generated or system files.
        if filename in self.ignored_files:
            return True

        # 3. Preserve safe environment examples.
        if filename in self.SAFE_ENV_FILES:
            return False

        # 4. Ignore environment secret files.
        if filename == ".env" or (
            filename.startswith(".env.")
            and filename not in self.SAFE_ENV_FILES
        ):
            return True

        # 5. Ignore files matching default glob patterns.
        if any(
            fnmatchcase(filename, pattern)
            for pattern in self.file_patterns
        ):
            return True

        # 6. Apply user-defined patterns.
        if self._matches_custom_pattern(path, is_dir):
            return True

        return False


