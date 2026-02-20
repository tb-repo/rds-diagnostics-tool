# Simplified Usage Guide

## ✅ What We've Set Up

1. **config.yaml** - Contains your defaults (LT-DEV profile, ap-southeast-1 region)
2. **Shortcut scripts** - Simple batch files with consistent syntax

## 🚀 Consistent Command Syntax

All batch files now accept the same parameters as the main `rds-diag` command!

### List Instances
```bash
# Use defaults from config.yaml (LT-DEV, ap-southeast-1)
rds-list.bat

# Override profile
rds-list.bat --profile LT-SIT

# Override profile and region
rds-list.bat --profile LT-PRD --region us-east-1
```

### Diagnose an Instance
```bash
# Use defaults from config.yaml
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1

# With custom time range
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1 --time-range 24h

# Override profile
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1 --profile LT-SIT

# Full example with all options
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1 --time-range 24h --profile LT-PRD --region ap-southeast-1
```

### Generate Report
```bash
# Use defaults
rds-report.bat --instance ielts-idv-dev-v1-clusterinstance1 --output report.txt

# With custom time range and profile
rds-report.bat --instance ielts-idv-dev-v1-clusterinstance1 --output report.txt --time-range 24h --profile LT-SIT
```

### Check Permissions
```bash
# Use defaults
rds-check.bat

# Override profile
rds-check.bat --profile LT-PRD
```

## 📝 Key Points

1. **Defaults from config.yaml**: If you don't specify `--profile` or `--region`, it uses values from config.yaml
2. **Consistent syntax**: All commands accept the same parameters as `rds-diag`
3. **Easy to override**: Just add `--profile` or `--region` when needed
