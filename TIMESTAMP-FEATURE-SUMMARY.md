# Specific Start/End Time Feature - Summary

## New Feature

Added support for specifying exact start and end times for diagnostics and reports, in addition to the existing duration-based time ranges (1h, 24h, 7d).

## Usage

### New CLI Options

Both `diagnose` and `report` commands now support:

- `--start-time`: Start timestamp (requires --end-time)
- `--end-time`: End timestamp (requires --start-time)

These options are mutually exclusive with `--time-range`.

### Supported Timestamp Formats

1. **ISO 8601**: `"2026-03-02T10:00:00"` or `"2026-03-02T10:00:00Z"`
2. **Date and time with space**: `"2026-03-02 10:00:00"` or `"2026-03-02 10:00"`
3. **Date only**: `"2026-03-02"` (assumes 00:00:00)

All timestamps are interpreted as UTC.

### Validation Rules

- Both `--start-time` and `--end-time` must be specified together
- End time must be after start time
- Maximum time range: 30 days
- Cannot use `--time-range` with `--start-time`/`--end-time`

## Examples

### Diagnose Command

```bash
# Analyze specific 4-hour window
rds-diag --profile LT-SIT diagnose --instance my-db \
  --start-time "2026-03-02 09:00" \
  --end-time "2026-03-02 13:00"

# Analyze business hours (9 AM - 5 PM)
rds-diag --profile LT-PRD diagnose --instance prod-db \
  --start-time "2026-03-02T09:00:00" \
  --end-time "2026-03-02T17:00:00"

# Analyze full day
rds-diag diagnose --instance my-db \
  --start-time "2026-03-01" \
  --end-time "2026-03-02"

# Analyze weekend
rds-diag diagnose --instance my-db \
  --start-time "2026-02-28" \
  --end-time "2026-03-02"
```

### Report Command

```bash
# Generate report for specific time window
rds-diag --profile LT-SIT report --instance my-db \
  --start-time "2026-03-02 10:00" \
  --end-time "2026-03-02 14:00" \
  --output morning-report.txt

# Generate report for business hours
rds-diag --profile LT-PRD report --instance prod-db \
  --start-time "2026-03-02 09:00" \
  --end-time "2026-03-02 17:00" \
  --report-type technical \
  --output business-hours.txt

# Generate JSON report for specific date
rds-diag report --instance my-db \
  --start-time "2026-03-01" \
  --end-time "2026-03-02" \
  --format json \
  --output daily-report.json

# Generate management report for last week
rds-diag --profile LT-PRD report --instance prod-db \
  --start-time "2026-02-24" \
  --end-time "2026-03-02" \
  --report-type management \
  --output weekly-summary.txt
```

## Use Cases

### 1. Incident Investigation
Analyze performance during a specific incident window:
```bash
rds-diag diagnose --instance prod-db \
  --start-time "2026-03-02 14:30" \
  --end-time "2026-03-02 15:30"
```

### 2. Peak Hours Analysis
Compare performance during peak vs off-peak hours:
```bash
# Peak hours (9 AM - 5 PM)
rds-diag report --instance my-db \
  --start-time "2026-03-02 09:00" \
  --end-time "2026-03-02 17:00" \
  --output peak-hours.txt

# Off-peak hours (6 PM - 2 AM)
rds-diag report --instance my-db \
  --start-time "2026-03-02 18:00" \
  --end-time "2026-03-03 02:00" \
  --output off-peak-hours.txt
```

### 3. Before/After Deployment Comparison
```bash
# Before deployment
rds-diag report --instance prod-db \
  --start-time "2026-03-02 08:00" \
  --end-time "2026-03-02 10:00" \
  --output before-deployment.txt

# After deployment
rds-diag report --instance prod-db \
  --start-time "2026-03-02 11:00" \
  --end-time "2026-03-02 13:00" \
  --output after-deployment.txt
```

### 4. Weekly Performance Review
```bash
# Generate report for entire week
rds-diag --profile LT-PRD report --instance prod-db \
  --start-time "2026-02-24" \
  --end-time "2026-03-02" \
  --report-type management \
  --output weekly-review.txt
```

### 5. Historical Analysis
```bash
# Analyze performance from 2 weeks ago
rds-diag report --instance my-db \
  --start-time "2026-02-16 00:00" \
  --end-time "2026-02-17 00:00" \
  --output historical-analysis.txt
```

## Error Handling

### Missing end-time
```bash
$ rds-diag diagnose --instance my-db --start-time "2026-03-02 10:00"
ERROR: Both --start-time and --end-time must be specified together.
```

### Conflicting options
```bash
$ rds-diag diagnose --instance my-db --time-range 1h --start-time "2026-03-02 10:00" --end-time "2026-03-02 11:00"
ERROR: Cannot use both --time-range and --start-time/--end-time options together.
Use either --time-range OR --start-time with --end-time.
```

### Invalid time order
```bash
$ rds-diag diagnose --instance my-db --start-time "2026-03-02 14:00" --end-time "2026-03-02 10:00"
ERROR: End time (2026-03-02 10:00) must be after start time (2026-03-02 14:00)
```

### Time range too large
```bash
$ rds-diag diagnose --instance my-db --start-time "2026-01-01" --end-time "2026-03-01"
ERROR: Time range too large: 59 days. Maximum is 30 days.
```

### Invalid format
```bash
$ rds-diag diagnose --instance my-db --start-time "March 2, 2026" --end-time "March 3, 2026"
ERROR: Invalid timestamp format: ...
Supported formats: '2026-03-02T10:00:00', '2026-03-02 10:00', or '2026-03-02'
```

## Implementation Details

### Changes Made

1. **core/models.py** - Added `TimeRange.from_timestamps()` method
   - Parses ISO 8601, date+time, and date-only formats
   - Validates time order and range limits
   - Uses python-dateutil for flexible parsing

2. **cli/main.py** - Updated `diagnose` and `report` commands
   - Added `--start-time` and `--end-time` options
   - Added validation for mutually exclusive options
   - Updated help text and examples
   - Defaults to `1h` if no time options specified

### Backward Compatibility

✅ Fully backward compatible - existing commands continue to work:
```bash
# These still work exactly as before
rds-diag diagnose --instance my-db
rds-diag diagnose --instance my-db --time-range 24h
rds-diag report --instance my-db --time-range 7d
```

## Testing

All timestamp formats tested and validated:
- ✅ ISO 8601 format
- ✅ Date and time with space
- ✅ Date only (full day)
- ✅ Short time format (HH:MM)
- ✅ Error handling (invalid order, too large, invalid format)

## Files Modified

1. `core/models.py` - Added `TimeRange.from_timestamps()` method
2. `cli/main.py` - Updated `diagnose` and `report` commands with new options

## Files Created

1. `test_timestamp_parsing.py` - Test script for timestamp parsing
2. `TIMESTAMP-FEATURE-SUMMARY.md` - This documentation

## Benefits

1. **Precise Analysis**: Analyze exact time windows for incident investigation
2. **Historical Analysis**: Review performance from specific dates in the past
3. **Comparison**: Compare performance across different time periods
4. **Flexibility**: Choose between duration-based (1h, 24h) or exact timestamps
5. **Business Hours**: Easily analyze performance during business hours vs off-hours

## Next Steps

Consider adding to EXAMPLES.md and updating batch scripts to support the new options.
