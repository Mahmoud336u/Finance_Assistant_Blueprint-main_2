# Contributing to Meridian

Thank you for your interest in contributing to Meridian! This document explains our development workflow and standards.

## Development Setup

### Prerequisites
- Python 3.12+
- Docker and Docker Compose
- Terraform 1.5+ (for infrastructure changes)
- AWS CLI v2 (for deployment)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/mahmoudheshmat/meridian.git
cd meridian

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install with all development dependencies
make install

# Copy environment template
cp .env.example .env

# Start local services
make docker-up

# Run tests
make test

# Start development server
make dev
```

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Usage |
|--------|-------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation change |
| `infra:` | Infrastructure (Terraform, Docker, CI) |
| `refactor:` | Code change that neither fixes a bug nor adds a feature |
| `test:` | Adding or updating tests |
| `chore:` | Maintenance tasks |

**Examples:**
```
feat: add /v1/chat endpoint with SSE streaming
fix: handle empty CSV upload gracefully
infra: add Terraform Aurora PostgreSQL module
docs: add ADR-003 for QLDB replacement decision
```

## Pull Request Process

1. Create a feature branch from `main`: `git checkout -b feat/my-feature`
2. Make your changes following the code standards below
3. Ensure all checks pass: `make check && make test`
4. Open a PR with a clear description using the PR template
5. Request review from at least one maintainer
6. Squash-merge after approval

## Code Standards

- **Linting:** `ruff` — run `make lint` to check, `make format` to auto-fix
- **Type checking:** `mypy` in strict mode — run `make type-check`
- **Testing:** `pytest` with ≥80% coverage — run `make test`
- **Docstrings:** All public functions and classes must have docstrings
- **Error handling:** Use structured error responses; never return raw exceptions

## Architecture Decisions

Major design decisions are documented as ADRs (Architecture Decision Records) in `docs/adr/`. When proposing a significant change:

1. Create a new ADR following the [Michael Nygard template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
2. Include in your PR
3. Reference the ADR in your commit message

## Questions?

Open a GitHub Discussion or reach out to the maintainers.
