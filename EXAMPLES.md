# RDS Diagnostics Tool - Usage Examples

This document provides practical examples for using the RDS Diagnostics Tool, including enhanced SQL performance analysis features.

## Table of Contents
- [Basic Usage](#basic-usage)
- [Using Different Profiles](#using-different-profiles)
- [Custom Time Ranges](#custom-time-ranges)
- [Enhanced SQL Analysis](#enhanced-sql-analysis)
- [Report Types and Formats](#report-types-and-formats)
- [Multi-Environment Workflow](#multi-environment-workflow)

---

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

### Custom time ranges
```bash
# Last hour (default)
rds-diagnose.bat --instance my-db --time-range 1h

# Last 6 hours
rds-diagnose.bat --instance my-db --time-range 6h

# Last 3 days
rds-diagnose.bat --instance my-db --time-range 3d
```

---

## Enhanced SQL Analysis

### Generate technical report with SQL metrics
```bash
# Default technical report includes enhanced SQL metrics
rds-report.bat --instance my-db --output sql-analysis.txt
```

**Output includes:**
- Full SQL query text
- Execution metrics (rate, count, time)
- Resource metrics (CPU time, lock time)
- Row metrics (examined vs. returned, efficiency ratio)
- I/O metrics (read/write bytes)
- Smart recommendations (INDEX, LOCK, CACHE, CPU)

### Analyze SQL performance over 24 hours
```bash
rds-report.bat --instance my-db --time-range 24h --output daily-sql.txt
```

### Generate SQL performance report for production
```bash
rds-report.bat --instance prod-db --profile LT-PRD --time-range 7d --output prod-sql-weekly.txt
```

### Export SQL metrics as JSON for analysis
```bash
rds-report.bat --instance my-db --format json --output sql-metrics.json
```

**JSON output includes all enhanced metrics:**
```json
{
  "sql_queries": [
    {
      "query_id": "0x1A2B3C4D5E6F7890",
      "query_text": "SELECT * FROM orders WHERE customer_id = ?",
      "total_execution_time": 45230.5,
      "average_execution_time": 125.3,
      "execution_count": 361,
      "engine_type": "mysql",
      "executions_per_second": 0.5,
      "cpu_time": 38450.2,
      "lock_time": 1250.3,
      "rows_examined": 1250000,
      "rows_returned": 1250,
      "read_io_bytes": 537395200,
      "write_io_bytes": 0
    }
  ]
}
```

---

## Report Types and Formats

### Technical Report (Detailed)
```bash
# Text format (default)
rds-report.bat --instance my-db --report-type technical --output technical.txt

# JSON format
rds-report.bat --instance my-db --report-type technical --format json --output technical.json
```

**Best for:** DBAs, developers, detailed troubleshooting

**Includes:**
- Full SQL query text
- All enhanced metrics
- Detailed recommendations with impact estimates
- CloudWatch metrics
- Wait events

### Management Report (Executive Summary)
```bash
# Text format
rds-report.bat --instance my-db --report-type management --output management.txt

# JSON format
rds-report.bat --instance my-db --report-type management --format json --output management.json
```

**Best for:** Managers, executives, high-level overview

**Includes:**
- SQL performance summary
- Top 3 problematic queries
- Key recommendations by category
- High-level metrics
- Severity assessment

### Compare report types
```bash
# Generate both reports for comparison
rds-report.bat --instance my-db --report-type technical --output tech.txt
rds-report.bat --instance my-db --report-type management --output mgmt.txt
```

---

## Complete Examples

### Full diagnostic with all options
```bash
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1 --time-range 24h --profile LT-SIT --region ap-southeast-1 --verbose
```

### Generate management report in JSON
```bash
rds-diag --profile LT-PRD --config config.yaml report --instance prod-db --report-type management --format json --output management.json
```

### Weekly SQL performance analysis
```bash
# Technical report with 7 days of SQL metrics
rds-report.bat --instance my-db --time-range 7d --output weekly-sql-analysis.txt

# Export as JSON for further processing
rds-report.bat --instance my-db --time-range 7d --format json --output weekly-sql-data.json
```

### Troubleshoot specific SQL performance issue
```bash
# 1. Run diagnosis to identify issues
rds-diagnose.bat --instance my-db --time-range 24h --verbose

# 2. Generate detailed technical report
rds-report.bat --instance my-db --time-range 24h --output troubleshooting.txt

# 3. Review SQL recommendations in the report
# Look for INDEX, LOCK, CACHE, or CPU recommendations
```

### Monthly performance review
```bash
# Generate management report for stakeholders
rds-report.bat --instance prod-db --profile LT-PRD --time-range 30d --report-type management --output monthly-review.txt

# Generate technical report for DBA team
rds-report.bat --instance prod-db --profile LT-PRD --time-range 30d --report-type technical --output monthly-technical.txt
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

### Weekly SQL performance review across environments
```bash
# Development
rds-report.bat --instance dev-db --profile LT-DEV --time-range 7d --output dev-weekly.txt

# Staging
rds-report.bat --instance sit-db --profile LT-SIT --time-range 7d --output sit-weekly.txt

# Production
rds-report.bat --instance prd-db --profile LT-PRD --time-range 7d --output prd-weekly.txt
```

### Compare SQL performance across environments
```bash
# Export JSON for all environments
rds-report.bat --instance dev-db --profile LT-DEV --format json --output dev-sql.json
rds-report.bat --instance sit-db --profile LT-SIT --format json --output sit-sql.json
rds-report.bat --instance prd-db --profile LT-PRD --format json --output prd-sql.json

# Use external tools to compare JSON files
```

---

## Advanced Use Cases

### Identify slow queries during peak hours
```bash
# Run report during peak hours (e.g., 9 AM - 5 PM)
# Use 1-hour time range for recent data
rds-report.bat --instance my-db --time-range 1h --output peak-hour-analysis.txt
```

### Monitor SQL performance after deployment
```bash
# Before deployment
rds-report.bat --instance my-db --time-range 1h --output before-deployment.txt

# After deployment (wait 1 hour for data)
rds-report.bat --instance my-db --time-range 1h --output after-deployment.txt

# Compare reports to identify regressions
```

### Generate reports for multiple instances
```bash
# Create a batch script to generate reports for all instances
for instance in db1 db2 db3; do
  rds-report.bat --instance $instance --output ${instance}-report.txt
done
```

---

## Tips and Best Practices

1. **Use appropriate time ranges:**
   - 1h for real-time troubleshooting
   - 24h for daily reviews
   - 7d for weekly analysis
   - 30d for monthly reports

2. **Choose the right report type:**
   - Technical reports for detailed SQL analysis
   - Management reports for executive summaries

3. **Export as JSON for automation:**
   - Integrate with monitoring systems
   - Build custom dashboards
   - Automate alerting

4. **Review SQL recommendations regularly:**
   - INDEX recommendations can significantly improve performance
   - LOCK recommendations help identify concurrency issues
   - CACHE recommendations optimize frequently-run queries
   - CPU recommendations highlight optimization opportunities

5. **Enable Performance Insights:**
   - Required for enhanced SQL metrics
   - Provides detailed query-level insights
   - Minimal performance impact on RDS instances

For more detailed information, see:
- [ENHANCED-SQL-GUIDE.md](ENHANCED-SQL-GUIDE.md) - Comprehensive guide to SQL features
- [QUICK-REFERENCE.md](QUICK-REFERENCE.md) - Quick reference card
- [README.md](README.md) - Full documentation
