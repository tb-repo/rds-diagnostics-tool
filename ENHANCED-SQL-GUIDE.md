# Enhanced SQL Metadata Collection - User Guide

## What's New

The RDS Diagnostics Tool now collects comprehensive SQL query metrics from AWS Performance Insights, including:

- **Execution Metrics**: Executions per second, total/average execution time
- **Resource Metrics**: CPU time, lock time
- **Row Metrics**: Rows examined vs. rows returned (efficiency analysis)
- **I/O Metrics**: Read and write I/O bytes
- **Intelligent Recommendations**: Automated analysis identifying:
  - Index optimization opportunities
  - Lock contention issues
  - Caching candidates
  - CPU-intensive queries

## Prerequisites

### Required IAM Permissions

Your AWS profile needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "cloudwatch:GetMetricStatistics",
        "pi:DescribeDimensionKeys",
        "pi:GetResourceMetrics"
      ],
      "Resource": "*"
    }
  ]
}
```

**Check your permissions:**
```bash
rds-diag check-permissions --profile your-profile
```

### Performance Insights Must Be Enabled

Enhanced SQL metrics require Performance Insights to be enabled on your RDS instance. If not enabled, the tool will still work but will only show basic CloudWatch metrics.

## Available Commands

### 1. List RDS Instances

```bash
# List all instances in default region
rds-diag list

# List instances in specific region
rds-diag list --profile lt-prd --region us-east-1
```

**Output:**
```
Found 3 RDS instance(s):

Instance ID                    Engine          Status       Instance Class
--------------------------------------------------------------------------------
my-prod-db                     mysql           available    db.r5.xlarge
my-staging-db                  postgres        available    db.t3.medium
my-aurora-cluster              aurora-mysql    available    db.r5.large
```

### 2. Run Quick Diagnostics

```bash
# Quick diagnostic check (1 hour of data)
rds-diag diagnose --instance my-prod-db --profile lt-prd

# Diagnostic check for last 24 hours
rds-diag diagnose -i my-prod-db -t 24h --profile lt-prd

# Diagnostic check for last 7 days with verbose output
rds-diag diagnose -i my-prod-db -t 7d --verbose --profile lt-prd
```

**Sample Output:**
```
================================================================================
Diagnostic Summary for my-prod-db
================================================================================

Instance Details:
  Engine: mysql 8.0.35
  Instance Class: db.r5.xlarge
  Status: available
  Storage: gp3 (500 GB)
  Availability Zone: ap-southeast-1a

Overall Status: WARNING

Threshold Violations (2):
  ⚠️  CPUUtilization: 78.50 (threshold: 75.00)
  ⚠️  DatabaseConnections: 145.00 (threshold: 100.00)

Recommendations (5):
  1. WARNING: CPU utilization is elevated. Monitor for continued growth.
  2. Review top SQL queries for optimization opportunities.
  3. Connection count is high. Review connection pooling settings and check for connection leaks.
  
  === SQL Query Recommendations (3 issues found) ===
  
  CRITICAL SQL Issues (1):
    • [INDEX] Query sql-abc123: Query examines 100,000 rows but returns only 50 rows (efficiency: 0.1%). Consider adding indexes to improve query selectivity.
  
  WARNING SQL Issues (2):
    • [LOCK] Query sql-xyz789: Query spends 35.2% of execution time waiting for locks. Consider reviewing transaction isolation levels.
    • [CPU] Query sql-def456: Query is CPU-intensive, using 87.3% of execution time on CPU. Consider query optimization.

✓ Performance Insights enabled (10 queries analyzed)

================================================================================

For detailed report, use: rds-diag report --instance my-prod-db --time-range 1h
```

### 3. Generate Detailed Reports

#### Technical Report (Detailed Metrics)

```bash
# Generate technical report to stdout
rds-diag report --instance my-prod-db --profile lt-prd

# Generate technical report for 24 hours
rds-diag report -i my-prod-db -t 24h --profile lt-prd

