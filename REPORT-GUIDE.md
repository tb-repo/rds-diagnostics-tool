# RDS Diagnostics Tool - Report Guide

## Report Types

### 1. Technical Report (Default)
**For**: DBAs, DevOps Engineers, Technical Teams

**Contains**:
- Complete CloudWatch metrics with timestamps
- CPU, Memory, Connections, IOPS, Storage metrics
- Top 10 SQL queries with execution times
- Wait events analysis
- Full instance configuration
- Threshold violations with details
- Trend analysis
- Technical recommendations

**Generate**:
```bash
rds-report.bat --profile LT-SIT --instance ielts-ors-sit-v1-clusterinstance1 --output technical-report.txt
```

---

### 2. Management Report
**For**: Managers, Executives, Non-Technical Stakeholders

**Contains**:
- Executive summary
- Overall health status
- Key findings (high-level)
- Business impact assessment
- Actionable recommendations
- Metrics as percentages and trends (not raw values)

**Generate**:
```bash
rds-diag --config config.yaml --profile LT-SIT report --instance ielts-ors-sit-v1-clusterinstance1 --report-type management --output management-report.txt
```

---

## Output Formats

### Text Format (Default)
Human-readable, easy to read in any text editor
```bash
rds-report.bat --profile LT-SIT --instance my-instance --output report.txt
```

### JSON Format
Machine-readable, for automation and integration
```bash
rds-diag --config config.yaml --profile LT-SIT report --instance my-instance --format json --output report.json
```

---

## Common Use Cases

### Daily Health Check Report
```bash
rds-report.bat --profile LT-SIT --instance my-instance --output daily-$(date +%Y%m%d).txt --time-range 24h
```

### Weekly Performance Report
```bash
rds-report.bat --profile LT-PRD --instance prod-db --output weekly-report.txt --time-range 7d
```

### Incident Investigation
```bash
# Get detailed data for the last hour
rds-report.bat --profile LT-PRD --instance prod-db --output incident-report.txt --time-range 1h
```

### Management Presentation
```bash
# Generate executive summary
rds-diag --config config.yaml --profile LT-PRD report --instance prod-db --report-type management --output executive-summary.txt --time-range 7d
```

---

## What's in a Technical Report?

### Section 1: Instance Information
- Instance ID, Engine, Version
- Instance Class, Status
- Storage Type and Configuration
- Availability Zone

### Section 2: CloudWatch Metrics
- **CPU Utilization**: Timestamps and percentages
- **Memory**: Freeable memory over time
- **Connections**: Database connection count
- **IOPS**: Read/Write IOPS metrics
- **Storage**: Free and used storage

### Section 3: Performance Insights (if enabled)
- **Top SQL Queries**: 
  - Query text
  - Execution time
  - Execution count
  - Average execution time
- **Wait Events**:
  - Event names
  - Wait times
  - Wait counts

### Section 4: Analysis
- Threshold violations
- Trend analysis (improving/degrading/stable)
- Overall severity assessment

### Section 5: Recommendations
- Actionable items based on findings
- Capacity planning suggestions
- Performance optimization tips

---

## Tips

1. **Save reports with timestamps** for historical tracking:
   ```bash
   rds-report.bat --profile LT-SIT --instance my-db --output report-2026-02-19.txt
   ```

2. **Compare reports over time** to track performance trends

3. **Use JSON format** for automated monitoring:
   ```bash
   rds-diag --config config.yaml --profile LT-SIT report --instance my-db --format json --output report.json
   # Then parse with jq, Python, etc.
   ```

4. **Generate reports for multiple instances** with a script:
   ```batch
   @echo off
   for %%i in (db1 db2 db3) do (
       rds-report.bat --profile LT-SIT --instance %%i --output report-%%i.txt
   )
   ```
