# RDS Diagnostics and Reporting Tool

A command-line tool for DBM teams to quickly diagnose, analyze, and report on AWS RDS instance performance issues.

## Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

```bash
# List RDS instances
rds-tool list --profile LT-DEV --region ap-southeast-1

# Run diagnostics
rds-tool diagnose --profile LT-DEV --instance my-rds-instance

# Generate management report
rds-tool report --profile LT-DEV --instance my-rds-instance --report-type management
```

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run property tests only
pytest -m property

# Run with coverage
pytest --cov=. --cov-report=html
```

## Documentation

See `.kiro/specs/rds-diagnostics-tool/` for complete requirements, design, and implementation plan.