# Save technical report to file
rds-diag report -i my-prod-db -t 24h -o my-prod-db_report.txt --profile lt-prd
```

**Technical Report Includes:**
- Instance configuration details
- CloudWatch metrics (CPU, memory, connections, IOPS, storage)
- Performance Insights SQL queries with enhanced metrics:
  - Query ID and full SQL text
  - Engine type
  - Total/average execution time
  - Execution count and executions per second
  - CPU time and percentage
  - Lock time and percentage
  - Rows examined vs. rows returned (efficiency ratio)
  - Read/write I/O bytes
- Detailed SQL recommendations by severity
- Threshold violations
- Metric trends

#### Management Report (Executive Summary)

```bash
# Generate management report
rds-diag report -i my-prod-db --report-type management --profile lt-prd

# Generate management report for 7 days
rds-diag report -i my-prod-db -t 7d --report-type management --profile lt-prd
```

**Management Report Includes:**
- High-level status summary
- Critical issues requiring attention
- Top 3 problematic SQL queries
- Key recommendations prioritized by impact
- Resource utilization summary

#### JSON Format (For Automation)

```bash
# Generate JSON report for automation/integration
rds-diag report -i my-prod-db --format json -o report.json --profile lt-prd

# Generate management report in JSON
rds-diag report -i my-prod-db --report-type management -f json -o summary.json --profile lt-prd
```

**JSON Output Includes All Enhanced Fields:**
```json
{
  "instance_info": { ... },
  "metrics": { ... },
  "performance_insights_queries": [
    {
      "query_id": "sql-abc123",
      "query_text": "SELECT * FROM users WHERE email LIKE ?",
      "engine_type": "mysql",
      "total_execution_time": 5000.0,
      "average_execution_time": 50.0,
      "execution_count": 100,
      "executions_per_second": 0.5,
      "cpu_time": 4200.0,
      "lock_time": 300.0,
      "rows_examined": 100000,
      "rows_returned": 50,
      "read_io_bytes": 2048000,
      "write_io_bytes": 0
    }
  ],
  "recommendations": [ ... ]
}
```

## Understanding SQL Recommendations

### Index Optimization Opportunities

**Triggered when:** Rows examined >> rows returned (efficiency < 10%)

**Example:**
```
[INDEX] Query sql-abc123: Query examines 100,000 rows but returns only 50 rows 
(efficiency: 0.1%). Consider adding indexes to improve query selectivity. 
Review WHERE clause conditions and JOIN predicates.
```

**Action:** Add indexes on columns used in WHERE clauses and JOIN conditions.

### Lock Contention Issues

**Triggered when:** Lock time > 30% of total execution time

**Example:**
```
[LOCK] Query sql-xyz789: Query spends 35.2% of execution time waiting for locks 
(35.2ms of 100ms total). Consider: 1) Reviewing transaction isolation levels, 
2) Reducing transaction scope, 3) Optimizing query to reduce lock duration.
```

**Action:** Review transaction isolation levels, reduce transaction scope, or optimize query.

### Caching Candidates

**Triggered when:** High execution frequency + fast execution time

**Example:**
```
[CACHE] Query sql-config: Query executes very frequently (15.2 calls/sec) with 
fast execution time (5ms average). Consider: 1) Application-level caching 
(Redis, Memcached), 2) Query result caching, 3) Materialized views.
```

**Action:** Implement application-level caching or query result caching.

### CPU-Intensive Queries

**Triggered when:** CPU time > 80% of total execution time

**Example:**
```
[CPU] Query sql-def456: Query is CPU-intensive, using 87.3% of execution time 
on CPU (4500ms of 5000ms total). Consider: 1) Query optimization, 2) Adding 
indexes, 3) Moving complex calculations to application layer.
```

**Action:** Optimize query complexity, add indexes, or move calculations to application.

## Practical Examples

### Example 1: Investigating High CPU Usage

```bash
# Step 1: Run diagnostics to identify the issue
rds-diag diagnose -i my-prod-db -t 24h --profile lt-prd

# Step 2: Generate detailed technical report
rds-diag report -i my-prod-db -t 24h -o cpu-investigation.txt --profile lt-prd

