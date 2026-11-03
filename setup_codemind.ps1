    
$ErrorActionPreference = "Stop"

# Use the current directory itself
$root = Get-Location

$directories = @(
    "app",
    "app/ingestion",
    "app/parsing",
    "app/indexing",
    "app/graph",
    "app/retrieval",
    "app/intelligence",
    "app/integrations",
    "app/evaluation",
    "app/api",
    "tests",
    "tests/ingestion",
    "tests/parsing",
    "tests/indexing",
    "tests/graph",
    "tests/retrieval",
    "tests/intelligence",
    "benchmarks",
    "experiments",
    "experiment_results",
    "evaluation_dataset",
    "architecture",
    "architecture/decisions",
    "configs",
    "frontend"
)

$files = @(
    "app/ingestion/repository.py",
    "app/ingestion/file_scanner.py",
    "app/ingestion/manifest.py",
    "app/ingestion/ignore_rules.py",

    "app/parsing/python_parser.py",
    "app/parsing/symbol_extractor.py",
    "app/parsing/import_extractor.py",
    "app/parsing/parser_models.py",

    "app/indexing/code_chunker.py",
    "app/indexing/symbol_index.py",
    "app/indexing/embedding_index.py",
    "app/indexing/hierarchy.py",

    "app/graph/builder.py",
    "app/graph/relationships.py",
    "app/graph/traversal.py",
    "app/graph/dependency_models.py",

    "app/retrieval/bm25.py",
    "app/retrieval/dense.py",
    "app/retrieval/hybrid.py",
    "app/retrieval/fusion.py",
    "app/retrieval/reranker.py",

    "app/intelligence/query_router.py",
    "app/intelligence/context_builder.py",
    "app/intelligence/code_qa.py",
    "app/intelligence/answer_schema.py",
    "app/intelligence/citation_validator.py",
    "app/intelligence/execution_flow.py",
    "app/intelligence/entrypoint_detector.py",
    "app/intelligence/call_chain.py",
    "app/intelligence/workflow_reconstructor.py",
    "app/intelligence/impact_analysis.py",
    "app/intelligence/dependency_analyzer.py",
    "app/intelligence/risk_scorer.py",
    "app/intelligence/impact_report.py",

    "app/integrations/github_client.py",
    "app/integrations/git_manager.py",
    "app/integrations/change_detector.py",
    "app/integrations/incremental_indexer.py",

    "app/evaluation/dataset.py",
    "app/evaluation/retrieval_metrics.py",
    "app/evaluation/graph_metrics.py",
    "app/evaluation/answer_evaluator.py",
    "app/evaluation/experiments.py",

    "app/api/main.py",
    "app/cli.py",

    "tests/ingestion/test_file_scanner.py",
    "tests/ingestion/test_manifest.py",
    "tests/parsing/test_python_parser.py",
    "tests/parsing/test_symbol_extractor.py",
    "tests/indexing/test_code_chunker.py",
    "tests/graph/test_builder.py",
    "tests/retrieval/test_bm25.py",
    "tests/retrieval/test_hybrid.py",
    "tests/intelligence/test_code_qa.py"
)

$packages = @(
    "app",
    "app/ingestion",
    "app/parsing",
    "app/indexing",
    "app/graph",
    "app/retrieval",
    "app/intelligence",
    "app/integrations",
    "app/evaluation",
    "app/api"
)

Write-Host "Creating folders and files in: $root" -ForegroundColor Cyan

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path (Join-Path $root $dir) -Force | Out-Null
}

foreach ($pkg in $packages) {
    $path = Join-Path $root "$pkg/__init__.py"
    if (!(Test-Path $path)) {
        New-Item -ItemType File -Path $path | Out-Null
    }
}

foreach ($file in $files) {
    $path = Join-Path $root $file
    if (!(Test-Path $path)) {
        New-Item -ItemType File -Path $path | Out-Null
    }
}

$docs = @{
    "README.md" = "# CodeMind`nIntelligent Software Engineering & Codebase Intelligence Platform."
    "architecture/system-design.md" = "# System Design`n`nInitial architecture: Python modular monolith with CLI."
    "architecture/data-model.md" = "# Data Model`n`nEntities: Repository, File, Symbol, CodeChunk, Dependency, Citation and IndexVersion."
    "architecture/requirements.md" = "# Requirements`n`nFunctional and non-functional requirements will be defined in Part 0."
    "architecture/decisions/ADR-001-architecture.md" = "# ADR-001: Modular Monolith`n`nDecision: Start with a modular monolithic architecture.`n`nReason: Simpler development and testing."
    ".gitignore" = "__pycache__/`n*.py[cod]`n.venv/`n.env`n.pytest_cache/`ndist/`nbuild/"
    ".env.example" = "# Future configuration`n# LLM_PROVIDER=`n# LLM_MODEL=`n# API_KEY="
    "pyproject.toml" = "[project]`nname = `"codemind`"`nversion = `"0.1.0`"`nrequires-python = `">=3.11`"`ndependencies = []`n`n[project.optional-dependencies]`ndev = [`"pytest`"]"
}

foreach ($entry in $docs.GetEnumerator()) {
    $path = Join-Path $root $entry.Key
    if (!(Test-Path $path)) {
        Set-Content -Path $path -Value $entry.Value -Encoding UTF8
    }
}

Write-Host "`nCodeMind structure created in current directory!" -ForegroundColor Green
Write-Host "Open this folder in VS Code using: code ." -ForegroundColor Yellow
