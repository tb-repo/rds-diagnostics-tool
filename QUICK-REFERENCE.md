# RDS Diagnostics Tool - Quick Reference

## Essential Commands

### List Instances
```bash
rds-diag list --profile your-profile
```

### Quick Health Check
```bash
rds-diag diagnose -i instance-name --profile your-profile
```

### Detailed Technical Report
```bash
rds-diag report -i instance-name -t 24h -o report.txt --profile your-profile
```

### Management Summary
```bash
rds-diag report -i instance-name --report-type management --profile your-profile
```

### JSON Output (for automation)
```bash
rds-diag report -i instance-name -f json -o report.json --profile your-profile
```

### Check Permissions
```bash
rds-diag check-permissions --profile your-profile
```

## Time Range Options

| Format | Description | Example |
|--------|-------------|---------|
| `15m` | 15 minutes | `-t 15m` |
| `1h` | 1 hour (default) | `-t 1h` |
| `6h` | 6 hours | `-t 6h` |
| `24h` | 24 hours | `-t 24h` |
| `7d` | 7 days | `-t 7d` |

## Report Types

| Type | Description | Use Case |
|------|-------------|----------|
| `technical` | Detailed metrics and SQL analysis | DBAs, troubleshooting |
| `management` | Executive summary | Management reviews |

## Output Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `text` | Human-readable text | Console viewing, reports |
| `json` | Machine-readable JSON | Automation, dashboards |

## SQL Recommendation Categories

| Category | What It Detects | Priority |
|----------|----------------|----------|
| `INDEX` | Low efficiency ratio (rows examined >> returned) | High |
| `LOCK` | High lock contention (>30% lock time) | High |
| `CPU` | CPU-intensive queries (>80% CPU time) | Medium |
| `CACHE` | High-frequency fast queries | Medium |

## Common Workflows

### Daily Health Check
```bash
rds-diag diagnose -i prod-db -t 1h --profile prod
```

### Weekly Performance Review
```bash
rds-diag report -i prod-db -t 7d --report-type management -o weekly.txt --profile prod
```

### Troubleshooting High CPU
```bash
# Step 1: Quick diagnostic
rds-diag diagnose -i prod-db -t 24h --profile prod

# Step 2: Detailed report
rds-diag report -i prod-db -t 24h -o cpu-analysis.txt --profile prod

# Step 3: Review [CPU] and [INDEX] recommendations
```

### Pre-Production Validation
```bash
# Check staging before promoting
rds-diag diagnose -i staging-db -t 1h --profile staging
rds-diag report -i staging-db -t 1h --profile staging
```

### Automated Monitoring
```bash
# Generate JSON for monitoring system
rds-diag report -i prod-db -t 1h -f json -o metrics.json --profile prod

# Extract critical issues
cat metrics.json | jq '.recommendations[] | select(.severity == "critical")'
```

## Windows Batch Scripts

```batch
REM List instances
rds-list.bat

REM Quick diagnostic
rds-diagnose.bat instance-name

REM Generate report
rds-report.bat instance-name

REM Advanced diagnostic (24h)
rds-diagnose-advanced.bat instance-name 24h
```

## Enhanced SQL Metrics

### What's Collected
- ✅ Execution metrics (calls/sec, execution time)
- ✅ Resource metrics (CPU time, lock time)
- ✅ Row metrics (examined vs. returned)
- ✅ I/O metrics (read/write bytes)
- ✅ Intelligent recommendations

### Requirements
- Performance Insights must be enabled
- IAM permissions: `pi:DescribeDimensionKeys`, `pi:GetResourceMetrics`

### Interpreting Metrics

**Efficiency Ratio:**
- 100%: Perfect
- 10-50%: Good
- 1-10%: Poor - add indexes
- <1%: Critical - immediate action

**Lock Time %:**
- <10%: Normal
- 10-30%: Monitor
- 30-50%: Review transactions
- >50%: Critical

**CPU Time %:**
- <50%: Normal
- 50-80%: Optimize
- >80%: CPU-intensive

**Executions/sec:**
- <0.1: Low
- 0.1-1.0: Moderate
- 1.0-10: High - consider caching
- >10: Very high - cache strongly recommended

## Troubleshooting

### Performance Insights Not Enabled
Enable in AWS Console → RDS → Modify → Performance Insights

### Missing Permissions
```bash
rds-diag check-permissions --profile your-profile
```

### No SQL Queries Found
Try longer time range: `-t 24h` or `-t 7d`

### Authentication Errors
```bash
aws sso login --profile your-profile
```

## Tips

1. **Use verbose mode** for troubleshooting: `--verbose`
2. **Save reports** for comparison: `-o report-$(date +%Y%m%d).txt`
3. **Check permissions first** when setting up new profiles
4. **Start with 1h** time range, increase if needed
5. **Act on CRITICAL** recommendations first
6. **Baseline metrics** during normal operation
7. **Track changes** before/after optimizations

## Getting Help

```bash
# General help
rds-diag --help

# Command-specific help
rds-diag diagnose --help
rds-diag report --help

# Version info
rds-diag version
```

## Example Output Snippets

### Diagnostic Summary
```
Overall Status: WARNING

Threshold Violations (2):
  ⚠️  CPUUtilization: 78.50 (threshold: 75.00)
  ⚠️  DatabaseConnections: 145.00 (threshold: 100.00)

=== SQL Query Recommendations (3 issues found) ===

CRITICAL SQL Issues (1):
  • [INDEX] Query sql-abc123: Query examines 100,000 rows...

✓ Performance Insights enabled (10 queries analyzed)
```

### SQL Query Details (Technical Report)
```
Query ID: sql-abc123
Engine: mysql
Total Execution Time: 5000.0 ms
Average Execution Time: 50.0 ms
Execution Count: 100
Executions/sec: 0.5 calls/sec
CPU Time: 4200.0 ms (84.0% of total)
Lock Time: 300.0 ms (6.0% of total)
Rows Examined: 100,000
Rows Returned: 50
Efficiency Ratio: 0.05% (index opportunity)
Read I/O: 2.0 MB
Write I/O: 0.0 MB

SQL Text:
SELECT * FROM users WHERE email LIKE '%@example.com'
```

## Quick Decision Tree

```
Need to...
├─ Check if instance is healthy?
│  └─ rds-diag diagnose -i instance-name
│
├─ Get detailed metrics?
│  └─ rds-diag report -i instance-name -t 24h
│
├─ Share with management?
│  └─ rds-diag report -i instance-name --report-type management
│
├─ Automate monitoring?
│  └─ rds-diag report -i instance-name -f json
│
├─ Troubleshoot slow queries?
│  └─ rds-diag report -i instance-name -t 24h
│     (Look for [INDEX], [CPU], [LOCK] recommendations)
│
└─ Verify permissions?
   └─ rds-diag check-permissions
```
