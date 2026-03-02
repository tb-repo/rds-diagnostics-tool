# Report Output Cleanup - Summary

## Problem
The technical report was showing too many "N/A" values for per-query execution metrics (CPU Time, Lock Time, Rows, I/O Time) which added clutter and no value to the report. These metrics are not available from the Performance Insights API for Aurora PostgreSQL.

## Solution
Modified `reporting/formatters.py` to implement conditional section display:

### Changes Made

1. **Conditional Section Display**
   - Only show "Resource Metrics" section if `cpu_time` or `lock_time` is available
   - Only show "Row Metrics" section if `rows_examined`, `rows_returned`, or `rows_per_second` is available
   - Only show "I/O Metrics" section if any I/O metric is available
   - Removed all individual "N/A" lines

2. **Explanatory Note**
   - When NO per-query execution metrics are available, display a helpful note:
     ```
     Note: Per-query execution metrics (CPU time, lock time, rows, I/O time)
           are not available from Performance Insights API for Aurora PostgreSQL.
           See 'OS-LEVEL PERFORMANCE METRICS' section below for system-wide
           CPU, memory, and disk I/O performance data.
     ```
   - This directs users to the OS-Level metrics section where they can find system-wide performance data

3. **Cleaner Execution Metrics**
   - Removed the redundant note "Note: Execution count not available from PI API for PostgreSQL"
   - Removed "Executions/sec: N/A (not available from PI API)" line when not available
   - Only show `Executions/sec` when the value is actually available

## Benefits

1. **Reduced Clutter**: No more N/A values filling up the report
2. **Better User Experience**: Users immediately see what data IS available
3. **Clear Guidance**: Explanatory note directs users to OS-Level metrics for system-wide performance data
4. **Accurate Representation**: Report now accurately reflects what the PI API provides

## Testing

Created test scripts to verify the formatting logic:

### Test Case 1: No Per-Query Metrics Available
- Shows only Execution Metrics section
- Displays explanatory note pointing to OS-Level metrics
- No N/A clutter

### Test Case 2: Some Metrics Available
- Shows only sections with actual data (Resource Metrics, Row Metrics)
- Hides sections with no data (I/O Metrics)
- No explanatory note (since some data is available)
- Calculates efficiency ratio when row data is available

## Files Modified

- `reporting/formatters.py` (lines 228-330): Updated SQL query formatting logic

## Files Created

- `test_report_formatting.py`: Test script for no metrics scenario
- `test_report_with_metrics.py`: Test script for partial metrics scenario
- `REPORT-CLEANUP-SUMMARY.md`: This summary document

## Related Documentation

- `AURORA-POSTGRESQL-LIMITATIONS.md`: Explains PI API limitations
- `ALTERNATIVE-OPTIONS.md`: Options for getting missing metrics
- `PI-METRICS-REFERENCE.md`: Complete PI API metrics reference

## Next Steps

1. Test with longer time ranges (24h) when database has actual activity
2. Consider implementing direct PostgreSQL connection to query `pg_stat_statements` for per-query metrics (if user requirements change)
3. Monitor user feedback on the new report format
