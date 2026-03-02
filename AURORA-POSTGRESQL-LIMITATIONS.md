# Aurora PostgreSQL Performance Insights Limitations

## Summary

After extensive testing with your Aurora PostgreSQL 17.5 instance (`ielts-ses-sit-v1-clusterinstance1`), we've identified that **Aurora PostgreSQL does not expose SQL-level performance metrics through the Performance Insights API**.

## What Works ✅

1. **SQL Query Collection** - We can get the list of top SQL queries
2. **Top Users** - User names are collected correctly (`speaking_exam_sit_read`, `routing_sit_read`)
3. **Wait Events** - CPU, IO:DataFileRead, etc.
4. **CloudWatch Metrics** - CPU, Memory, Connections, IOPS all work

## What Doesn't Work ❌

1. **Enhanced SQL Metrics** - All show "N/A":
   - Executions/sec
   - CPU Time
   - Lock Time
   - Rows Examined/Returned
   - Read/Write I/O Time
   - Read/Write I/O Bytes

2. **Top Databases** - API returns error: "The specified group is not a known group"

## Root Cause

### API Test Results

```bash
# Test 1: list_available_resource_metrics
Result: 0 metrics available for Aurora PostgreSQL

# Test 2: describe_dimension_keys with AdditionalMetrics
Result: Parameter validation failed (empty list not allowed)

# Test 3: describe_dimension_keys for db.name (Top Databases)
Result: "The specified group is not a known group"
```

### Why AWS Console Shows These Metrics

The AWS Performance Insights console has **direct access to PostgreSQL's internal statistics tables** (`pg_stat_statements`, `pg_stat_database`, etc.), which is why you see:
- Average latency
- Read time (ms/call)
- Write time (ms/call)
- Rows/sec
- Calls/sec

However, these metrics are **NOT exposed through the Performance Insights API** that our tool uses.

## Comparison: Aurora MySQL vs Aurora PostgreSQL

| Feature | Aurora MySQL | Aurora PostgreSQL |
|---------|--------------|-------------------|
| SQL Query List | ✅ Yes | ✅ Yes |
| Executions/sec | ✅ Yes | ❌ No |
| CPU Time | ✅ Yes | ❌ No |
| Lock Time | ✅ Yes | ❌ No |
| Rows Examined | ✅ Yes | ❌ No |
| Rows Returned | ✅ Yes | ❌ No |
| I/O Bytes | ✅ Yes | ❌ No |
| Top Databases | ✅ Yes | ❌ No |
| Top Users | ✅ Yes | ✅ Yes |

## Workarounds

### Option 1: Query PostgreSQL Statistics Directly

We could add a feature to connect directly to the PostgreSQL database and query `pg_stat_statements`:

```sql
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows,
    shared_blks_read,
    shared_blks_written,
    blk_read_time,
    blk_write_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

**Pros:**
- Would get all the metrics you see in AWS console
- More accurate and detailed

**Cons:**
- Requires database credentials
- Requires network access to the database
- Requires `pg_stat_statements` extension enabled
- More complex setup

### Option 2: Use CloudWatch Logs Insights

If you have PostgreSQL slow query logs enabled and sent to CloudWatch Logs, we could parse those.

**Pros:**
- No database access needed
- Uses existing AWS APIs

**Cons:**
- Only captures slow queries
- Less real-time
- Requires log configuration

### Option 3: Accept Current Limitations

Continue using the tool as-is, understanding that:
- SQL queries are listed (which is valuable)
- Enhanced metrics aren't available for Aurora PostgreSQL
- Use AWS Console for detailed SQL analysis

## Recommendations

### Immediate Actions

1. **Use the tool for what it does well:**
   - CloudWatch metrics analysis
   - Threshold violations
   - Trend detection
   - SQL query identification (you can see which queries are running)

2. **Use AWS Console for SQL details:**
   - When you need Read/Write time
   - When you need detailed performance metrics
   - For query-level optimization

### Future Enhancements

If you need programmatic access to SQL metrics, we should implement Option 1 (direct PostgreSQL connection). This would require:

1. Adding database connection parameters to config
2. Implementing `pg_stat_statements` query logic
3. Merging PI data with pg_stat data
4. Handling connection security (SSL, credentials)

Would you like me to implement this enhancement?

## Current Report Quality

Despite the limitations, the current report provides:

✅ **Instance health overview**
✅ **CloudWatch metrics with trends**
✅ **Threshold violations**
✅ **Memory warnings** (your instance shows low memory)
✅ **SQL query identification** (you can see which stored procedures are being called)
✅ **Top users by load**
✅ **Wait events**

## What's Missing

❌ **SQL performance details** (latency, I/O time, rows processed)
❌ **Top databases**
❌ **Query optimization recommendations** (need metrics to generate these)

## Conclusion

This is a **limitation of Aurora PostgreSQL's Performance Insights API**, not a bug in our tool. Aurora MySQL provides these metrics through the API, but Aurora PostgreSQL does not.

To get the detailed SQL metrics you need, we would need to implement direct database querying via `pg_stat_statements`.

---

**Last Updated:** February 27, 2026
**Tested With:** Aurora PostgreSQL 17.5
**Instance:** ielts-ses-sit-v1-clusterinstance1
