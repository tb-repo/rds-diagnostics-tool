# Performance Insights Metrics - Complete Guide

## Quick Start

**Question:** What metrics can I get from Performance Insights API for Aurora PostgreSQL 17.5?

**Answer:** You can get IDENTIFICATION and LOAD metrics, but NOT EXECUTION metrics.

---

## Documents Overview

This folder contains comprehensive documentation about Performance Insights metrics:

### 1. PI-METRICS-SUMMARY.txt ⭐ START HERE
**Quick reference** showing what you can and cannot get from PI API.
- Lists all available metrics
- Shows what's missing
- Provides recommendations
- Best for: Quick lookup

### 2. PI-METRICS-REFERENCE.md
**Detailed documentation** with examples and explanations.
- Complete metric catalog
- Code examples
- Workarounds
- Best for: Implementation

### 3. PI-METRICS-COMPARISON.md
**Side-by-side comparison** of AWS Console vs PI API.
- Visual tables
- Feature comparison
- Source identification
- Best for: Understanding limitations

### 4. AURORA-POSTGRESQL-LIMITATIONS.md
**Technical analysis** of API limitations.
- Test results
- Root cause analysis
- Comparison with Aurora MySQL
- Best for: Deep dive

### 5. ALTERNATIVE-OPTIONS.md
**Solutions** for getting missing metrics.
- 6 different approaches
- Pros/cons for each
- Implementation effort
- Best for: Planning next steps

---

## The Bottom Line

### What Performance Insights API Provides ✅

```
┌─────────────────────────────────────────────────────────────┐
│ IDENTIFICATION METRICS                                      │
├─────────────────────────────────────────────────────────────┤
│ • Which SQL queries are running                             │
│ • Which users are active                                    │
│ • Which wait events are occurring                           │
│ • SQL query text                                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ LOAD METRICS                                                │
├─────────────────────────────────────────────────────────────┤
│ • How much load each query contributes (AAS)                │
│ • How much load each user contributes                       │
│ • How much load each wait event contributes                 │
│ • Database load over time                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ OS-LEVEL METRICS (74 metrics)                               │
├─────────────────────────────────────────────────────────────┤
│ • CPU utilization (total, user, system, wait)               │
│ • Memory usage (free, active, cached, buffers)              │
│ • Disk I/O (IOPS, latency, throughput)                      │
│ • Network (receive/transmit throughput)                     │
│ • Swap usage                                                │
│ • Load average                                              │
└─────────────────────────────────────────────────────────────┘
```

### What Performance Insights API Does NOT Provide ❌

```
┌─────────────────────────────────────────────────────────────┐
│ EXECUTION METRICS                                           │
├─────────────────────────────────────────────────────────────┤
│ ✗ How many times a query executed (calls/sec)               │
│ ✗ How long each execution took (average latency)            │
│ ✗ Total execution time                                      │
│ ✗ Execution count                                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ I/O METRICS PER QUERY                                       │
├─────────────────────────────────────────────────────────────┤
│ ✗ Read time (ms/call)                                       │
│ ✗ Write time (ms/call)                                      │
│ ✗ Blocks read from disk                                     │
│ ✗ Blocks written to disk                                    │
│ ✗ Buffer cache hit ratio                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ROW METRICS                                                 │
├─────────────────────────────────────────────────────────────┤
│ ✗ Rows examined per execution                               │
│ ✗ Rows returned per execution                               │
│ ✗ Rows per second                                           │
│ ✗ Efficiency ratio (returned/examined)                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ DATABASE GROUPING                                           │
├─────────────────────────────────────────────────────────────┤
│ ✗ Top databases by load                                     │
│ ✗ Per-database metrics                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Why This Matters

### Your Current Report Shows:

```
Query #1: CALL usp_sesr_cron_pseudo_hub_live_dashboard_generate_cache_0001()

✅ SQL Text: CALL usp_sesr_cron_pseudo_hub_live_dashboard_generate_cache_0001()
✅ Engine: aurora-postgresql
✅ Total Load: 1.234 AAS

❌ Executions/sec: N/A
❌ Average Latency: N/A
❌ CPU Time: N/A
❌ Lock Time: N/A
❌ Rows Examined: N/A
❌ Rows Returned: N/A
❌ Read I/O Time: N/A
❌ Write I/O Time: N/A
```

### AWS Console Shows:

```
Query #1: CALL usp_sesr_cron_pseudo_hub_live_dashboard_generate_cache_0001()

✅ SQL Text: CALL usp_sesr_cron_pseudo_hub_live_dashboard_generate_cache_0001()
✅ Load: 1.234 AAS
✅ Calls/sec: 0.5
✅ Average latency: 125.3 ms
✅ Read time (ms/call): 45.2
✅ Write time (ms/call): 12.8
✅ Rows/sec: 150
```

**Why the difference?**

AWS Console has **direct access to PostgreSQL's `pg_stat_statements` table**.  
Performance Insights API does **NOT expose this table**.

---

## What You Can Do

### Option A: Accept Current Limitations
Use the tool for what it does well:
- ✅ Identify which queries are running
- ✅ See which queries consume most resources
- ✅ Identify top users
- ✅ Analyze wait events
- ✅ Monitor system health
- ✅ Detect threshold violations
- ✅ Track trends

Use AWS Console for detailed SQL analysis.

### Option B: Add Enhanced CloudWatch Metrics (Recommended)
Collect additional CloudWatch metrics:
- SelectLatency, DMLLatency
- ReadLatency, WriteLatency
- SelectThroughput, DMLThroughput

**Pros:** Easy to implement (2-3 hours), no database access needed  
**Cons:** Database-level only (not per-query)

See: ALTERNATIVE-OPTIONS.md Option 1

### Option C: Direct PostgreSQL Connection
Connect to PostgreSQL and query `pg_stat_statements`.

**Pros:** All metrics available, most accurate  
**Cons:** Requires database credentials and network access

See: ALTERNATIVE-OPTIONS.md Option 6

---

## Testing

To verify what metrics are available for your instance:

```bash
# Run comprehensive test
python list_all_pi_metrics.py

