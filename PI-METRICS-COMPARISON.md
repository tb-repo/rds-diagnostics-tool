# Performance Insights API vs AWS Console
## What Metrics Are Available Where

---

## SQL Query Metrics Comparison

| Metric | AWS Console | PI API | Source |
|--------|-------------|--------|--------|
| **Identification** |
| SQL Query Text | ✅ Yes | ✅ Yes | PI API |
| SQL Query ID | ✅ Yes | ✅ Yes | PI API |
| Load Contribution (AAS) | ✅ Yes | ✅ Yes | PI API |
| **Execution Metrics** |
| Calls/sec | ✅ Yes | ❌ No | pg_stat_statements |
| Average Latency (ms) | ✅ Yes | ❌ No | pg_stat_statements |
| Total Execution Time | ✅ Yes | ❌ No | pg_stat_statements |
| Execution Count | ✅ Yes | ❌ No | pg_stat_statements |
| **I/O Metrics** |
| Read Time (ms/call) | ✅ Yes | ❌ No | pg_stat_statements |
| Write Time (ms/call) | ✅ Yes | ❌ No | pg_stat_statements |
| Blocks Read | ✅ Yes | ❌ No | pg_stat_statements |
| Blocks Written | ✅ Yes | ❌ No | pg_stat_statements |
| Buffer Cache Hits | ✅ Yes | ❌ No | pg_stat_statements |
| **Row Metrics** |
| Rows/sec | ✅ Yes | ❌ No | pg_stat_statements |
| Rows/call | ✅ Yes | ❌ No | pg_stat_statements |
| Total Rows | ✅ Yes | ❌ No | pg_stat_statements |

---

## Database Grouping Comparison

| Feature | AWS Console | PI API | Source |
|---------|-------------|--------|--------|
| Top Databases | ✅ Yes | ❌ No | pg_stat_database |
| Per-Database Load | ✅ Yes | ❌ No | pg_stat_database |
| Database Connections | ✅ Yes | ⚠️ Partial | CloudWatch |
| Top Users | ✅ Yes | ✅ Yes | PI API |
| Top Hosts | ✅ Yes | ✅ Yes | PI API |
| Top Applications | ✅ Yes | ✅ Yes | PI API |

---

## Wait Events Comparison

| Feature | AWS Console | PI API | Source |
|---------|-------------|--------|--------|
| Wait Event Names | ✅ Yes | ✅ Yes | PI API |
| Wait Event Load | ✅ Yes | ✅ Yes | PI API |
| CPU Usage | ✅ Yes | ✅ Yes | PI API |
| I/O Waits | ✅ Yes | ✅ Yes | PI API |
| Lock Waits | ✅ Yes | ✅ Yes | PI API |

---

## System Metrics Comparison

| Category | AWS Console | PI API | CloudWatch | Source |
|----------|-------------|--------|------------|--------|
| **Database Load** |
| Average Active Sessions | ✅ Yes | ✅ Yes | ❌ No | PI API |
| Max Active Sessions | ✅ Yes | ✅ Yes | ❌ No | PI API |
| **CPU** |
| CPU Utilization | ✅ Yes | ✅ Yes | ✅ Yes | PI API / CloudWatch |
| CPU User | ✅ Yes | ✅ Yes | ❌ No | PI API (OS metrics) |
| CPU System | ✅ Yes | ✅ Yes | ❌ No | PI API (OS metrics) |
| CPU Wait (I/O) | ✅ Yes | ✅ Yes | ❌ No | PI API (OS metrics) |
| **Memory** |
| Freeable Memory | ✅ Yes | ✅ Yes | ✅ Yes | PI API / CloudWatch |
| Active Memory | ✅ Yes | ✅ Yes | ❌ No | PI API (OS metrics) |
| Cached Memory | ✅ Yes | ✅ Yes | ❌ No | PI API (OS metrics) |
| Buffer Memory | ✅ Yes | ✅ Yes | ❌ No | PI API (OS metrics) |
| **Disk I/O** |
| Read IOPS | ✅ Yes | ✅ Yes | ✅ Yes | PI API / CloudWatch |
| Write IOPS | ✅ Yes | ✅ Yes | ✅ Yes | PI API / CloudWatch |
| Read Latency | ✅ Yes | ✅ Yes | ✅ Yes | PI API / CloudWatch |
| Write Latency | ✅ Yes | ✅ Yes | ✅ Yes | PI API / CloudWatch |
| Read Throughput (KB/s) | ✅ Yes | ✅ Yes | ✅ Yes | PI API / CloudWatch |
| Write Throughput (KB/s) | ✅ Yes | ✅ Yes | ✅ Yes | PI API / CloudWatch |
| **Network** |
| Network Receive | ✅ Yes | ✅ Yes | ✅ Yes | PI API / CloudWatch |
| Network Transmit | ✅ Yes | ✅ Yes | ✅ Yes | PI API / CloudWatch |
| **Connections** |
| Database Connections | ✅ Yes | ❌ No | ✅ Yes | CloudWatch |

