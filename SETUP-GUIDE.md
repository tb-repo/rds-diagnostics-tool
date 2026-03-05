# RDS Diagnostics Tool - Setup Guide

Quick setup guide for team members to install and start using the RDS Diagnostics Tool.

---

## Prerequisites

- Python 3.8 or higher
- AWS credentials (Access Key ID and Secret Access Key)
- Access to AWS RDS instances

**Optional but Recommended:**
- AWS CLI (makes credential management easier)

---

## Step 1: Install Python (if not already installed)

### Check if Python is installed:
```bash
python --version
```

If not installed, download from: https://www.python.org/downloads/

**Important:** During installation, check "Add Python to PATH"

---

## Step 2: Get the Tool

### Option A: Clone from Git (if available)
```bash
git clone <repository-url>
cd rds-diagnostics-tool
```

### Option B: Extract from ZIP
1. Extract the ZIP file to a folder (e.g., `C:\Tools\rds-diagnostics-tool`)
2. Open Command Prompt or PowerShell
3. Navigate to the folder:
   ```bash
   cd C:\Tools\rds-diagnostics-tool
   ```

---

## Step 3: Install the Tool

### Option A: Install with pip (Recommended)
Run this command in the tool directory:

```bash
pip install -e .
```

This installs the tool and all required dependencies automatically.

### Option B: Install dependencies separately
If you prefer to see what's being installed:

```bash
# Install dependencies first
pip install -r requirements.txt

# Then install the tool
pip install -e .
```

### What gets installed:
- boto3 - AWS SDK for Python
- click - CLI framework
- pydantic - Data validation
- python-dateutil - Date/time parsing
- pyyaml - Configuration file support

---

## Step 4: Configure AWS Credentials

### Option A: Using AWS CLI (Recommended - Easiest)

#### Install AWS CLI (if not already installed):
```bash
pip install awscli
```

#### Configure a profile:
```bash
aws configure --profile YOUR-PROFILE-NAME
```

Enter your AWS credentials when prompted:
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `ap-southeast-1`
- Default output format: `json`

#### For AWS SSO users:
```bash
aws sso login --profile YOUR-PROFILE-NAME
```

### Option B: Manual Configuration (No AWS CLI needed)

#### Create credentials file:
Create `~/.aws/credentials` (Windows: `C:\Users\USERNAME\.aws\credentials`):

```ini
[YOUR-PROFILE-NAME]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

#### Create config file:
Create `~/.aws/config` (Windows: `C:\Users\USERNAME\.aws\config`):

```ini
[profile YOUR-PROFILE-NAME]
region = ap-southeast-1
output = json
```

### Option C: Environment Variables (Temporary)

```bash
# Windows
set AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
set AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
set AWS_DEFAULT_REGION=ap-southeast-1

# Linux/Mac
export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
export AWS_DEFAULT_REGION=ap-southeast-1
```

### Verify credentials:

#### With AWS CLI:
```bash
aws sts get-caller-identity --profile YOUR-PROFILE
```

#### Without AWS CLI (using the tool):
```bash
rds-diag --profile YOUR-PROFILE check-permissions
```

---

## Step 5: Verify Installation

### Test the tool:
```bash
rds-diag --help
```

You should see the help menu with available commands.

### List RDS instances:
```bash
rds-diag --profile YOUR-PROFILE list
```

---

## Step 6: Run Your First Report

### Basic command:
```bash
rds-diag --profile YOUR-PROFILE report --instance YOUR-INSTANCE-ID --output my-report.txt
```

### Example:
```bash
rds-diag --profile LT-SIT report --instance ielts-ses-sit-v1-clusterinstance1 --output report.txt
```

---

## Common Commands

### List all RDS instances:
```bash
rds-diag --profile YOUR-PROFILE list
```

### Quick diagnostics (last 1 hour):
```bash
rds-diag --profile YOUR-PROFILE diagnose --instance INSTANCE-ID
```

### Full report (last 24 hours):
```bash
rds-diag --profile YOUR-PROFILE report --instance INSTANCE-ID --time-range 24h --output report.txt
```

### Weekly report:
```bash
rds-diag --profile YOUR-PROFILE report --instance INSTANCE-ID --time-range 7d --output weekly-report.txt
```

---

## Configuration File (Optional)

Create `config.yaml` in the tool directory to set defaults:

```yaml
aws_profile: YOUR-DEFAULT-PROFILE
default_region: ap-southeast-1
output_format: text

thresholds:
  cpu_utilization: 80.0
  freeable_memory_gb: 0.5
  database_connections_percent: 80.0
```

Then you can run commands without specifying profile:
```bash
rds-diag report --instance INSTANCE-ID --output report.txt
```

---

## Troubleshooting

### "rds-diag: command not found"
- Restart your terminal/command prompt
- Or run: `pip install -e .` again

### "No credentials found"
- **Option 1 (with AWS CLI):** Run `aws configure --profile YOUR-PROFILE`
- **Option 2 (without AWS CLI):** Manually create `~/.aws/credentials` file (see Step 4)
- **Option 3:** Use environment variables (see Step 4)
- Verify: `rds-diag --profile YOUR-PROFILE check-permissions`

### "Access Denied" errors
- Contact your AWS administrator for required permissions:
  - `rds:DescribeDBInstances`
  - `cloudwatch:GetMetricStatistics`
  - `pi:GetResourceMetrics` (for Performance Insights)

### "Performance Insights not available"
- This is normal if PI is not enabled on the instance
- The tool will still collect CloudWatch metrics

---

## Quick Reference

### Command Structure:
```bash
rds-diag --profile PROFILE COMMAND --instance INSTANCE-ID [OPTIONS]
```

### Available Commands:
- `list` - List all RDS instances
- `diagnose` - Quick diagnostics check
- `report` - Generate detailed report
- `check-permissions` - Verify IAM permissions

### Common Options:
- `--time-range 1h|24h|7d` - Time range for metrics
- `--output filename.txt` - Save to file
- `--report-type technical|management` - Report detail level
- `--verbose` - Show detailed progress

---

## Getting Help

### Command help:
```bash
rds-diag --help
rds-diag report --help
rds-diag diagnose --help
```

### Documentation:
- `EXAMPLES.md` - Usage examples
- `TIME-RANGE-QUICK-REFERENCE.md` - Time range options
- `README.md` - Full documentation

---

## Next Steps

1. ✅ Install the tool
2. ✅ Configure AWS profiles
3. ✅ Run your first report
4. 📖 Review `EXAMPLES.md` for more use cases
5. 🔧 Customize `config.yaml` for your needs

---

**Need help?** Contact your team lead or check the documentation files in the tool directory.