# Or use batch file
list-pi-metrics.bat
```

This will:
1. List all available dimension groups
2. List all available resource metrics  
3. Test each dimension group
4. Show sample data
5. Provide a summary

---

## Metric Catalog

### Dimension Groups (What You Can Group By)

| Group | Status | Description |
|-------|--------|-------------|
| db.sql | ✅ Works | Top SQL queries by load |
| db.sql_tokenized | ✅ Works | Grouped query patterns |
| db.wait_event | ✅ Works | Wait events (CPU, I/O, locks) |
| db.user | ✅ Works | Top users by load |
| db.host | ✅ Works | Top client hosts |
| db.application | ✅ Works | Top applications |
| db.session_type | ✅ Works | Session types |
| db.name | ❌ Not supported | Top databases |
| db.database | ❌ Not supported | Database grouping |

### Load Metrics

| Metric | Status | Description |
|--------|--------|-------------|
| db.load.avg | ✅ Works | Average active sessions |
| db.load.max | ✅ Works | Maximum active sessions |
| db.load.min | ✅ Works | Minimum active sessions |

### OS Metrics (74 available)

| Category | Example Metrics | Status |
|----------|----------------|--------|
| CPU | os.cpuUtilization.total.avg | ✅ Works |
| Memory | os.memory.free.avg | ✅ Works |
| Disk I/O | os.diskIO.readLatency.avg | ✅ Works |
| Network | os.network.rx.avg | ✅ Works |
| Swap | os.swap.free.avg | ✅ Works |
| Load | os.loadAverageMinute.one.avg | ✅ Works |

See PI-METRICS-REFERENCE.md for complete list.

### SQL Execution Metrics

| Metric | Status | Source |
|--------|--------|--------|
| calls_per_sec | ❌ Not available | pg_stat_statements |
| avg_latency_per_call | ❌ Not available | pg_stat_statements |
| rows_per_sec | ❌ Not available | pg_stat_statements |
| blk_read_time | ❌ Not available | pg_stat_statements |
| blk_write_time | ❌ Not available | pg_stat_statements |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR TOOL                                │
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │ Performance  │         │  CloudWatch  │                │
│  │  Insights    │◄────────┤     API      │                │
│  │     API      │         │              │                │
│  └──────┬───────┘         └──────────────┘                │
│         │                                                   │
│         │ Returns:                                          │
│         │ • SQL query IDs                                   │
│         │ • Load metrics (AAS)                              │
│         │ • Wait events                                     │
│         │ • Top users                                       │
│         │ • OS metrics                                      │
│         │                                                   │
│         │ Does NOT return:                                  │
│         │ ✗ Execution count                                 │
│         │ ✗ Latency                                         │
│         │ ✗ I/O time                                        │
│         │ ✗ Rows processed                                  │
└─────────┴───────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  AWS CONSOLE                                │
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │ Performance  │         │  PostgreSQL  │                │
│  │  Insights    │◄────────┤   Internal   │                │
│  │     API      │         │    Tables    │                │
│  └──────────────┘         └──────┬───────┘                │
│                                  │                          │
│                                  │ Direct Access:           │
│                                  │ • pg_stat_statements     │
│                                  │ • pg_stat_database       │
│                                  │                          │
│                                  │ Returns:                 │
│                                  │ ✅ Execution count       │
│                                  │ ✅ Latency               │
│                                  │ ✅ I/O time              │
│                                  │ ✅ Rows processed        │
└──────────────────────────────────┴──────────────────────────┘
```

---

## Next Steps

1. **Read PI-METRICS-SUMMARY.txt** for quick reference
2. **Run list_all_pi_metrics.py** to verify metrics for your instance
3. **Review ALTERNATIVE-OPTIONS.md** to decide on approach
4. **Choose:**
   - Option A: Accept limitations, use Console for SQL details
   - Option B: Add Enhanced CloudWatch Metrics (recommended)
   - Option C: Implement direct PostgreSQL connection

---

## Questions?

- **Q: Why can't I get SQL execution metrics?**  
  A: Aurora PostgreSQL PI API doesn't expose `pg_stat_statements`. AWS Console has direct access to this table.

- **Q: Can I get these metrics through any AWS API?**  
  A: Not per-query. CloudWatch provides database-level latency metrics (SelectLatency, DMLLatency).

- **Q: What's the best workaround?**  
  A: For programmatic access without database connection, use Enhanced CloudWatch Metrics (Option B). For complete metrics, use direct PostgreSQL connection (Option C).

- **Q: Does Aurora MySQL have the same limitation?**  
  A: No! Aurora MySQL PI API provides SQL execution metrics through the AdditionalMetrics parameter.

- **Q: Will this change in the future?**  
  A: Unknown. This is an AWS API design decision. Monitor AWS announcements for updates.

---

## References

- [AWS Performance Insights Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.html)
- [PostgreSQL pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html)
- [Aurora PostgreSQL Performance Insights](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/USER_PerfInsights.html)
- [CloudWatch RDS Metrics](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/monitoring-cloudwatch.html)

---

**Last Updated:** February 27, 2026  
**Tested With:** Aurora PostgreSQL 17.5  
**Instance:** ielts-ses-sit-v1-clusterinstance1