# Step 3: Review SQL recommendations in the report
# Look for [CPU] and [INDEX] recommendations
```

### Example 2: Weekly Performance Review

```bash
# Generate management report for weekly review
rds-diag report -i my-prod-db -t 7d --report-type management -o weekly-review.txt --profile lt-prd

# Generate JSON for tracking trends
rds-diag report -i my-prod-db -t 7d -f json -o weekly-metrics.json --profile lt-prd
```

### Example 3: Pre-Production Validation

```bash
# Check staging database before promoting to production
rds-diag diagnose -i my-staging-db -t 1h --profile lt-stg

# Generate technical report to review query performance
rds-diag report -i my-staging-db -t 1h --profile lt-stg
```

### Example 4: Automated Monitoring

```bash
# Run diagnostics and save JSON for monitoring system
rds-diag report -i my-prod-db -t 1h -f json -o /var/log/rds-metrics/$(date +%Y%m%d-%H%M%S).json --profile lt-prd

# Parse JSON to extract critical issues
cat report.json | jq '.recommendations[] | select(.severity == "critical")'
```

## Batch Scripts (Windows)

For convenience, use the provided batch scripts:

```batch
REM List all instances
rds-list.bat

REM Quick diagnostic check
rds-diagnose.bat my-prod-db

REM Generate detailed report
rds-report.bat my-prod-db

REM Advanced diagnostics with 24h time range
rds-diagnose-advanced.bat my-prod-db 24h
```

## Interpreting Enhanced Metrics

### Efficiency Ratio
- **100%**: Perfect - every row examined is returned
- **10-50%**: Good - reasonable selectivity
- **1-10%**: Poor - consider adding indexes
- **<1%**: Critical - significant optimization needed

### Lock Time Percentage
- **<10%**: Normal - minimal lock contention
- **10-30%**: Moderate - monitor for trends
- **30-50%**: High - review transaction patterns
- **>50%**: Critical - immediate action needed

### CPU Time Percentage
- **<50%**: Normal - balanced workload
- **50-80%**: Moderate - query may benefit from optimization
- **>80%**: High - CPU-intensive query, optimize or scale

### Executions Per Second
- **<0.1**: Low frequency
- **0.1-1.0**: Moderate frequency
- **1.0-10**: High frequency - consider caching
- **>10**: Very high frequency - caching strongly recommended

## Troubleshooting

### "Performance Insights not enabled"

**Solution:** Enable Performance Insights on your RDS instance:
1. Go to AWS Console → RDS → Your Instance
2. Click "Modify"
3. Enable "Performance Insights"
4. Apply changes (may require restart)

### "Missing required permissions"

**Solution:** Run permission check and add missing permissions:
```bash
rds-diag check-permissions --profile your-profile
```

### "No SQL queries found"

**Possible causes:**
1. Performance Insights recently enabled (wait 5-10 minutes for data)
2. No queries executed during time range
3. Instance has very low activity

**Solution:** Try a longer time range:
```bash
rds-diag report -i my-db -t 24h --profile your-profile
```

### "Enhanced metrics not available"

**Possible causes:**
1. Engine doesn't support specific metrics (e.g., PostgreSQL doesn't have lock_time)
2. Metrics not collected by Performance Insights for this engine version

**Solution:** This is normal - the tool will show available metrics and mark unavailable ones as "N/A"

## Best Practices

1. **Regular Monitoring**: Run diagnostics daily or weekly to catch issues early
2. **Baseline Metrics**: Generate reports during normal operation to establish baselines
3. **Time Range Selection**: 
   - Use 1h for real-time troubleshooting
   - Use 24h for daily reviews
   - Use 7d for trend analysis
4. **Act on Recommendations**: Prioritize CRITICAL recommendations first
5. **Track Changes**: Save reports before and after optimizations to measure impact
6. **Automate**: Integrate JSON output into monitoring dashboards

## Next Steps

- Review the generated reports and identify top issues
- Implement recommended optimizations (indexes, caching, query optimization)
- Monitor metrics after changes to validate improvements
- Set up automated reporting for continuous monitoring

## Support

For issues or questions:
- Check the main README.md for general documentation
- Review EXAMPLES.md for more usage examples
- Check REPORT-GUIDE.md for report interpretation details
