# Time Range Options - Quick Reference

## Two Ways to Specify Time Ranges

### Option 1: Duration-Based (Relative to Now)

Use `--time-range` / `-t` with duration string:

```bash
# Last hour (default)
rds-diag diagnose --instance my-db

# Last 24 hours
rds-diag diagnose --instance my-db --time-range 24h

# Last 7 days
rds-diag report --instance my-db -t 7d
```

**Supported formats:**
- `15m` - 15 minutes
- `1h` - 1 hour
- `24h` - 24 hours
- `7d` - 7 days
- `30d` - 30 days

### Option 2: Specific Start/End Times (Absolute)

Use `--start-time` and `--end-time` together:

```bash
# Specific 4-hour window
rds-diag diagnose --instance my-db \
  --start-time "2026-03-02 09:00" \
  --end-time "2026-03-02 13:00"

# Full day
rds-diag report --instance my-db \
  --start-time "2026-03-01" \
  --end-time "2026-03-02"
```

**Supported formats:**
- `"2026-03-02T10:00:00"` - ISO 8601
- `"2026-03-02 10:00:00"` - Date and time
- `"2026-03-02 10:00"` - Date and time (short)
- `"2026-03-02"` - Date only (00:00:00)

## Quick Examples

### Duration-Based (Relative)

```bash
# Last 15 minutes
rds-diag diagnose --instance my-db -t 15m

# Last hour
rds-diag diagnose --instance my-db -t 1h

# Last 24 hours
rds-diag report --instance my-db -t 24h -o daily.txt

# Last week
rds-diag report --instance my-db -t 7d -o weekly.txt
```

### Timestamp-Based (Absolute)

```bash
# Morning hours (9 AM - 12 PM)
rds-diag diagnose --instance my-db \
  --start-time "2026-03-02 09:00" \
  --end-time "2026-03-02 12:00"

# Business hours (9 AM - 5 PM)
rds-diag report --instance my-db \
  --start-time "2026-03-02T09:00:00" \
  --end-time "2026-03-02T17:00:00" \
  -o business-hours.txt

# Specific date (full day)
rds-diag report --instance my-db \
  --start-time "2026-03-01" \
  --end-time "2026-03-02" \
  -o march-1st.txt

# Last week (specific dates)
rds-diag report --instance my-db \
  --start-time "2026-02-24" \
  --end-time "2026-03-02" \
  -o last-week.txt
```

## When to Use Each Option

### Use Duration-Based (`--time-range`) When:
- ✅ You want recent data (last hour, last day, etc.)
- ✅ You're doing real-time monitoring
- ✅ You want a quick check of current performance
- ✅ You don't care about exact timestamps

### Use Timestamp-Based (`--start-time`/`--end-time`) When:
- ✅ Investigating a specific incident at a known time
- ✅ Comparing performance across specific time periods
- ✅ Analyzing historical data from the past
- ✅ Generating reports for specific business hours
- ✅ You need exact time boundaries

## Rules and Limitations

### Duration-Based
- ✅ Simple and quick
- ✅ Always relative to current time
- ✅ Supported: m (minutes), h (hours), d (days)
- ❌ Cannot specify exact historical times

### Timestamp-Based
- ✅ Precise control over time range
- ✅ Can analyze any historical period
- ✅ Flexible timestamp formats
- ⚠️ Both start and end must be specified
- ⚠️ End must be after start
- ⚠️ Maximum 30 days range
- ❌ Cannot mix with `--time-range`

## Common Patterns

### Real-Time Monitoring
```bash
# Check last hour (default)
rds-diag diagnose --instance my-db

# Check last 15 minutes
rds-diag diagnose --instance my-db -t 15m
```

### Daily Reports
```bash
# Yesterday (duration-based)
rds-diag report --instance my-db -t 24h -o yesterday.txt

# Specific date (timestamp-based)
rds-diag report --instance my-db \
  --start-time "2026-03-01" \
  --end-time "2026-03-02" \
  -o march-1st.txt
```

### Weekly Reports
```bash
# Last 7 days (duration-based)
rds-diag report --instance my-db -t 7d -o last-week.txt

# Specific week (timestamp-based)
rds-diag report --instance my-db \
  --start-time "2026-02-24" \
  --end-time "2026-03-02" \
  -o week-of-feb-24.txt
```

### Incident Investigation
```bash
# Analyze specific incident window
rds-diag diagnose --instance prod-db \
  --start-time "2026-03-02 14:30" \
  --end-time "2026-03-02 15:30"
```

### Peak vs Off-Peak Analysis
```bash
# Peak hours (9 AM - 5 PM)
rds-diag report --instance my-db \
  --start-time "2026-03-02 09:00" \
  --end-time "2026-03-02 17:00" \
  -o peak.txt

# Off-peak (6 PM - 2 AM next day)
rds-diag report --instance my-db \
  --start-time "2026-03-02 18:00" \
  --end-time "2026-03-03 02:00" \
  -o off-peak.txt
```

## Error Messages

### Missing end-time
```
ERROR: Both --start-time and --end-time must be specified together.
```
**Fix:** Add both options

### Conflicting options
```
ERROR: Cannot use both --time-range and --start-time/--end-time options together.
```
**Fix:** Use either `--time-range` OR `--start-time` with `--end-time`

### Invalid time order
```
ERROR: End time must be after start time
```
**Fix:** Ensure end-time is later than start-time

### Time range too large
```
ERROR: Time range too large: 59 days. Maximum is 30 days.
```
**Fix:** Reduce time range to 30 days or less

## Summary

| Feature | Duration-Based | Timestamp-Based |
|---------|---------------|-----------------|
| **Syntax** | `--time-range 24h` | `--start-time "..." --end-time "..."` |
| **Use Case** | Recent data | Specific time windows |
| **Flexibility** | Simple | Precise |
| **Historical** | ❌ | ✅ |
| **Real-time** | ✅ | ❌ |
| **Max Range** | 30 days | 30 days |

Choose the option that best fits your use case!
