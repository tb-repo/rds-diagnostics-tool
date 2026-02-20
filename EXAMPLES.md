# RDS Diagnostics Tool - Usage Examples

## Basic Usage (Using Defaults from config.yaml)

### List all RDS instances
```bash
rds-list.bat
```

### Diagnose an instance
```bash
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1
```

### Generate a report
```bash
rds-report.bat --instance ielts-idv-dev-v1-clusterinstance1 --output my-report.txt
```

---

## Using Different Profiles

### List instances in LT-SIT
```bash
rds-list.bat --profile LT-SIT
```

### Diagnose instance in LT-PRD
```bash
rds-diagnose.bat --instance prod-db-instance --profile LT-PRD
```

### Generate report for DM-DEV
```bash
rds-report.bat --instance dm-db-instance --output dm-report.txt --profile DM-DEV
```

---

## Custom Time Ranges

### Diagnose last 24 hours
```bash
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1 --time-range 24h
```

### Weekly report (7 days)
```bash
rds-report.bat --instance ielts-idv-dev-v1-clusterinstance1 --output weekly.txt --time-range 7d
```

---

## Complete Examples

### Full diagnostic with all options
```bash
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1 --time-range 24h --profile LT-SIT --region ap-southeast-1
```

### Generate management report in JSON
```bash
rds-diag --config config.yaml --profile LT-PRD report --instance prod-db --report-type management --format json --output management.json
```

---

## Multi-Environment Workflow

### Check all environments
```bash
# Development
rds-list.bat --profile LT-DEV

# Staging  
rds-list.bat --profile LT-SIT

# Production
rds-list.bat --profile LT-PRD
```

### Daily health check across environments
```bash
rds-diagnose.bat --instance dev-db --profile LT-DEV
rds-diagnose.bat --instance sit-db --profile LT-SIT
rds-diagnose.bat --instance prd-db --profile LT-PRD
```
