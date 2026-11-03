# this content classifier determines whther file is suitable for text processing

# we classify files into text , binary , unsupported, unknown


from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContentInfo:
    category: str
    is_text: bool
    reason: str


class ContentClassifier:

    BINARY_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".gif", ".webp",
        ".ico", ".pdf", ".exe", ".dll", ".so",
        ".zip", ".gz", ".tar", ".rar",
        ".mp3", ".mp4", ".wav", ".avi",
        ".pyc", ".class", ".o", ".bin"
    }

    def classify(self, file_path, sample: bytes) -> ContentInfo:

        path = Path(file_path)

        # Check known binary extensions.
        if path.suffix.lower() in self.BINARY_EXTENSIONS:
            return ContentInfo(
                "binary", False, "Known binary extension"
            )

        # Empty files can safely be treated as text candidates.
        if not sample:
            return ContentInfo(
                "text", True, "Empty file"
            )

        # Null bytes are a strong binary indicator.
        if b"\x00" in sample:
            return ContentInfo(
                "binary", False, "Null bytes detected"
            )

        # Check for excessive control characters.
        control_bytes = sum(
            byte < 32 and byte not in (9, 10, 13)
            for byte in sample
        )

        control_ratio = control_bytes / len(sample)

        if control_ratio > 0.10:
            return ContentInfo(
                "binary", False, "Excessive control characters"
            )

        # Check whether the sample is valid UTF-8.
        try:
            sample.decode("utf-8")
            return ContentInfo(
                "text", True, "Valid UTF-8 content"
            )

        except UnicodeDecodeError:
            return ContentInfo(
                "unknown", False, "Unsupported text encoding"
            )
