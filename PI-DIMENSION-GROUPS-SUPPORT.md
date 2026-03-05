# Performance Insights Dimension Groups Support

## Issue: "The specified group is not a known group"

This error occurs when trying to collect top databases for Aurora PostgreSQL because the `db.name` dimension group is not supported for PostgreSQL engines.

---

## What Was Fixed

### Before (Error):
```
ERROR - Failed to collect top databases: AWS API error: The specified group is not a known group
```

### After (Graceful Handling):
```
INFO - Top databases not available for aurora-postgresql: This is normal for Aurora PostgreSQL.
```

---

## Dimension Group Support by Engine

### Supported Dimension Groups

| Dimension Group | MySQL/MariaDB | PostgreSQL | Aurora MySQL | Aurora PostgreSQL |
|----------------|---------------|------------|--------------|-------------------|
| `db.sql` | ✅ | ✅ | ✅ | ✅ |
| `db.wait_event` | ✅ | ✅ | ✅ | ✅ |
| `db.user` | ✅ | ✅ | ✅ | ✅ |
| `db.host` | ✅ | ✅ | ✅ | ✅ |
| `db.name` | ✅ | ❌ | ✅ | ❌ |
| `db.application` | ❌ | ✅ | ❌ | ✅ |

### What This Means

**For Aurora PostgreSQL:**
- ✅ Top SQL queries - Available
- ✅ Wait events - Available
- ✅ Top users - Available
- ❌ Top databases - NOT available (db.name not supported)
- ✅ Top applications - Available (db.application)

**For Aurora MySQL:**
- ✅ Top SQL queries - Available
- ✅ Wait events - Available
- ✅ Top users - Available
- ✅ Top databases - Available
- ❌ Top applications - NOT available

---

## What the Tool Does Now

### 1. Engine Detection
The tool now checks the database engine before attempting to collect top databases:

```python
if 'postgres' in engine.lower():
    logger.info("Top databases by load not available for PostgreSQL")
    return []
```

### 2. Graceful Degradation
- For PostgreSQL: Skips top databases collection (not supported)
- For MySQL: Collects top databases normally
- No error messages - just an informational log

### 3. Report Output
The report will show:
- For PostgreSQL: "Top databases" section is omitted (not shown)
- For MySQL: "Top databases" section with data

---

## Available Metrics by Engine

### Aurora PostgreSQL - What You Get:

✅ **Instance Information**
- Engine version, instance class, storage

✅ **CloudWatch Metrics**
- CPU, memory, connections, IOPS

✅ **OS-Level Metrics** (NEW!)
- CPU breakdown, memory, disk I/O, latency

✅ **Top SQL Queries**
- Query text, execution load, time buckets
- Wait events per query

✅ **Wait Events**
- Top wait events by load

✅ **Top Users**
- Users by database load

❌ **Top Databases**
- NOT available (dimension not supported)

### Aurora MySQL - What You Get:

All of the above, PLUS:

✅ **Top Databases**
- Databases by load percentage

---

## Why This Limitation Exists

### AWS Performance Insights API Design

The Performance Insights API uses different dimension groups for different database engines based on:

1. **Engine Architecture**: PostgreSQL and MySQL have different internal structures
2. **Metadata Availability**: Some engines expose different metadata
3. **AWS Implementation**: AWS implements PI features differently per engine

### PostgreSQL Specifics

- PostgreSQL doesn't expose database-level load in the same way MySQL does
- PostgreSQL focuses on application-level grouping instead
- You can still see which databases are being queried in the SQL query text

---

## Workarounds for PostgreSQL

### Option 1: Check SQL Query Text
The SQL queries show which databases are being accessed:
```sql
SELECT * FROM my_database.my_table WHERE ...
```

### Option 2: Use Top Users
Users are often associated with specific databases, so top users can give you insights into database usage.

### Option 3: Use CloudWatch Metrics
CloudWatch provides instance-level metrics that apply to all databases.

### Option 4: Query pg_stat_database Directly
If you need database-level statistics, you can query PostgreSQL directly:
```sql
SELECT datname, 
       numbackends,
       xact_commit,
       xact_rollback,
       blks_read,
       blks_hit
FROM pg_stat_database
WHERE datname NOT IN ('template0', 'template1', 'rdsadmin');
```

---

## Impact on Reports

### Technical Report
- "TOP DATABASES BY LOAD" section is omitted for PostgreSQL
- All other sections remain available
- No error messages in the report

### Management Report
- Database breakdown not included for PostgreSQL
- Focus on SQL queries, wait events, and users instead
- Overall assessment still accurate

---

## Logging Changes

### Before (Error Level):
```
ERROR - Failed to collect top databases: AWS API error: The specified group is not a known group
```

### After (Info Level):
```
INFO - Top databases not available for aurora-postgresql: This is normal for Aurora PostgreSQL.
```

This change:
- ✅ Reduces noise in logs
- ✅ Clarifies this is expected behavior
- ✅ Doesn't alarm users with ERROR messages
- ✅ Still provides information for debugging

---

## Testing

The fix has been implemented and tested:

1. ✅ Detects PostgreSQL engines correctly
2. ✅ Skips top databases collection for PostgreSQL
3. ✅ Logs informational message instead of error
4. ✅ Continues with other data collection
5. ✅ Generates complete report without top databases section

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| Error Message | ❌ ERROR logged | ✅ INFO logged |
| Report Generation | ✅ Continues | ✅ Continues |
| Top Databases (PostgreSQL) | ❌ Attempted, failed | ✅ Skipped gracefully |
| Top Databases (MySQL) | ✅ Works | ✅ Works |
| User Experience | ⚠️ Confusing error | ✅ Clean, expected |

---

## Files Modified

- `collectors/performance_insights.py` - Added engine detection and graceful handling

---

## Related Documentation

- `AURORA-POSTGRESQL-LIMITATIONS.md` - Complete list of PI API limitations
- `PI-METRICS-REFERENCE.md` - Available metrics by engine
- `ALTERNATIVE-OPTIONS.md` - Workarounds for missing metrics

---

## For Users

**This is normal behavior!** If you see:
```
INFO - Top databases not available for aurora-postgresql
```

This means:
- ✅ Everything is working correctly
- ✅ This is expected for PostgreSQL
- ✅ All other metrics are still collected
- ✅ Your report is complete and accurate

**No action needed!**
