# RDS Diagnostics Tool - Command Reference Guide

## Table of Contents
1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Command List](#command-list)
4. [Detailed Command Examples](#detailed-command-examples)
5. [Batch Script Shortcuts](#batch-script-shortcuts)
6. [Output Formats](#output-formats)

---

## Overview

The RDS Diagnostics Tool helps you quickly diagnose and analyze AWS RDS instance performance issues. It collects CloudWatch metrics, Performance Insights data, and generates formatted reports for technical and management audiences.

**Key Features:**
- List all RDS instances in a region
- Collect performance metrics (CPU, memory, connections, IOPS, storage)
- Analyze Performance Insights data (top queries, wait events, databases, users)
- Generate technical and management reports
- Support for multiple AWS profiles and regions
- Configurable time ranges and thresholds

---

## Installation & Setup

### Install the Tool
```bash
pip install -e .
```

### Verify Installation
```bash
rds-diag --version
```

### Configure AWS Credentials
Ensure your AWS credentials are configured:
```bash
aws configure --profile LT-SIT
```

---

## Command List

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `rds-diag list` | List all RDS instances | `--profile`, `--region` |
| `rds-diag diagnose` | Run diagnostics on an instance | `--instance`, `--time-range`, `--profile` |
| `rds-diag report` | Generate detailed report | `--instance`, `--report-type`, `--format`, `--output` |
| `rds-diag --help` | Show help documentation | - |
| `rds-diag --version` | Show version information | - |

---

## Detailed Command Examples

### 1. List All RDS Instances

**Purpose:** Discover all RDS instances in your AWS account/region

#### Basic Usage
```bash
rds-diag --profile LT-SIT list
```

#### Sample Output
```
================================================================================
RDS Instances in region ap-southeast-1
================================================================================

Found 8 instances:

1. ielts-ors-sit-v1-clusterinstance1
   Engine: aurora-postgresql 15.12
   Class: db.t4g.large
   Status: available
   Storage: aurora (Auto-scaling cluster storage)

2. ielts-ors-sit-v1-clusterinstance2
   Engine: aurora-postgresql 15.12
   Class: db.t4g.large
   Status: available
   Storage: aurora (Auto-scaling cluster storage)

3. myapp-database
   Engine: postgres 14.7
   Class: db.t3.medium
   Status: available
   Storage: gp2 (100 GB)

4. legacy-mysql-db
   Engine: mysql 8.0.32
   Class: db.t3.small
   Status: available
   Storage: gp2 (50 GB)

... (4 more instances)

================================================================================
```

#### With Different Region
```bash
rds-diag --profile LT-PRD --region us-east-1 list
```

---

### 2. Run Quick Diagnostics

**Purpose:** Get a quick health check summary of an RDS instance

#### Basic Usage (Default: Last 1 hour)
```bash
rds-diag --profile LT-SIT diagnose --instance ielts-ors-sit-v1-clusterinstance1
```

#### Sample Output
```
2026-02-19 17:06:12 - aws.clients - INFO - Created AWS session with profile: LT-SIT
2026-02-19 17:06:12 - core.app - INFO - Running diagnostics for instance: ielts-ors-sit-v1-clusterinstance1
2026-02-19 17:06:12 - core.app - INFO - Collecting instance information...
2026-02-19 17:06:12 - core.app - INFO - Collecting CloudWatch metrics...
2026-02-19 17:06:14 - core.app - INFO - Collecting Performance Insights data...
2026-02-19 17:06:57 - collectors.performance_insights - INFO - Collected 10 top SQL queries
2026-02-19 17:06:57 - collectors.performance_insights - INFO - Collected 8 wait events
2026-02-19 17:06:57 - collectors.performance_insights - INFO - Collected 5 top databases
2026-02-19 17:06:57 - collectors.performance_insights - INFO - Collected 3 top users
2026-02-19 17:06:57 - core.app - INFO - Diagnostics completed successfully

================================================================================
Diagnostic Summary for ielts-ors-sit-v1-clusterinstance1
================================================================================

Instance Details:
  Engine: aurora-postgresql 15.12
  Instance Class: db.t4g.large
  Status: available
  Storage: aurora (Auto-scaling cluster storage)
  Availability Zone: ap-southeast-1c

Overall Status: NORMAL

✓ No threshold violations detected

Recommendations (2):
  1. CPUUtilization is increasing rapidly (26.3%). Investigate root cause and plan capacity adjustments.
  2. TotalIOPS is increasing rapidly (148.0%). Investigate root cause and plan capacity adjustments.

✓ Performance Insights enabled (10 queries analyzed)

================================================================================
For detailed report, use: rds-diag report --instance ielts-ors-sit-v1-clusterinstance1 --time-range 1h
```

#### With Custom Time Range (15 minutes)
```bash
rds-diag --profile LT-SIT diagnose --instance ielts-ors-sit-v1-clusterinstance1 --time-range 15m
```

#### With Custom Time Range (24 hours)
```bash
rds-diag --profile LT-SIT diagnose --instance myapp-database --time-range 24h
```

#### With Custom Time Range (7 days)
```bash
rds-diag --profile LT-PRD diagnose --instance prod-database --time-range 7d
```

---

### 3. Generate Technical Report

**Purpose:** Create a detailed technical report with all metrics, queries, and analysis

#### Generate to Console (Text Format)
```bash
rds-diag --profile LT-SIT report --instance ielts-ors-sit-v1-clusterinstance1 --time-range 15m
```

#### Sample Output (Technical Report - Text)
```
================================================================================
RDS DIAGNOSTICS REPORT - TECHNICAL
================================================================================
Generated: 2026-02-19 17:11:26 UTC

INSTANCE INFORMATION
--------------------------------------------------------------------------------
Instance ID:       ielts-ors-sit-v1-clusterinstance1
Resource ID:       db-ABCDEFGHIJKLMNOPQRSTUVWXYZ
Engine:            aurora-postgresql 15.12
Instance Class:    db.t4g.large
Status:            available
Storage Type:      aurora
Allocated Storage: Auto-scaling (cluster-level)
Max Connections:   Dynamic (formula-based)
Availability Zone: ap-southeast-1c

ANALYSIS SUMMARY
--------------------------------------------------------------------------------
Overall Severity: NORMAL
Summary: All metrics within normal thresholds. Continue regular monitoring.

THRESHOLD VIOLATIONS
--------------------------------------------------------------------------------
✓ No threshold violations detected

CLOUDWATCH METRICS
--------------------------------------------------------------------------------
CPU Utilization:
  Average: 23.45%
  Maximum: 45.67%
  Minimum: 12.34%
  Latest:  26.30% at 17:11:00

Freeable Memory:
  Average: 6.78 GB
  Maximum: 7.12 GB
  Minimum: 6.45 GB
  Latest:  6.89 GB at 17:11:00

Database Connections:
  Average: 15
  Maximum: 23
  Minimum: 8
  Latest:  18 (1.8% of max) at 17:11:00

IOPS:
  Read IOPS Average:  45.23
  Write IOPS Average: 102.45
  Total IOPS Average: 147.68

Storage:
  Type: Auto-scaling cluster storage
  Current Total: 25.34 GB
  Used: 18.67 GB (73.7%)
  Free: 6.67 GB

METRIC TRENDS
--------------------------------------------------------------------------------
📈 CPUUtilization is increasing rapidly (26.3%). Investigate root cause and plan capacity adjustments.
📈 TotalIOPS is increasing rapidly (148.0%). Investigate root cause and plan capacity adjustments.

TOP SQL QUERIES (Performance Insights)
--------------------------------------------------------------------------------
Note: Values represent database load (Average Active Sessions)

1. Query ID: 0x1A2B3C4D5E6F7890
   Total Load: 2.45 AAS
   Average Load: 0.2450 AAS
   Time Samples: 10
   SQL: SELECT * FROM orders WHERE status = 'pending' AND created_at > NOW() - INTERVAL '1 day' ORDER BY created_at DESC LIMIT 100

2. Query ID: 0x9F8E7D6C5B4A3210
   Total Load: 1.89 AAS
   Average Load: 0.1890 AAS
   Time Samples: 10
   SQL: UPDATE inventory SET quantity = quantity - 1 WHERE product_id = $1 AND quantity > 0

3. Query ID: 0xABCDEF1234567890
   Total Load: 1.23 AAS
   Average Load: 0.1230 AAS
   Time Samples: 10
   Wait Events: IO:DataFileRead, Lock:relation
   SQL: SELECT u.*, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id HAVING COUNT(o.id) > 10

... (7 more queries)

WAIT EVENTS
--------------------------------------------------------------------------------
• IO:DataFileRead
  Total Wait Time: 3.45s
  Wait Count: 234

• Lock:relation
  Total Wait Time: 1.23s
  Wait Count: 45

• CPU
  Total Wait Time: 0.89s
  Wait Count: 156

... (5 more wait events)

TOP DATABASES BY LOAD
--------------------------------------------------------------------------------
1. ielts_ors_production
   Total Load: 4.56 AAS
   Load %: 65.2%

2. ielts_ors_reporting
   Total Load: 1.89 AAS
   Load %: 27.0%

3. postgres
   Total Load: 0.55 AAS
   Load %: 7.8%

TOP USERS BY LOAD
--------------------------------------------------------------------------------
1. app_user
   Total Load: 5.23 AAS
   Load %: 74.7%

2. reporting_user
   Total Load: 1.45 AAS
   Load %: 20.7%

3. admin_user
   Total Load: 0.32 AAS
   Load %: 4.6%

RECOMMENDATIONS
--------------------------------------------------------------------------------
1. CPUUtilization is increasing rapidly (26.3%). Investigate root cause and plan capacity adjustments.
2. TotalIOPS is increasing rapidly (148.0%). Investigate root cause and plan capacity adjustments.

================================================================================
END OF REPORT
================================================================================
```

#### Save to File
```bash
rds-diag --profile LT-SIT report --instance ielts-ors-sit-v1-clusterinstance1 --time-range 15m --output detailed-report.txt
```

Output:
```
Report generated successfully
Report saved to: detailed-report.txt
```

#### Generate JSON Format
```bash
rds-diag --profile LT-SIT report --instance ielts-ors-sit-v1-clusterinstance1 --format json --output report.json
```

#### Sample Output (Technical Report - JSON)
```json
{
  "generated_at": "2026-02-19T17:11:26.123456",
  "instance": {
    "instance_id": "ielts-ors-sit-v1-clusterinstance1",
    "resource_id": "db-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "engine": "aurora-postgresql",
    "engine_version": "15.12",
    "instance_class": "db.t4g.large",
    "status": "available",
    "storage_type": "aurora",
    "allocated_storage_gb": 1,
    "max_connections": 0,
    "availability_zone": "ap-southeast-1c"
  },
  "analysis": {
    "overall_severity": "normal",
    "summary": "All metrics within normal thresholds. Continue regular monitoring.",
    "violations": [],
    "trends": [
      {
        "metric_name": "CPUUtilization",
        "trend": "degrading",
        "change_percentage": 26.3,
        "description": "CPUUtilization is increasing rapidly (26.3%). Investigate root cause and plan capacity adjustments."
      }
    ]
  },
  "metrics": {
    "cpu_utilization": {
      "average": 23.45,
      "max": 45.67,
      "min": 12.34,
      "unit": "Percent"
    },
    "freeable_memory_gb": {
      "average": 6.78,
      "max": 7.12,
      "min": 6.45,
      "unit": "GB"
    },
    "database_connections": {
      "average": 15.0,
      "max": 23.0,
      "min": 8.0,
      "unit": "Count"
    },
    "storage_usage_percent": 73.7
  },
  "performance_insights": {
    "available": true,
    "note": "Load values represent Average Active Sessions (AAS), not execution time",
    "top_queries": [
      {
        "query_id": "0x1A2B3C4D5E6F7890",
        "total_load_aas": 2.45,
        "average_load_aas": 0.245,
        "time_samples": 10,
        "query_text": "SELECT * FROM orders WHERE status = 'pending' AND created_at > NOW() - INTERVAL '1 day' ORDER BY created_at DESC LIMIT 100",
        "wait_events": []
      }
    ],
    "top_databases": [
      {
        "database_name": "ielts_ors_production",
        "total_load_aas": 4.56,
        "load_percentage": 65.2
      }
    ],
    "top_users": [
      {
        "user_name": "app_user",
        "total_load_aas": 5.23,
        "load_percentage": 74.7
      }
    ]
  },
  "recommendations": [
    "CPUUtilization is increasing rapidly (26.3%). Investigate root cause and plan capacity adjustments.",
    "TotalIOPS is increasing rapidly (148.0%). Investigate root cause and plan capacity adjustments."
  ]
}
```

---

### 4. Generate Management Report

**Purpose:** Create a concise executive summary for management audiences

#### Generate Management Report
```bash
rds-diag --profile LT-SIT report --instance ielts-ors-sit-v1-clusterinstance1 --report-type management --time-range 24h
```

#### Sample Output (Management Report)
```
======================================================================
RDS DIAGNOSTICS REPORT - EXECUTIVE SUMMARY
======================================================================
Report Date: 2026-02-19 17:11
Instance: ielts-ors-sit-v1-clusterinstance1

EXECUTIVE SUMMARY
----------------------------------------------------------------------
The RDS instance is operating within normal parameters. All monitored 
metrics are within acceptable thresholds. Continue regular monitoring. 
Note: 2 metrics show increasing trends that warrant attention.

SEVERITY ASSESSMENT
----------------------------------------------------------------------
Status: ✓ NORMAL - No Issues Detected

PERFORMANCE METRICS
----------------------------------------------------------------------
CPU Utilization:     23.5%
Connection Usage:    1.8%
Storage Usage:       73.7%
  CPUUtilization: ↑ 26%
  TotalIOPS: ↑ 148%

RECOMMENDED ACTIONS
----------------------------------------------------------------------
Additional Recommendations:
  1. CPUUtilization is increasing rapidly (26.3%). Investigate root cause and plan capacity adjustments.
  2. TotalIOPS is increasing rapidly (148.0%). Investigate root cause and plan capacity adjustments.

======================================================================
For detailed technical analysis, request a technical report.
======================================================================
```

#### Save Management Report to File
```bash
rds-diag --profile LT-PRD report --instance prod-database --report-type management --output executive-summary.txt
```

---

### 5. Verbose Mode

**Purpose:** See detailed progress information during execution

```bash
rds-diag --profile LT-SIT --verbose diagnose --instance ielts-ors-sit-v1-clusterinstance1
```

Output includes detailed logging:
```
2026-02-19 17:06:12 - aws.clients - INFO - Created AWS session with profile: LT-SIT
2026-02-19 17:06:12 - botocore.credentials - INFO - Found credentials in shared credentials file: ~/.aws/credentials
2026-02-19 17:06:12 - core.app - INFO - Running diagnostics for instance: ielts-ors-sit-v1-clusterinstance1
2026-02-19 17:06:12 - core.app - INFO - Using default time range: 1h
2026-02-19 17:06:12 - core.app - INFO - Collecting instance information...
2026-02-19 17:06:12 - collectors.instance_info - INFO - Retrieved instance details for ielts-ors-sit-v1-clusterinstance1
2026-02-19 17:06:12 - core.app - INFO - Collecting CloudWatch metrics...
2026-02-19 17:06:12 - collectors.metrics - INFO - Collecting all metrics for instance ielts-ors-sit-v1-clusterinstance1
2026-02-19 17:06:13 - collectors.metrics - INFO - Collected CPU utilization metrics: 60 data points
2026-02-19 17:06:13 - collectors.metrics - INFO - Collected memory metrics: 60 data points
... (more detailed logs)
```

---

### 6. Help and Version

#### Show Help
```bash
rds-diag --help
```

#### Show Command-Specific Help
```bash
rds-diag list --help
rds-diag diagnose --help
rds-diag report --help
```

#### Show Version
```bash
rds-diag --version
```

Output:
```
RDS Diagnostics Tool version 1.0.0
```

---

## Batch Script Shortcuts

For convenience, use the provided batch scripts with simplified syntax:

### List Instances
```bash
./rds-list.bat --profile LT-SIT
```

### Quick Diagnose
```bash
./rds-diagnose.bat --profile LT-SIT --instance ielts-ors-sit-v1-clusterinstance1 --time-range 15m
```

### Generate Report
```bash
./rds-report.bat --profile LT-SIT --instance ielts-ors-sit-v1-clusterinstance1 --output detailed-report.txt --time-range 15m
```

### Check Instance Health
```bash
./rds-check.bat --profile LT-SIT --instance ielts-ors-sit-v1-clusterinstance1
```

---

## Output Formats

### Supported Formats
- **Text** (default): Human-readable formatted output
- **JSON**: Machine-readable structured data

### Format Comparison

| Format | Use Case | Example |
|--------|----------|---------|
| Text | Human review, documentation | `--format text` |
| JSON | Automation, integration, parsing | `--format json` |

---

## Common Use Cases

### 1. Daily Health Check
```bash
# Check all instances in production
rds-diag --profile LT-PRD list

# Quick diagnose critical instances
rds-diag --profile LT-PRD diagnose --instance prod-db-1
rds-diag --profile LT-PRD diagnose --instance prod-db-2
```

### 2. Incident Investigation
```bash
# Get detailed 24-hour report
rds-diag --profile LT-PRD report --instance affected-db --time-range 24h --output incident-report.txt

# Check Performance Insights for slow queries
rds-diag --profile LT-PRD report --instance affected-db --time-range 1h --format json --output pi-data.json
```

### 3. Capacity Planning
```bash
# Generate 7-day trend report
rds-diag --profile LT-PRD report --instance prod-db --time-range 7d --output capacity-analysis.txt
```

### 4. Management Reporting
```bash
# Weekly executive summary
rds-diag --profile LT-PRD report --instance prod-db --report-type management --time-range 7d --output weekly-summary.txt
```

### 5. Multi-Environment Monitoring
```bash
# Check all environments
rds-diag --profile LT-DEV diagnose --instance dev-db
rds-diag --profile LT-SIT diagnose --instance sit-db
rds-diag --profile LT-UAT diagnose --instance uat-db
rds-diag --profile LT-PRD diagnose --instance prod-db
```

---

## Time Range Options

| Format | Description | Example |
|--------|-------------|---------|
| `15m` | 15 minutes | `--time-range 15m` |
| `30m` | 30 minutes | `--time-range 30m` |
| `1h` | 1 hour (default) | `--time-range 1h` |
| `6h` | 6 hours | `--time-range 6h` |
| `24h` | 24 hours | `--time-range 24h` |
| `7d` | 7 days | `--time-range 7d` |
| `30d` | 30 days | `--time-range 30d` |

---

## Tips and Best Practices

1. **Start with `list`**: Always list instances first to verify connectivity and see available instances

2. **Use appropriate time ranges**:
   - Real-time issues: `15m` or `30m`
   - Recent trends: `1h` or `6h`
   - Daily analysis: `24h`
   - Weekly reports: `7d`

3. **Save important reports**: Use `--output` to save reports for documentation and comparison

4. **Use JSON for automation**: Parse JSON output in scripts for automated monitoring

5. **Check Performance Insights**: If enabled, it provides the most valuable query-level insights

6. **Monitor trends**: Look for "degrading" trends even when metrics are within thresholds

7. **Regular health checks**: Run daily diagnostics on critical instances

8. **Profile management**: Use descriptive profile names (LT-PRD, LT-SIT) for clarity

---

## Troubleshooting

### Common Issues

**Issue**: `ERROR: Authentication failed`
**Solution**: Refresh AWS credentials
```bash
aws sso login --profile LT-SIT
```

**Issue**: `ERROR: Instance not found`
**Solution**: Verify instance ID and region
```bash
rds-diag --profile LT-SIT list
```

**Issue**: `Performance Insights not enabled`
**Solution**: This is informational - the tool will still collect CloudWatch metrics

**Issue**: `ERROR: Invalid duration format`
**Solution**: Use correct format: `15m`, `1h`, `24h`, `7d`

---

## Support

For issues or questions:
1. Check this command reference
2. Run `rds-diag --help` for built-in documentation
3. Review the README.md file
4. Check the EXAMPLES.md file for more use cases

---

**Last Updated**: February 2026
**Version**: 1.0.0
