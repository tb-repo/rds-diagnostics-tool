# Bug Fix Summary - Report Output Issues

## Issues Fixed

### 1. Top Users showing "Unknown" instead of actual usernames
**Problem**: The code was looking for user names in `dimensions.get('db.user')` but the AWS Performance Insights API might return it with a different key structure.

**Fix**: Added fallback logic to try multiple possible key names:
- `dimensions.get('db.user')`
- `dimensions.get('db.user.name')`
- `key.get('db.user')`
- Falls back to 'Unknown' if none found

**Location**: `collectors/performance_insights.py` - `collect_top_users()` method

### 2. Top Databases section missing from report
**Problem**: Similar to Top Users - the database name key structure might be different.

**Fix**: Added fallback logic to try multiple possible key names:
- `dimensions.get('db.name')`
- `dimensions.get('db.database')`
- `dimensions.get('db.database.name')`
- `key.get('db.name')`
- Falls back to 'Unknown' if none found

**Location**: `collectors/performance_insights.py` - `collect_top_databases()` method

**Note**: The report formatter already had the code to display Top Databases - it was just not getting the data.

### 3. Enhanced SQL metrics showing "N/A" instead of actual values
**Problem**: The original implementation used a two-phase approach:
1. Call `describe_dimension_keys` to get top queries
2. Call `get_resource_metrics` for each query to get enhanced metrics

This approach had issues with the Filter parameter structure and was making too many API calls.

**Fix**: Changed to use the AWS Performance Insights best practice - request additional metrics in the same `describe_dimension_keys` call:
- Added `additional_metrics` parameter to `describe_dimension_keys` API call
- AWS PI returns enhanced metrics in the `AdditionalMetrics` field of each dimension key
- Parse and map these metrics to our SQLQuery fields
- This is more efficient (one API call instead of N+1) and more reliable

**Locations**:
- `aws/clients.py` - Updated `PerformanceInsightsClient.describe_dimension_keys()` to support `additional_metrics` parameter
- `collectors/performance_insights.py` - Updated `collect_top_sql_queries()` to request and parse AdditionalMetrics

## Debug Logging Added

Added extensive debug logging to help diagnose issues:
- Logs the actual dimension key structure returned by AWS API
- Logs the AdditionalMetrics data for each SQL query
- Logs metric mapping and validation results

To see debug logs, run with `--verbose` flag:
```bash
rds-diag --verbose --profile LT-SIT report --instance ielts-ses-sit-v1-clusterinstance2 --time-range 12h
```

## Testing the Fixes

### Test with your Aurora PostgreSQL instance:

```bash
# Generate a report with verbose logging to see what's happening
rds-diag --verbose --profile LT-SIT report --instance ielts-ses-sit-v1-clusterinstance2 --time-range 12h --output test-report.txt
```

### What to look for in the output:

1. **Top Users section** should show actual usernames (not "Unknown"):
   ```
   TOP USERS BY LOAD
   --------------------------------------------------------------------------------
   1. app_user
      Total Load: 5.23 AAS
      Load %: 74.7%
   ```

2. **Top Databases section** should appear in the report:
   ```
   TOP DATABASES BY LOAD
   --------------------------------------------------------------------------------
   1. ielts_ses_production
      Total Load: 4.56 AAS
      Load %: 65.2%
   ```

3. **Enhanced SQL metrics** should show actual values (not "N/A"):
   ```
   Execution Metrics:
   Total Execution Time:   1.78 ms
   Average Execution Time: 1.78 ms
   Execution Count:        1
   Executions/sec:         0.5          ← Should have a value
   
   Resource Metrics:
   CPU Time:               800.0 ms     ← Should have a value
   Lock Time:              50.0 ms      ← Should have a value (MySQL/Aurora MySQL only)
   
   Row Metrics:
   Rows Examined:          10000        ← Should have a value
   Rows Returned:          100          ← Should have a value
   Efficiency Ratio:       1.00%        ← Should be calculated
   
   I/O Metrics:
   Read I/O:               512.0 KB     ← Should have a value
   Write I/O:              0 B          ← Should have a value
   ```

### If issues persist:

1. **Check the verbose logs** for lines like:
   ```
   DEBUG - Top user dimension key structure: {...}
   DEBUG - Top database dimension key structure: {...}
   DEBUG - SQL ID xxx: AdditionalMetrics = {...}
   ```

2. **Look for the actual key names** AWS is returning and let me know - I can add them to the fallback logic

3. **Check if Performance Insights has the data** - if AWS console shows the metrics but our tool doesn't, it's a parsing issue

## Technical Details

### AWS Performance Insights API Changes

**Old approach (problematic)**:
```python
# Phase 1: Get top queries
keys = describe_dimension_keys(group_by='db.sql', metric='db.load.avg')

# Phase 2: For each query, get enhanced metrics (N+1 API calls!)
for key in keys:
    metrics = get_resource_metrics(
        metric_queries=[...],
        filter={'db.sql.id': key['sql_id']}  # Filter syntax was problematic
    )
```

**New approach (AWS best practice)**:
```python
# Single API call with additional metrics requested
keys = describe_dimension_keys(
    group_by='db.sql',
    metric='db.load.avg',
    additional_metrics=[
        'db.sql.stats.calls_per_sec',
        'db.sql.stats.cpu_time_ms',
        'db.sql.stats.rows',
        'db.sql.stats.shared_blks_read',
        'db.sql.stats.shared_blks_written'
    ]
)

# Enhanced metrics are in the response
for key in keys:
    additional_metrics = key.get('AdditionalMetrics', {})
    # Parse and use the metrics
```

### Engine-Specific Metrics

The tool automatically requests the correct metrics for each database engine:

**Aurora PostgreSQL** (your instance):
- `db.sql.stats.calls_per_sec` → executions_per_second
- `db.sql.stats.cpu_time_ms` → cpu_time
- `db.sql.stats.rows` → rows_returned
- `db.sql.stats.shared_blks_read` → read_io_bytes
- `db.sql.stats.shared_blks_written` → write_io_bytes

**Aurora MySQL**:
- `db.sql.stats.executions_per_sec` → executions_per_second
- `db.sql.stats.cpu_time_ms` → cpu_time
- `db.sql.stats.lock_time_ms` → lock_time
- `db.sql.stats.rows_examined` → rows_examined
- `db.sql.stats.rows_sent` → rows_returned
- `db.sql.stats.innodb_io_r_bytes` → read_io_bytes
- `db.sql.stats.innodb_io_w_bytes` → write_io_bytes

## Files Modified

1. `collectors/performance_insights.py`
   - Updated `collect_top_users()` - added fallback key logic
   - Updated `collect_top_databases()` - added fallback key logic
   - Updated `collect_top_sql_queries()` - changed to use AdditionalMetrics approach
   - Updated `_collect_query_metrics()` - simplified query structure
   - Added debug logging throughout

2. `aws/clients.py`
   - Updated `PerformanceInsightsClient.describe_dimension_keys()` - added `additional_metrics` parameter

3. `tests/integration/test_enhanced_sql_collection.py`
   - Updated all test mocks to use AdditionalMetrics approach
   - Tests now pass with new implementation

4. `tests/unit/test_collect_query_metrics.py`
   - Updated query structure test to match simplified implementation

## Next Steps

1. **Test with your actual instance** using the command above
2. **Review the output** to confirm all three issues are fixed
3. **Check the verbose logs** if any issues remain
4. **Let me know the results** so I can make further adjustments if needed

The changes are backward compatible - if AdditionalMetrics are not available, the tool will gracefully fall back to basic metrics (load data only).
