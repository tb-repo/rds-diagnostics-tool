# RDS Diagnostics Tool - Quick Start Guide

## Simple Commands (Using config.yaml)

The `config.yaml` file contains your default settings (profile: LT-DEV, region: ap-southeast-1), so you don't need to type them every time!

### 1. List All RDS Instances
```bash
rds-list.bat
```
Or:
```bash
rds-diag --config config.yaml list
```

### 2. Run Diagnostics on an Instance
```bash
rds-diagnose.bat ielts-idv-dev-v1-clusterinstance1
```
Or with custom time range:
```bash
rds-diagnose.bat ielts-idv-dev-v1-clusterinstance1 24h
```

### 3. Generate a Report
```bash
rds-report.bat ielts-idv-dev-v1-clusterinstance1
```
Or with custom output file and time range:
```bash
rds-report.bat ielts-idv-dev-v1-clusterinstance1 my-report.txt 24h
```

### 4. Check Permissions
```bash
rds-check.bat
```

---

## Using Different Profiles

To use a different AWS profile (e.g., LT-PRD), you have two options:

### Option 1: Override on Command Line
```bash
rds-diag --config config.yaml --profile LT-PRD list
```

### Option 2: Edit config.yaml
Change the line:
```yaml
aws_profile: LT-DEV
```
to:
```yaml
aws_profile: LT-PRD
```

---

## Common Use Cases

### Quick Health Check
```bash
rds-diagnose.bat ielts-idv-dev-v1-clusterinstance1
```

### Generate Daily Report
```bash
rds-report.bat ielts-idv-dev-v1-clusterinstance1 daily-report.txt 24h
```

### Generate Weekly Report
```bash
rds-report.bat ielts-idv-dev-v1-clusterinstance1 weekly-report.txt 7d
```

### Management Report (JSON)
```bash
rds-diag --config config.yaml report --instance ielts-idv-dev-v1-clusterinstance1 --report-type management --format json --output management-report.json
```

---

## Tips

1. **Tab Completion**: After typing `rds-diagnose.bat `, you can start typing the instance name and press Tab to autocomplete (if your shell supports it)

2. **Batch Processing**: Create a script to check multiple instances:
   ```batch
   @echo off
   for %%i in (instance1 instance2 instance3) do (
       rds-diagnose.bat %%i
   )
   ```

3. **Scheduled Reports**: Use Windows Task Scheduler to run reports automatically

4. **Different Environments**: Create separate config files:
   - `config-dev.yaml` (LT-DEV)
   - `config-prod.yaml` (LT-PRD)
   
   Then use: `rds-diag --config config-prod.yaml list`

---

## Full Command Reference

If you need the full syntax:
```bash
rds-diag --help
rds-diag list --help
rds-diag diagnose --help
rds-diag report --help
rds-diag check-permissions --help
```
