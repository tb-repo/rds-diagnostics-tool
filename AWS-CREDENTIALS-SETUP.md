# AWS Credentials Setup Guide

## Do I Need AWS CLI?

**Short answer: No, but it's recommended.**

- The RDS Diagnostics Tool uses **boto3** (AWS SDK for Python)
- boto3 works with or without AWS CLI
- AWS CLI just makes credential setup easier

---

## Three Ways to Configure Credentials

### Method 1: AWS CLI (Recommended - Easiest)

#### Step 1: Install AWS CLI
```bash
pip install awscli
```

#### Step 2: Configure profile
```bash
aws configure --profile YOUR-PROFILE-NAME
```

You'll be prompted for:
- AWS Access Key ID: `AKIA...`
- AWS Secret Access Key: `wJalr...`
- Default region: `ap-southeast-1`
- Default output format: `json`

#### Step 3: Verify
```bash
aws sts get-caller-identity --profile YOUR-PROFILE-NAME
```

#### For AWS SSO users:
```bash
aws sso login --profile YOUR-PROFILE-NAME
```

**Pros:**
- ✅ Easy to use
- ✅ Supports SSO
- ✅ Can manage multiple profiles
- ✅ Can test credentials easily

**Cons:**
- ❌ Requires installing AWS CLI

---

### Method 2: Manual File Configuration (No AWS CLI)

#### Step 1: Create credentials file

**Windows:** `C:\Users\YOUR-USERNAME\.aws\credentials`
**Linux/Mac:** `~/.aws/credentials`

```ini
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[lt-sit]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[lt-prd]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

#### Step 2: Create config file

**Windows:** `C:\Users\YOUR-USERNAME\.aws\config`
**Linux/Mac:** `~/.aws/config`

```ini
[default]
region = ap-southeast-1
output = json

[profile lt-sit]
region = ap-southeast-1
output = json

[profile lt-prd]
region = ap-southeast-1
output = json
```

#### Step 3: Verify
```bash
rds-diag --profile lt-sit check-permissions
```

**Pros:**
- ✅ No AWS CLI needed
- ✅ Simple text files
- ✅ Works everywhere

**Cons:**
- ❌ Manual file editing
- ❌ No SSO support
- ❌ Harder to manage multiple profiles

---

### Method 3: Environment Variables (Temporary)

#### Windows (Command Prompt):
```cmd
set AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
set AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
set AWS_DEFAULT_REGION=ap-southeast-1
```

#### Windows (PowerShell):
```powershell
$env:AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
$env:AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
$env:AWS_DEFAULT_REGION="ap-southeast-1"
```

#### Linux/Mac:
```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_DEFAULT_REGION=ap-southeast-1
```

#### Verify:
```bash
rds-diag list
```

**Pros:**
- ✅ No files needed
- ✅ No AWS CLI needed
- ✅ Quick for testing

**Cons:**
- ❌ Temporary (lost when terminal closes)
- ❌ Only one profile at a time
- ❌ Must set every time

---

## How boto3 Finds Credentials

boto3 searches for credentials in this order:

1. **Environment variables** (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
2. **Credentials file** (~/.aws/credentials)
3. **Config file** (~/.aws/config)
4. **IAM role** (if running on EC2/ECS/Lambda)

The tool will use the first credentials it finds.

---

## Multiple Profiles

### With AWS CLI:
```bash
# Configure multiple profiles
aws configure --profile dev
aws configure --profile sit
aws configure --profile prd

# Use specific profile
rds-diag --profile sit list
rds-diag --profile prd report --instance my-db
```

### Without AWS CLI (Manual):
Edit `~/.aws/credentials`:
```ini
[dev]
aws_access_key_id = KEY_FOR_DEV
aws_secret_access_key = SECRET_FOR_DEV

[sit]
aws_access_key_id = KEY_FOR_SIT
aws_secret_access_key = SECRET_FOR_SIT

[prd]
aws_access_key_id = KEY_FOR_PRD
aws_secret_access_key = SECRET_FOR_PRD
```

Edit `~/.aws/config`:
```ini
[profile dev]
region = ap-southeast-1

[profile sit]
region = ap-southeast-1

[profile prd]
region = ap-southeast-1
```

---

## Getting AWS Credentials

### From AWS Console:

1. Log in to AWS Console
2. Go to **IAM** → **Users** → Your username
3. Click **Security credentials** tab
4. Click **Create access key**
5. Download or copy the credentials
6. **Important:** Save the Secret Access Key - you can't view it again!

### From Your Administrator:

Ask your AWS administrator for:
- AWS Access Key ID
- AWS Secret Access Key
- Region (usually `ap-southeast-1`)
- Profile name to use

---

## Testing Credentials

### With AWS CLI:
```bash
# Test specific profile
aws sts get-caller-identity --profile YOUR-PROFILE

# List profiles
aws configure list-profiles
```

### Without AWS CLI (using the tool):
```bash
# Check permissions
rds-diag --profile YOUR-PROFILE check-permissions

# Try listing instances
rds-diag --profile YOUR-PROFILE list
```

---

## Troubleshooting

### "Unable to locate credentials"
- Check if credentials file exists: `~/.aws/credentials`
- Check if profile name is correct
- Try using environment variables instead

### "The security token included in the request is invalid"
- Credentials are incorrect or expired
- Regenerate access keys in AWS Console
- Update credentials file

### "Access Denied"
- Credentials are valid but lack permissions
- Contact AWS administrator for required permissions:
  - `rds:DescribeDBInstances`
  - `cloudwatch:GetMetricStatistics`
  - `pi:GetResourceMetrics`

### "Profile not found"
- Check profile name spelling
- List available profiles: `aws configure list-profiles` (if AWS CLI installed)
- Check credentials file: `~/.aws/credentials`

---

## Security Best Practices

### DO:
- ✅ Use IAM users with minimal required permissions
- ✅ Rotate access keys regularly (every 90 days)
- ✅ Use different credentials for different environments
- ✅ Store credentials securely
- ✅ Use AWS SSO if available

### DON'T:
- ❌ Share credentials with others
- ❌ Commit credentials to Git
- ❌ Use root account credentials
- ❌ Give credentials more permissions than needed
- ❌ Store credentials in code

---

## Credential File Locations

### Windows:
- Credentials: `C:\Users\USERNAME\.aws\credentials`
- Config: `C:\Users\USERNAME\.aws\config`

### Linux/Mac:
- Credentials: `~/.aws/credentials`
- Config: `~/.aws/config`

### Check if files exist:

**Windows:**
```cmd
dir %USERPROFILE%\.aws
```

**Linux/Mac:**
```bash
ls -la ~/.aws/
```

---

## Summary

| Method | AWS CLI Required? | Best For |
|--------|------------------|----------|
| AWS CLI | ✅ Yes | Most users, SSO users |
| Manual Files | ❌ No | Users without AWS CLI |
| Environment Variables | ❌ No | Testing, temporary use |

**Recommendation:** Install AWS CLI (`pip install awscli`) - it makes everything easier!

---

## Quick Start

### If you have AWS CLI:
```bash
aws configure --profile YOUR-PROFILE
rds-diag --profile YOUR-PROFILE list
```

### If you don't have AWS CLI:
1. Create `~/.aws/credentials` with your access keys
2. Create `~/.aws/config` with region settings
3. Run: `rds-diag --profile YOUR-PROFILE list`

---

## Need Help?

- Check `SETUP-GUIDE.md` for complete setup instructions
- Check `INSTALLATION.md` for installation help
- Contact your AWS administrator for credentials
- Contact your team lead for assistance
