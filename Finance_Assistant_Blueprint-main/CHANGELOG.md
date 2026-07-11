# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Conventional Commits](https://www.conventionalcommits.org/).

## [Unreleased]

### Added
- Production engineering audit and implementation plan
- Comprehensive `.gitignore` for Python, Terraform, Docker, IDE
- `pyproject.toml` with dependency management and tool configs (ruff, mypy, pytest)
- `.env.example` with documented environment variables
- `Makefile` with standard development targets
- `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`
- `.pre-commit-config.yaml` for code quality hooks
- GitHub issue and PR templates
- ADR-001 (Technology Choices) and ADR-003 (QLDB Replacement)
- FastAPI application skeleton with health endpoints
- Structured logging with structlog
- Pydantic settings for configuration management
- Docker and docker-compose for local development
- CI pipeline (ruff lint + mypy + pytest)

### Changed
- Moved architecture blueprints from `docs/adr/` to `docs/architecture/`
- Replaced CUDA-only `.gitignore` with comprehensive patterns
- Converted tests from `unittest` to `pytest` style

## [0.0.1] - 2026-06-12

### Added
- Initial repository scaffolding with folder structure
- Architecture documentation (System Blueprint, App Blueprint)
- Delivery plan (README.md)
- Placeholder CI/CD workflows
- Basic transaction categorization module (`core.py`)
- Unit tests for core module
