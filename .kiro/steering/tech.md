---
inclusion: always
---

# Technology Stack

## Language & Runtime

- Python 3.8+ (supports 3.8, 3.9, 3.10, 3.11)
- Type hints used throughout codebase

## Core Dependencies

- boto3/botocore: AWS SDK for RDS, CloudWatch, Performance Insights
- click: CLI framework with command groups and options
- pydantic v2: Data validation and models
- pyyaml: Configuration file parsing
- python-dateutil: Time range parsing

## Development Dependencies

- pytest: Test framework with markers (unit, property, integration)
- pytest-mock: Mocking support
- hypothesis: Property-based testing
- moto: AWS service mocking
- black: Code formatting (line length: 100)
- ruff: Linting (target: py38)

## Build System

Uses setuptools with pyproject.toml configuration. Package includes entry point `rds-diag` for CLI access.

## Common Commands

```bash
# Installation
pip install -e .                    # Development mode
pip install -e ".[dev]"             # With dev dependencies

# Testing
pytest                              # Run all tests
pytest -m unit                      # Unit tests only
pytest -m integration               # Integration tests only
pytest --cov=. --cov-report=html    # With coverage report

# Code Quality
black .                             # Format code
ruff check .                        # Lint code

# CLI Usage
rds-diag list                       # List instances
rds-diag diagnose -i INSTANCE       # Run diagnostics
rds-diag report -i INSTANCE         # Generate report
rds-diag check-permissions          # Validate IAM permissions
```

## Configuration

- Default config location: `~/.rds-diagnostics/config.yaml`
- Custom config via `--config` flag
- Precedence: defaults < config file < CLI args
- YAML format with thresholds, regions, profiles, output format
