# Quick Start Guide

Get up and running in 5 minutes!

---

## Step 1: Install Python (if needed)

Check if installed:
```bash
python --version
```

Need Python 3.8 or higher? Download from: https://www.python.org/downloads/

---

## Step 2: Install the Tool

```bash
cd rds-diagnostics-tool
pip install -e .
```

---

## Step 3: Setup AWS Credentials

### Option A: With AWS CLI (Recommended)
```bash
pip install awscli
aws configure --profile YOUR-PROFILE
```

### Option B: Without AWS CLI
Create `~/.aws/credentials`:
```ini
[YOUR-PROFILE]
aws_access_key_id = YOUR_KEY
aws_secret_access_key = YOUR_SECRET
```

Create `~/.aws/config`:
```ini
[profile YOUR-PROFILE]
region = ap-southeast-1
```

---

## Step 4: Test It

```bash
rds-diag --profile YOUR-PROFILE list
```

---

## Step 5: Run Your First Report

```bash
rds-diag --profile YOUR-PROFILE report --instance YOUR-INSTANCE-ID --output report.txt
```

---

## Done! 🎉

### What's Next?

- **Full details:** See `SETUP-GUIDE.md`
- **Examples:** See `EXAMPLES.md`
- **Credentials help:** See `AWS-CREDENTIALS-SETUP.md`
- **Installation issues:** See `INSTALLATION.md`

### Common Commands

```bash
# List instances
rds-diag --profile YOUR-PROFILE list

# Quick check (1 hour)
rds-diag --profile YOUR-PROFILE diagnose --instance INSTANCE-ID

# Daily report (24 hours)
rds-diag --profile YOUR-PROFILE report --instance INSTANCE-ID --time-range 24h --output daily.txt

# Weekly report
rds-diag --profile YOUR-PROFILE report --instance INSTANCE-ID --time-range 7d --output weekly.txt
```

---

## Need Help?

Run: `rds-diag --help`

Or check the documentation files in this directory.