---

## Key Findings

### What PI API Provides ✅
1. **Load Metrics** - Which queries/users/events consume resources
2. **Wait Events** - What the database is waiting on
3. **OS Metrics** - System-level performance (CPU, memory, disk, network)
4. **Identification** - Which queries are running

### What PI API Does NOT Provide ❌
1. **Execution Metrics** - How many times, how fast
2. **I/O Metrics per Query** - Read/write time per query
3. **Row Metrics** - How many rows processed
4. **Database Grouping** - Top databases

### Why the Difference?

| Data Source | AWS Console | PI API | Your Tool |
|-------------|-------------|--------|-----------|
| Performance Insights API | ✅ Yes | ✅ Yes | ✅ Yes |
| pg_stat_statements | ✅ Yes | ❌ No | ❌ No |
| pg_stat_database | ✅ Yes | ❌ No | ❌ No |
| CloudWatch API | ✅ Yes | ❌ No | ✅ Yes |

**AWS Console has direct access to PostgreSQL internal tables**, which is why it shows more detailed metrics.

---

## What This Means for Your Tool

### Current Capabilities ✅
Your tool can provide:
- SQL query identification
- Load contribution analysis
- Top users by load
- Wait event analysis
- CloudWatch metrics (CPU, memory, connections, IOPS)
- OS-level metrics (74 metrics)
- Threshold violations
- Trend analysis

### Missing Capabilities ❌
Your tool cannot provide (via PI API):
- SQL execution statistics (calls/sec, latency)
- SQL I/O statistics (read/write time per query)
- SQL row statistics (rows examined/returned)
- Top databases

### To Get Missing Metrics
You need to either:
1. **Connect directly to PostgreSQL** and query `pg_stat_statements`
2. **Use CloudWatch Logs** (if slow query logging enabled)
3. **Use Enhanced CloudWatch Metrics** (aggregated, not per-query)
4. **Accept limitation** and use AWS Console for detailed SQL analysis

---

## Recommendation Matrix

| Use Case | Best Solution | Why |
|----------|---------------|-----|
| Identify which queries are running | PI API ✅ | Already works |
| See which queries consume most resources | PI API ✅ | Already works |
| Identify top users | PI API ✅ | Already works |
| Analyze wait events | PI API ✅ | Already works |
| Monitor system health | PI API + CloudWatch ✅ | Already works |
| Get query execution count | pg_stat_statements | Not in PI API |
| Get query latency | pg_stat_statements | Not in PI API |
| Get query I/O time | pg_stat_statements | Not in PI API |
| Get rows processed | pg_stat_statements | Not in PI API |
| Get top databases | pg_stat_database | Not in PI API |
| Aggregated latency metrics | CloudWatch Enhanced | Available via API |

---

## Example: What You See in AWS Console

When you look at a SQL query in AWS Console Performance Insights, you see:

```
Query: CALL usp_sesr_cron_pseudo_hub_live_dashboard_generate_cache_0001()

Load: 1.234 AAS                    ← From PI API ✅
Calls/sec: 0.5                     ← From pg_stat_statements ❌
Average latency: 125.3 ms          ← From pg_stat_statements ❌
Read time (ms/call): 45.2          ← From pg_stat_statements ❌
Write time (ms/call): 12.8         ← From pg_stat_statements ❌
Rows/sec: 150                      ← From pg_stat_statements ❌
```

**Your tool can get:** Load (1.234 AAS)  
**Your tool cannot get:** Calls/sec, latency, read/write time, rows/sec

---

## Summary

| Metric Category | Available via PI API | Workaround |
|-----------------|---------------------|------------|
| SQL Identification | ✅ Yes | None needed |
| Load Contribution | ✅ Yes | None needed |
| Top Users | ✅ Yes | None needed |
| Wait Events | ✅ Yes | None needed |
| OS Metrics | ✅ Yes | None needed |
| CloudWatch Metrics | ⚠️ Via CloudWatch API | Already implemented |
| SQL Execution Stats | ❌ No | Direct PostgreSQL connection |
| SQL I/O Stats | ❌ No | Direct PostgreSQL connection |
| SQL Row Stats | ❌ No | Direct PostgreSQL connection |
| Top Databases | ❌ No | Direct PostgreSQL connection |

---

**Conclusion:** Performance Insights API provides excellent load and wait event analysis, but does not expose PostgreSQL-specific execution statistics. For complete metrics, you need direct database access.
