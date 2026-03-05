# Dependencies Summary

## Quick Reference

### Installation Files

| File | Purpose | Usage |
|------|---------|-------|
| `requirements.txt` | Core dependencies | `pip install -r requirements.txt` |
| `requirements-dev.txt` | Development dependencies | `pip install -r requirements-dev.txt` |
| `pyproject.toml` | Package configuration | Used by `pip install -e .` |

---

## Core Dependencies (Required)

These are automatically installed when you run `pip install -e .`

### 1. boto3 (≥1.26.0)
- **Purpose**: AWS SDK for Python
- **Used for**: Connecting to AWS RDS, CloudWatch, Performance Insights
- **License**: Apache 2.0

### 2. botocore (≥1.29.0)
- **Purpose**: Low-level AWS service access
- **Used for**: AWS API calls and authentication
- **License**: Apache 2.0

### 3. click (≥8.1.0)
- **Purpose**: CLI framework
- **Used for**: Command-line interface, options, arguments
- **License**: BSD

### 4. pydantic (≥2.0.0)
- **Purpose**: Data validation and settings management
- **Used for**: Configuration validation, data models
- **License**: MIT

### 5. python-dateutil (≥2.8.0)
- **Purpose**: Date/time parsing
- **Used for**: Parsing time ranges and timestamps
- **License**: Apache 2.0 / BSD

### 6. pyyaml (≥6.0)
- **Purpose**: YAML parser
- **Used for**: Reading configuration files
- **License**: MIT

---

## Development Dependencies (Optional)

Only needed if you're developing or testing the tool.

### Testing
- **pytest** (≥7.4.0) - Test framework
- **pytest-mock** (≥3.11.0) - Mocking support
- **hypothesis** (≥6.82.0) - Property-based testing
- **moto** (≥4.1.0) - AWS service mocking
- **pytest-cov** (≥4.1.0) - Code coverage

### Code Quality
- **black** (≥23.0.0) - Code formatter
- **ruff** (≥0.0.280) - Fast Python linter

---

## Python Version Requirements

- **Minimum**: Python 3.8
- **Recommended**: Python 3.10 or higher
- **Tested on**: Python 3.8, 3.9, 3.10, 3.11, 3.13

---

## Installation Commands

### Install everything (recommended):
```bash
pip install -e .
```

### Install core dependencies only:
```bash
pip install -r requirements.txt
```

### Install with development tools:
```bash
pip install -r requirements-dev.txt
```

### Check installed versions:
```bash
pip list | grep -E "boto3|click|pydantic|pyyaml|dateutil"
```

---

## Dependency Tree

```
rds-diagnostics-tool
├── boto3 (AWS SDK)
│   └── botocore (AWS core)
├── click (CLI framework)
├── pydantic (Data validation)
├── python-dateutil (Date parsing)
└── pyyaml (YAML parser)
```

---

## Why These Dependencies?

### boto3 & botocore
- Industry-standard AWS SDK
- Required for all AWS API interactions
- Handles authentication, retries, error handling

### click
- Popular CLI framework (used by Flask, AWS CLI)
- Clean command structure
- Built-in help generation

### pydantic
- Type-safe data validation
- Clear error messages
- Modern Python best practices

### python-dateutil
- Flexible date/time parsing
- Handles multiple timestamp formats
- Timezone support

### pyyaml
- Standard YAML parser
- Configuration file support
- Human-readable config format

---

## Security & Updates

### Keeping dependencies updated:
```bash
pip install --upgrade boto3 click pydantic python-dateutil pyyaml
```

### Check for security vulnerabilities:
```bash
pip install safety
safety check
```

### Check for outdated packages:
```bash
pip list --outdated
```

---

## Offline Installation

If you need to install without internet:

### 1. Download dependencies:
```bash
pip download -r requirements.txt -d ./packages
```

### 2. Install from downloaded packages:
```bash
pip install --no-index --find-links=./packages -r requirements.txt
```

---

## Troubleshooting

### Dependency conflicts
```bash
pip install -e . --force-reinstall
```

### Specific version issues
```bash
pip install boto3==1.26.0 click==8.1.0
```

### Clear pip cache
```bash
pip cache purge
```

---

## License Compliance

All dependencies use permissive licenses:
- Apache 2.0: boto3, botocore, python-dateutil
- MIT: pydantic, pyyaml
- BSD: click, python-dateutil

No GPL or restrictive licenses - safe for commercial use.

---

## Size Information

### Installed size (approximate):
- Core dependencies: ~50 MB
- Development dependencies: ~100 MB
- Total with tool: ~150 MB

### Download size:
- Core dependencies: ~15 MB
- Development dependencies: ~30 MB

---

## Support

For dependency-related issues:
- Check `INSTALLATION.md` for troubleshooting
- Review `SETUP-GUIDE.md` for setup help
- Contact team lead for assistance
