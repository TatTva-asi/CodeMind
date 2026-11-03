# CodeMind

### Intelligent Software Engineering & Codebase Intelligence Platform

CodeMind is an AI-powered software engineering platform designed to understand, analyze and reason about entire software repositories.

Unlike conventional code search or basic RAG systems, CodeMind aims to build structured knowledge of source code, symbols, dependencies, execution flows and architectural relationships.

The goal is to help developers understand unfamiliar codebases, investigate dependencies, trace execution paths, assess change impact and perform intelligent code reviews.

> **Project status:** Active development. Foundational repository ingestion, content processing, Python AST parsing and initial semantic analysis are under development.

## Vision

Build a repository intelligence platform capable of answering questions such as:

- How is this project architected?
- Where is a particular function defined?
- Which files depend on this module?
- What happens when this function executes?
- Which components might break if I modify this file?
- How does data flow through this application?
- Does this pull request introduce potential regressions?

## Core Features — Planned

| Component | Purpose |
|---|---|
| Repository Ingestion | Scan repositories and generate metadata |
| AST Parsing | Extract classes, functions, methods and imports |
| Code-aware Chunking | Generate structurally meaningful code chunks |
| Symbol Indexing | Index code entities and their relationships |
| Hybrid Retrieval | Combine dense and lexical search |
| Reranking | Improve retrieval relevance |
| Knowledge Graph | Represent code dependencies and relationships |
| Repository QA | Answer questions with source citations |
| Execution Flow | Reconstruct possible execution paths |
| Change Impact | Identify potentially affected components |
| GitHub Integration | Support repository synchronization |
| PR Intelligence | Analyze changes and provide code reviews |
| Evaluation | Measure retrieval and analysis quality |

## Architecture

```text
CodeMind/
│
├── app/
│   ├── api/
│   ├── evaluation/
│   ├── graph/
│   ├── indexing/
│   │
│   ├── ingestion/
│   │   ├── ignore_rules.py
│   │   ├── file_scanner.py
│   │   ├── language_detector.py
│   │   ├── hasher.py
│   │   ├── manifest.py
│   │   └── repository.py
│   │
│   ├── integrations/
│   ├── intelligence/
│   │
│   ├── parsing/
│   │   ├── content_classifier.py
│   │   ├── file_reader.py
│   │   ├── parser_models.py
│   │   ├── parser_registry.py
│   │   ├── python_parser.py
│   │   ├── symbol_extractor.py
│   │   ├── import_extractor.py
│   │   ├── semantic_models.py
│   │   └── python_semantic_analyser.py
│   │
│   ├── retrieval/
│   ├── cli.py
│   └── __init__.py
│
├── architecture/
├── benchmarks/
├── configs/
├── evaluation_dataset/
├── experiment_results/
├── experiments/
├── frontend/
├── output/
├── tests/
├── main.py
└── pyproject.toml
```

## Current Implementation

### 1. Repository Ingestion

- Recursive repository scanning using `os.scandir()`.
- Configurable file and directory exclusion rules.
- Extension-based programming language detection.
- SHA-256 file hashing with chunk-based reading.
- Structured repository manifest generation.
- JSON metadata serialization.

### 2. Content Processing

- Binary and text classification.
- File-size validation.
- UTF-8 content reading.
- Structured file-reading results.

### 3. Python AST Parsing

- Python AST generation.
- Function and class extraction.
- Method and asynchronous function extraction.
- Import extraction.
- Qualified symbol names.
- Source locations, signatures and decorators.
- Syntax error handling.

### 4. Initial Semantic Analysis

- Repository module indexing.
- Preliminary import resolution.
- Function-call candidate detection.
- Inheritance candidate detection.
- Basic type inference.
- Module-level execution-event extraction.

These are foundational implementations. Full repository-wide semantic resolution and execution-flow reconstruction remain future development work.

## Technology Stack

| Area | Technology |
|---|---|
| Primary Language | Python |
| Syntax Parsing | Python AST |
| Filesystem Traversal | pathlib, os.scandir |
| Hashing | hashlib / SHA-256 |
| Data Models | Python dataclasses |
| Metadata | JSON |
| Testing | unittest |

Additional technologies for indexing, graph construction, retrieval, APIs and integrations will be selected as those components are implemented.

## Getting Started

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd CodeMind
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -e .
```

This assumes the dependencies are declared in `pyproject.toml`. If the project has not yet defined installable dependencies, configure that file before using this command.

### 4. Run tests

```powershell
python -m unittest discover -s tests -v
```

## Development Roadmap

- [x] Initial repository ingestion modules
- [x] File exclusion rules
- [x] File scanning
- [x] Language detection
- [x] SHA-256 hashing
- [x] Repository manifest
- [x] Content classification and file reading
- [x] Python AST parsing foundation
- [x] Symbol and import extraction
- [x] Initial semantic analysis
- [ ] Complete ingestion-to-parsing integration
- [ ] Robust repository-wide symbol resolution
- [ ] Multi-language parsing using Tree-sitter
- [ ] Advanced code-aware chunking
- [ ] Symbol and chunk indexing
- [ ] Dense and lexical retrieval
- [ ] Hybrid retrieval and reranking
- [ ] Code knowledge graph
- [ ] Graph-assisted retrieval
- [ ] Repository-level question answering
- [ ] Execution-flow analysis
- [ ] Change impact analysis
- [ ] GitHub integration
- [ ] PR intelligence and reviews
- [ ] Evaluation and benchmarking



## Reference Projects

The architecture and product direction are informed by existing software engineering tools:

- [Sourcegraph](https://sourcegraph.com/) — Code search and repository understanding.
- [Greptile](https://greptile.com/) — Codebase-aware pull request reviews.
- [DeepWiki](https://deepwiki.com/) — Repository architecture documentation.
- [GitNexus](https://github.com/abhigyanpatwari/GitNexus) — Code knowledge graphs.

CodeMind aims to explore an integrated approach to repository understanding, retrieval and software engineering intelligence.

---

**CodeMind — Building deeper intelligence for software repositories.**