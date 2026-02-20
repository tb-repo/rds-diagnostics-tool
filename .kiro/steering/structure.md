---
inclusion: always
---

# Project Structure

## Module Organization

```
cli/                    # Command-line interface layer
  main.py              # Click commands, argument parsing, error handling

core/                   # Core application logic
  app.py               # Main orchestrator (RDSDiagnosticsApp)
  config.py            # Configuration management and validation
  models.py            # Pydantic data models (instances, metrics, reports)

aws/                    # AWS service integration
  clients.py           # Client factory and wrappers (RDS, CloudWatch, PI)
  permissions.py       # IAM permission validation

collectors/             # Data collection modules
  instance_info.py     # RDS instance metadata collector
  metrics.py           # CloudWatch metrics collector
  performance_insights.py  # Performance Insights collector

analysis/               # Analysis and diagnostics
  analyzer.py          # Threshold analysis, severity assessment, recommendations

reporting/              # Report generation
  formatters.py        # Text and JSON formatters
  generator.py         # Report orchestration

tests/                  # Test suite
  unit/                # Unit tests (fast, isolated)
  property/            # Property-based tests (hypothesis)
  integration/         # Integration tests (AWS mocking with moto)
  fixtures/            # Shared test fixtures
```

## Architecture Patterns

### Layered Architecture
- CLI layer handles user interaction and argument validation
- Core layer orchestrates business logic
- Collectors gather data from AWS services
- Analysis layer processes and evaluates metrics
- Reporting layer formats output

### Dependency Flow
CLI → Core (App) → Collectors/Analysis/Reporting → AWS Clients

### Error Handling
- Custom `AWSClientError` for AWS-specific failures
- Centralized error handling in CLI with actionable suggestions
- Graceful degradation (e.g., continues without Performance Insights)

### Configuration Management
- Immutable Configuration dataclass
- Merge pattern for CLI args (creates new instance)
- Validation in MetricThresholds with error collection

## Code Conventions

- Line length: 100 characters
- Type hints on function signatures
- Docstrings with Args/Returns/Raises sections
- Logging at INFO level for operations, DEBUG for verbose
- Exit codes: 0 (success), 1 (error), 2 (user cancelled)

## Testing Strategy

- Unit tests for business logic (config, models, analysis)
- Integration tests for end-to-end workflows
- Property-based tests for validation logic
- AWS service mocking via moto
- Pytest markers for test categorization
