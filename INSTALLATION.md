
# Installation Guide

## Prerequisites

- **Python**: 3.8 or higher
- **pip**: Python package installer (included with Python)
- **AWS Credentials**: Access Key ID and Secret Access Key

**Optional but Recommended:**
- **AWS CLI**: Makes credential management easier (can be installed with `pip install awscli`)

---

## Quick Install

```bash
# Navigate to the tool directory
cd rds-diagnostics-tool

# Install the tool and all dependencies
pip install -e .
```

That's it! The tool is now installed and ready to use.

---

## What Gets Installed

### Core Dependencies (automatically installed)

| Package | Version | Purpose |
|---------|---------|---------|
| boto3 | ≥1.26.0 | AWS SDK for Python |
| botocore | ≥1.29.0 | AWS service access |
| click | ≥8.1.0 | CLI framework |
| pydantic | ≥2.0.0 | Data validation |
| python-dateutil | ≥2.8.0 | Date/time parsing |
| pyyaml | ≥6.0 | Configuration files |

### Development Dependencies (optional)

Only needed if you're developing/testing the tool:

```bash
pip install -r requirements-dev.txt
```

Includes: pytest, black, ruff, moto (for testing)

---

## Installation Methods

### Method 1: Editable Install (Recommended for Development)

```bash
pip install -e .
```

**Pros:**
- Changes to code take effect immediately
- No need to reinstall after code changes
- Good for development and testing

### Method 2: Regular Install

```bash
pip install .
```

**Pros:**
- Cleaner installation
- Good for production use

### Method 3: Install from requirements.txt

```bash
# Install dependencies only
pip install -r requirements.txt

# Then install the tool
pip install -e .
```

**Pros:**
- See exactly what's being installed
- Can review dependencies first

---

## Verify Installation

### Check if installed:
```bash
rds-diag --version
```

### Check if dependencies are installed:
```bash
pip list | grep -E "boto3|click|pydantic|pyyaml|dateutil"
```

### Test the tool:
```bash
rds-diag --help
```

---

## Upgrade

To upgrade to a newer version:

```bash
# Pull latest code (if using git)
git pull

# Reinstall
pip install -e . --upgrade
```

---

## Uninstall

```bash
pip uninstall rds-diagnostics-tool
```

---

## Troubleshooting

### "pip: command not found"
- Install pip: `python -m ensurepip --upgrade`
- Or use: `python -m pip install -e .`

### "Permission denied"
- Use: `pip install -e . --user`
- Or run as administrator (Windows) / sudo (Linux/Mac)

### "Python version not supported"
- Check version: `python --version`
- Requires Python 3.8 or higher
- Upgrade Python if needed

### Dependencies fail to install
- Upgrade pip: `pip install --upgrade pip`
- Try again: `pip install -e .`

### "ModuleNotFoundError" after installation
- Restart your terminal/command prompt
- Check installation: `pip show rds-diagnostics-tool`
- Reinstall: `pip install -e . --force-reinstall`

---

## Virtual Environment (Recommended)

For isolated installation:

### Create virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Install in virtual environment:
```bash
pip install -e .
```

### Deactivate when done:
```bash
deactivate
```

---

## System Requirements

### Minimum:
- Python 3.8+
- 100 MB disk space
- Internet connection (for AWS API calls)

### Recommended:
- Python 3.10+
- 500 MB disk space (for logs and reports)
- Stable internet connection

---

## Next Steps

After installation:

1. ✅ Configure AWS profiles: `aws configure --profile YOUR-PROFILE`
2. ✅ Test the tool: `rds-diag --help`
3. ✅ List instances: `rds-diag --profile YOUR-PROFILE list`
4. ✅ Run first report: See `SETUP-GUIDE.md`

---

## Files Reference

- `requirements.txt` - Core dependencies
- `requirements-dev.txt` - Development dependencies
- `pyproject.toml` - Package configuration
- `SETUP-GUIDE.md` - Complete setup guide
- `README.md` - Full documentation
