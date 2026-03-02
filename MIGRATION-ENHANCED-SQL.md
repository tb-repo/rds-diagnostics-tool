# Migration Guide: Enhanced SQL Metadata Collection

This guide helps you upgrade to the enhanced SQL metadata collection feature and understand what's changed.

## What's New

The RDS Diagnostics Tool now collects detailed SQL performance metrics when Performance Insights is enabled, providing deeper insights into query performance and automatic optimization recommendations.

### New Features

1. **Enhanced SQL Metrics**
   - Execution rate (queries per second)
   - CPU time per query
   - Lock time and contention analysis
   - Row efficiency (examined vs. returned)
   - I/O metrics (read/write bytes)

2. **Smart Recommendations**
   - INDEX: Identifies queries needing indexes
   - LOCK: Detects lock contention issues
   - CACHE: Suggests caching opportunities
   - CPU: Flags CPU-intensive queries

3. **Engine-Specific Collection**
   - Automatic detection of RDS engine type
   - Engine-specific metric collection (MySQL, PostgreSQL, Oracle, SQL Server, Aurora)
   - Optimized for each database engine

4. **Configurable Collection**
   - Control which metrics to collect
   - Set maximum number of queries to analyze
   - Enable/disable enhanced metrics

## Backward Compatibility

✅ **Fully Backward Compatible** - No breaking changes!

- Existing commands work exactly as before
- Existing configuration files remain valid
- Reports maintain the same structure with additional sections
- JSON output includes new fields (all optional)
- Tool works without Performance Insights (graceful degradation)

## Migration Steps

### Step 1: Update IAM Permissions (Recommended)

To use enhanced SQL metrics, add the `pi:GetResourceMetrics` permission:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:GetMetricData",
        "pi:DescribeDimensionKeys",
        "pi:GetResourceMetrics"
      ],
      "Resource": "*"
    }
  ]
}
```

**Note:** If you don't add this permission, the tool will continue to work with basic SQL metrics only.

### Step 2: Update Configuration (Optional)

Add Performance Insights configuration to your `config.yaml`:

```yaml
# Add this section to your existing config.yaml
performance_insights:
  enabled: true
  max_queries: 25
  collect_enhanced_metrics: true
  fallback_on_error: true
  collect_cpu_metrics: true
  collect_lock_metrics: true
  collect_io_metrics: true
  collect_row_metrics: true
```

**Default Behavior:** If you don't add this section, the tool uses these defaults automatically.

### Step 3: Enable Performance Insights on RDS (If Not Already Enabled)

Enhanced metrics require Performance Insights to be enabled on your RDS instance:

1. Go to AWS RDS Console
2. Select your instance
3. Click "Modify"
4. Scroll to "Performance Insights"
5. Enable Performance Insights
6. Choose retention period (7 days free, longer periods have costs)
7. Apply changes

**Cost:** Performance Insights is free for 7 days of retention. Longer retention periods incur charges.

### Step 4: Test the Enhanced Features

```bash
# Generate a report to see enhanced SQL metrics
rds-diag report --instance your-instance --output test-report.txt

# Check for SQL recommendations in the output
grep -A 5 "Recommendations:" test-report.txt
```

## What Changed

### SQLQuery Data Model

New optional fields added to SQLQuery (all backward compatible):

| Field | Type | Description |
|-------|------|-------------|
| `engine_type` | string | Database engine (mysql, postgres, etc.) |
| `executions_per_second` | float | Query execution rate |
| `cpu_time` | float | CPU time in milliseconds |
| `lock_time` | float | Lock time in milliseconds |
| `rows_examined` | int | Number of rows scanned |
| `rows_returned` | int | Number of rows returned |
| `read_io_bytes` | int | Bytes read from storage |
| `write_io_bytes` | int | Bytes written to storage |

**Backward Compatibility:** All new fields are optional (default: None). Existing code continues to work.

### Report Format Changes

#### Technical Reports

**Before:**
```
SQL Query Performance
=====================

Query 1 (ID: 0x1A2B3C4D5E6F7890)
-----------------------------------
SQL: SELECT * FROM orders WHERE customer_id = ?
Total Execution Time: 45,230.50 ms
Average Execution Time: 125.30 ms
Execution Count: 361
```

**After (with enhanced metrics):**
```
SQL Query Performance
=====================

Query 1 (ID: 0x1A2B3C4D5E6F7890)
-----------------------------------
SQL: SELECT * FROM orders WHERE customer_id = ?
Total Execution Time: 45,230.50 ms
Average Execution Time: 125.30 ms
Execution Count: 361

Execution Metrics:
  Executions/sec: 0.50 calls/sec
  Total Time: 45,230.50 ms

Resource Metrics:
  CPU Time: 38,450.20 ms (85.0%)
  Lock Time: 1,250.30 ms (2.8%)

Row Metrics:
  Rows Examined: 1,250,000
  Rows Returned: 1,250
  Efficiency Ratio: 0.10% ⚠️ LOW EFFICIENCY

I/O Metrics:
  Read I/O: 512.50 MB
  Write I/O: 0.00 MB

Recommendations:
  [CRITICAL] INDEX: Query examines 1,250,000 rows but returns only 1,250 (0.10% efficiency).
             Consider adding an index on customer_id and status columns.
             Potential impact: 45,230.50 ms total execution time
