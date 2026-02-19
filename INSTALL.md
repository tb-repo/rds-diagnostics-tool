# Installation Guide

## Quick Installation

### 1. Install the Package

```bash
# Navigate to the project directory
cd rds-diagnostics-tool

# Install in development mode (recommended for development)
pip install -e .

# Or install normally
pip install .
```

### 2. Verify Installation

```bash
# Check that the command is available
rds-diag version

# Expected output:
# RDS Diagnostics Tool v0.1.0
# A command-line utility for AWS RDS performance diagnostics and reporting
```

### 3. Configure AWS Credentials

The tool uses AWS CLI credentials. Ensure you have configured your AWS credentials:

```bash
# Option 1: Configure AWS CLI
aws configure --profile your-profile

# Option 2: Use AWS SSO
aws sso login --profile your-profile

# Option 3: Use environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=ap-southeast-1
```

### 4. Test the Installation

```bash
# List RDS instances (this will verify your credentials and permissions)
rds-diag list --profile your-profile

# If successful, you should see a list of RDS instances
```

## Installation with Development Dependencies

If you plan to contribute or run tests:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Verify pytest is installed
pytest --version

# Run tests
pytest
```

## Configuration (Optional)

### Create Configuration File

```bash
# Create config directory
mkdir -p ~/.rds-diagnostics

# Copy example config
cp config.example.yaml ~/.rds-diagnostics/config.yaml

# Edit the config file
nano ~/.rds-diagnostics/config.yaml
```

### Configuration File Location

The tool looks for configuration in these locations (in order):
1. Path specified with `--config` flag
2. `~/.rds-diagnostics/config.yaml`
3. Default values (if no config file found)

## Troubleshooting Installation

### Issue: `pip: command not found`

**Solution:** Install pip
```bash
# On Ubuntu/Debian
sudo apt-get install python3-pip

# On macOS
brew install python3

# On Windows
# Download and install Python from python.org
```

### Issue: `Permission denied` when installing

**Solution:** Use virtual environment or user install
```bash
# Option 1: Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .

# Option 2: Install for user only
pip install --user -e .
```

### Issue: `ModuleNotFoundError: No module named 'click'`

**Solution:** Dependencies not installed
```bash
# Reinstall with dependencies
pip install -e .

# Or install dependencies manually
pip install boto3 click pydantic python-dateutil pyyaml
```

### Issue: `rds-diag: command not found` after installation

**Solution:** Add Python scripts directory to PATH
```bash
# Find where pip installs scripts
python3 -m site --user-base

# Add to PATH (add to ~/.bashrc or ~/.zshrc for persistence)
export PATH="$PATH:$(python3 -m site --user-base)/bin"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

## Uninstallation

```bash
# Uninstall the package
pip uninstall rds-diagnostics-tool

# Remove configuration (optional)
rm -rf ~/.rds-diagnostics
```

## Next Steps

After installation, see the [README.md](README.md) for:
- Usage examples
- Command reference
- Configuration options
- IAM permissions required
- Troubleshooting guide

## System Requirements

- **Python:** 3.8 or higher
- **Operating System:** Linux, macOS, or Windows
- **AWS CLI:** Configured with valid credentials
- **Network:** Internet access to AWS APIs
- **IAM Permissions:** See README.md for required permissions

## Dependencies

The tool automatically installs these dependencies:
- `boto3` - AWS SDK for Python
- `botocore` - Low-level AWS service access
- `click` - CLI framework
- `pydantic` - Data validation
- `python-dateutil` - Date/time parsing
- `pyyaml` - YAML configuration support

Development dependencies (optional):
- `pytest` - Testing framework
- `pytest-mock` - Mocking utilities
- `hypothesis` - Property-based testing
- `moto` - AWS service mocking
- `black` - Code formatter
- `ruff` - Linter
