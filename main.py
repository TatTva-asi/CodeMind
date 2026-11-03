
from app.ingestion.repository import RepositoryIngestor


if __name__ == "__main__":

    repository = RepositoryIngestor(
        repository_path=r"C:\Users\mukes\OneDrive\Desktop\codemind",

        extra_ignore_patterns=[
            "generated/",
            "*.log"
        ]
    )

    manifest = repository.ingest(
        manifest_path="output/manifest.json"
    )

    print("\nLanguage Summary:")

    for language, count in manifest.language_summary.items():
        print(f"{language}: {count}")

    print("\nFirst 5 discovered files:")

    for file in manifest.files[:5]:
        print(file.path, file.language, file.sha256)