```

#### Management Reports

New "SQL Performance Summary" section added with:
- Query count and issue summary
- Top 3 problematic queries
- Key recommendations by category

#### JSON Output

New fields added to JSON output (all optional):

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
  ],
  "recommendations": [
    {
      "severity": "CRITICAL",
      "category": "SQL",
      "message": "INDEX: Query 0x1A2B3C4D examines 1,250,000 rows but returns only 1,250..."
    }
  ]
}
```

## Configuration Changes

### New Configuration Section

```yaml
performance_insights:
  enabled: true                    # Enable/disable PI collection
  max_queries: 25                  # Number of queries to analyze (1-100)
  collect_enhanced_metrics: true   # Collect detailed metrics
  fallback_on_error: true          # Continue with basic metrics on error
  collect_cpu_metrics: true        # Include CPU time
  collect_lock_metrics: true       # Include lock time
  collect_io_metrics: true         # Include I/O metrics
  collect_row_metrics: true        # Include row statistics
```

### Existing Configuration

All existing configuration options remain unchanged and work as before.

## Troubleshooting Migration Issues

### Issue: "Permission denied: pi:GetResourceMetrics"

**Cause:** IAM user/role doesn't have the new permission.

**Solution:**
```bash
# Update IAM policy to include pi:GetResourceMetrics
# See Step 1 above for the complete policy
```

### Issue: "Performance Insights not enabled"

**Cause:** Performance Insights is not enabled on the RDS instance.

**Solution:**
```bash
# Enable Performance Insights on the RDS instance
# See Step 3 above for instructions
```

**Note:** This is informational. The tool will continue with basic metrics.

### Issue: Enhanced metrics showing as "N/A"

**Cause:** One of the following:
- Performance Insights not enabled
- Missing `pi:GetResourceMetrics` permission
- Engine doesn't support specific metrics
- No data available for the time range

**Solution:**
1. Verify Performance Insights is enabled
2. Check IAM permissions
3. Ensure sufficient data collection time (wait 5-10 minutes after enabling PI)
4. Some metrics are engine-specific (e.g., lock_time not available on PostgreSQL)

### Issue: Reports look different

**Cause:** Enhanced metrics add new sections to reports.

**Solution:** This is expected behavior. The new sections provide additional insights. If you prefer the old format, you can:
1. Disable enhanced metrics in config: `collect_enhanced_metrics: false`
2. Or remove `pi:GetResourceMetrics` permission (tool will fall back to basic metrics)

### Issue: JSON parsing errors in existing scripts

**Cause:** New optional fields in JSON output.

**Solution:** Update your JSON parsing scripts to handle optional fields:

```python
# Before
cpu_time = query['cpu_time']  # May fail if field is None

# After
cpu_time = query.get('cpu_time')  # Returns None if not present
if cpu_time is not None:
    # Process CPU time
```

## Rollback Instructions

If you need to revert to basic SQL metrics only:

### Option 1: Disable in Configuration

```yaml
performance_insights:
  collect_enhanced_metrics: false
```

### Option 2: Remove IAM Permission

Remove `pi:GetResourceMetrics` from your IAM policy. The tool will automatically fall back to basic metrics.

### Option 3: Disable Performance Insights Collection

```yaml
performance_insights:
  enabled: false
```

**Note:** This disables all Performance Insights collection, including basic SQL queries.

## Performance Impact

### Tool Performance

- **API Calls:** Increases by ~30% (one additional call per query for enhanced metrics)
- **Execution Time:** Increases by ~20% (additional API calls and processing)
- **Memory Usage:** Minimal increase (<5%)

### RDS Instance Performance

- **No impact:** The tool only reads data from Performance Insights
- **No modifications:** Tool does NOT modify any AWS resources
- **Read-only:** All operations are read-only API calls

### Cost Impact

- **Performance Insights:** Free for 7 days retention, charges for longer retention
- **API Calls:** Minimal increase in AWS API costs (typically <$0.01/month)

## Best Practices

1. **Start with defaults:** Use default configuration initially, customize later if needed
2. **Monitor gradually:** Enable on dev/test environments first, then production
3. **Review recommendations:** Check SQL recommendations regularly for optimization opportunities
4. **Update IAM policies:** Ensure all users have the new `pi:GetResourceMetrics` permission
5. **Enable PI strategically:** Enable Performance Insights on instances where SQL analysis is valuable

## Getting Help

- **Documentation:** See [ENHANCED-SQL-GUIDE.md](ENHANCED-SQL-GUIDE.md) for detailed feature guide
- **Examples:** See [EXAMPLES.md](EXAMPLES.md) for usage examples
- **Quick Reference:** See [QUICK-REFERENCE.md](QUICK-REFERENCE.md) for command cheat sheet
- **Issues:** Report issues or ask questions via your support channel

## Summary

✅ **Fully backward compatible** - existing functionality unchanged  
✅ **Opt-in enhanced features** - works without Performance Insights  
✅ **No breaking changes** - all existing commands and configs work  
✅ **Graceful degradation** - falls back to basic metrics if enhanced unavailable  
✅ **Read-only operations** - no modifications to AWS resources  

The enhanced SQL metadata collection feature adds powerful new capabilities while maintaining full backward compatibility. You can adopt it gradually at your own pace.
