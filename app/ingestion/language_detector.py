
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LanguageInfo:
    language: str
    category: str
    is_programming_language: bool


class LanguageDetector:

    EXTENSION_MAP = {
        ".py": "Python",
        ".pyi": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".mjs": "JavaScript",
        ".cjs": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".cpp": "C++",
        ".cc": "C++",
        ".c": "C",
        ".h": "C/C++",
        ".hpp": "C++",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".cs": "C#",
        ".sql": "SQL",
        ".sh": "Shell",
        ".ps1": "PowerShell",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".vue": "Vue",
        ".svelte": "Svelte",
        ".md": "Markdown",
        ".mdx": "MDX",
        ".rst": "reStructuredText",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".xml": "XML",
        ".ini": "INI",
        ".cfg": "INI",
        ".txt": "Text",
    }

    SPECIAL_FILES = {
        "dockerfile": ("Dockerfile", "configuration", False),
        "makefile": ("Makefile", "configuration", False),
        "jenkinsfile": ("Groovy", "source", True),
        "cmakelists.txt": ("CMake", "configuration", False),
        "requirements.txt": ("Requirements", "configuration", False),
        "pyproject.toml": ("TOML", "configuration", False),
        "package.json": ("JSON", "configuration", False),
    }

    def detect(self, file_path: str | Path) -> LanguageInfo:

        path = Path(file_path)
        filename = path.name.lower()

        # Check special filenames first.
        if filename in self.SPECIAL_FILES:
            language, category, is_code = (
                self.SPECIAL_FILES[filename]
            )

            return LanguageInfo(
                language,
                category,
                is_code
            )

        extension = path.suffix.lower()

        language = self.EXTENSION_MAP.get(extension)

        if language is None:
            return LanguageInfo(
                language="Unknown",
                category="unknown",
                is_programming_language=False
            )

        if language in {"Markdown", "MDX", "reStructuredText", "Text"}:
            category = "documentation"
            is_code = False

        elif language in {"JSON", "YAML", "TOML", "XML", "INI"}:
            category = "configuration"
            is_code = False

        elif language in {"HTML", "CSS", "SCSS", "Vue", "Svelte"}:
            category = "markup"
            is_code = False

        elif language == "SQL":
            category = "source"
            is_code = True

        else:
            category = "source"
            is_code = True

        return LanguageInfo(
            language=language,
            category=category,
            is_programming_language=is_code
        )


