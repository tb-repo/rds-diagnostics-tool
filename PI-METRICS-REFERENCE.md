# Performance Insights Metrics Reference
## Aurora PostgreSQL 17.5

**Instance:** ielts-ses-sit-v1-clusterinstance1  
**Engine:** aurora-postgresql 17.5  
**Last Updated:** February 27, 2026

---

## Executive Summary

Performance Insights API for Aurora PostgreSQL 17.5 provides **identification and load metrics** but NOT **execution metrics**. This means you can see WHAT is running and HOW MUCH load it creates, but not HOW MANY TIMES it runs or HOW FAST it executes.

---

## Available Dimension Groups ✅

These dimension groups work and return data:

### 1. db.sql ✅
- **Purpose:** Identify top SQL queries by load
- **Returns:** SQL query IDs and their contribution to database load
- **Key Fields:**
  - `db.sql.id` - Unique query identifier
  - `db.sql.statement` - SQL query text (via get_resource_metadata)
  - `Total` - Total load contribution (AAS - Average Active Sessions)

**Example:**
```python
{
  'Dimensions': {'db.sql.id': '8709EEADC409741D404A04D61CF19F8BAF3C340A'},
  'Total': 1.234,  # AAS
  'Partitions': [...]
}
```

### 2. db.sql_tokenized ✅
- **Purpose:** Group similar queries (with different literal values)
- **Returns:** Tokenized query IDs
- **Use Case:** Identify query patterns across different parameter values

### 3. db.wait_event ✅
- **Purpose:** Identify what the database is waiting on
- **Returns:** Wait event types and their contribution to load
- **Common Events:**
  - `CPU` - Active CPU usage
  - `IO:DataFileRead` - Reading from disk
  - `Lock:relation` - Waiting for table locks
  - `Lock:tuple` - Waiting for row locks

**Example:**
```python
{
  'Dimensions': {'db.wait_event.name': 'CPU'},
  'Total': 0.456  # AAS spent on CPU
}
```

### 4. db.user ✅
- **Purpose:** Identify top database users by load
- **Returns:** Database usernames and their load contribution
- **Key Fields:**
  - `db.user` or `db.user.name` - Username

**Example:**
```python
{
  'Dimensions': {'db.user.name': 'speaking_exam_sit_read'},
  'Total': 4.62  # AAS
}
```

### 5. db.host ✅
- **Purpose:** Identify which client hosts are generating load
- **Returns:** Client IP addresses or hostnames

### 6. db.application ✅
- **Purpose:** Identify applications by their connection string
- **Returns:** Application names from connection metadata

### 7. db.session_type ✅
- **Purpose:** Distinguish between foreground and background sessions
- **Returns:** Session type classification

---

## NOT Available Dimension Groups ❌

These dimension groups are NOT supported for Aurora PostgreSQL:

### db.name ❌
- **Error:** "The specified group is not a known group"
- **Impact:** Cannot get top databases
- **Workaround:** None via PI API

### db.database ❌
- **Error:** "The specified group is not a known group"
- **Impact:** Cannot group metrics by database name
- **Workaround:** None via PI API

---

## Available Metrics ✅

### Database Load Metrics

| Metric | Description | Unit | Available |
|--------|-------------|------|-----------|
| `db.load.avg` | Average active sessions | AAS | ✅ Yes |
| `db.load.max` | Maximum active sessions | AAS | ✅ Yes |
| `db.load.min` | Minimum active sessions | AAS | ✅ Yes |

**What this tells you:**
- How busy the database is
- Which queries/users/wait events contribute most to load
- Peak load times

**What this DOESN'T tell you:**
- How many times a query executed
- How long each execution took
- How many rows were processed

### OS-Level Metrics (74 metrics available) ✅

Performance Insights provides extensive OS-level metrics:

#### CPU Metrics
- `os.cpuUtilization.total.avg` - Average CPU usage
- `os.cpuUtilization.user.avg` - User space CPU
- `os.cpuUtilization.system.avg` - System/kernel CPU
- `os.cpuUtilization.wait.avg` - I/O wait time
- `os.cpuUtilization.idle.avg` - Idle CPU
- `os.cpuUtilization.nice.avg` - Nice priority processes
- `os.cpuUtilization.steal.avg` - Stolen CPU (virtualization)
- `os.cpuUtilization.irq.avg` - Hardware interrupts
- `os.cpuUtilization.softIrq.avg` - Software interrupts
- `os.cpuUtilization.guest.avg` - Guest VM CPU

#### Memory Metrics
- `os.memory.total` - Total memory
- `os.memory.free.avg` - Free memory
- `os.memory.active.avg` - Active memory
- `os.memory.inactive.avg` - Inactive memory
- `os.memory.cached.avg` - Page cache
- `os.memory.buffers.avg` - Buffer cache
- `os.memory.dirty.avg` - Dirty pages
- `os.memory.writeback.avg` - Pages being written back
- `os.memory.hugePagesFree.avg` - Free huge pages
- `os.memory.hugePagesTotal` - Total huge pages

#### Disk I/O Metrics
- `os.diskIO.readIOsPS.avg` - Read IOPS
- `os.diskIO.writeIOsPS.avg` - Write IOPS
- `os.diskIO.readKb.avg` - KB read per second
- `os.diskIO.writeKb.avg` - KB written per second
- `os.diskIO.readLatency.avg` - Read latency (ms)
- `os.diskIO.writeLatency.avg` - Write latency (ms)
- `os.diskIO.diskQueueDepth.avg` - Queue depth
- `os.diskIO.await.avg` - Average wait time
- `os.diskIO.util.avg` - Disk utilization %

#### Network Metrics
- `os.network.rx.avg` - Bytes received per second
- `os.network.tx.avg` - Bytes transmitted per second

#### Swap Metrics
- `os.swap.total` - Total swap space
- `os.swap.free.avg` - Free swap space
- `os.swap.cached.avg` - Cached swap
- `os.swap.in.avg` - Swap in rate
- `os.swap.out.avg` - Swap out rate

#### Process/Task Metrics
- `os.tasks.running.avg` - Running processes
- `os.tasks.sleeping.avg` - Sleeping processes
- `os.tasks.blocked.avg` - Blocked processes
- `os.tasks.zombie.avg` - Zombie processes
- `os.tasks.stopped.avg` - Stopped processes
- `os.tasks.total.avg` - Total processes

#### File System Metrics
- `os.fileSys.used.avg` - Used disk space
- `os.fileSys.total` - Total disk space
- `os.fileSys.maxConfigured` - Max configured space

#### Load Average
- `os.loadAverageMinute.one.avg` - 1-minute load average
- `os.loadAverageMinute.five.avg` - 5-minute load average
- `os.loadAverageMinute.fifteen.avg` - 15-minute load average

---

## NOT Available Metrics ❌

### SQL Execution Metrics (db.sql.stats.*)

These metrics are available for Aurora MySQL but NOT for Aurora PostgreSQL:

| Metric | Description | Available |
|--------|-------------|-----------|
| `db.sql.stats.calls_per_sec` | Executions per second | ❌ No |
| `db.sql.stats.avg_latency_per_call` | Average latency (ms) | ❌ No |
| `db.sql.stats.total_time` | Total execution time | ❌ No |
| `db.sql.stats.rows_per_call` | Rows per execution | ❌ No |
| `db.sql.stats.rows_per_sec` | Rows per second | ❌ No |
| `db.sql.stats.blk_read_time` | Block read time | ❌ No |
| `db.sql.stats.blk_write_time` | Block write time | ❌ No |
| `db.sql.stats.shared_blks_read` | Blocks read | ❌ No |
| `db.sql.stats.shared_blks_written` | Blocks written | ❌ No |
| `db.sql.stats.shared_blks_hit` | Buffer cache hits | ❌ No |
| `db.sql.stats.local_blks_read` | Local blocks read | ❌ No |
| `db.sql.stats.local_blks_written` | Local blocks written | ❌ No |
| `db.sql.stats.temp_blks_read` | Temp blocks read | ❌ No |
| `db.sql.stats.temp_blks_written` | Temp blocks written | ❌ No |

**Result:** When you call `list_available_resource_metrics` with `MetricTypes=['db.sql.stats']`, it returns **0 metrics**.

### AdditionalMetrics Parameter ❌

The `AdditionalMetrics` parameter in `describe_dimension_keys` is NOT supported for Aurora PostgreSQL:

```python
# This works for Aurora MySQL but NOT PostgreSQL
response = pi_client.describe_dimension_keys(
    ...
    AdditionalMetrics=['db.sql.stats.calls_per_sec', 'db.sql.stats.avg_latency_per_call']
)
# Error: Parameter validation failed (empty list not allowed)
```

---

## What You CAN Do with PI API ✅

### 1. Identify Top SQL Queries by Load
```python
# Get queries that contribute most to database load
queries = describe_dimension_keys(
    group_by='db.sql',
    metric='db.load.avg'
)
# Returns: List of SQL IDs with their load contribution
```

**Use Case:** Find which queries are keeping the database busy

### 2. Identify Top Users by Load
```python
# Get users generating the most load
users = describe_dimension_keys(
    group_by='db.user',
    metric='db.load.avg'
)
# Returns: List of usernames with their load contribution
```

**Use Case:** Identify which applications/users are impacting performance

### 3. Analyze Wait Events
```python
# See what the database is waiting on
wait_events = describe_dimension_keys(
    group_by='db.wait_event',
    metric='db.load.avg'
)
# Returns: CPU, IO, Lock waits with their contribution
```

**Use Case:** Diagnose if issue is CPU-bound, I/O-bound, or lock contention

### 4. Monitor OS-Level Performance
```python
# Get detailed OS metrics
metrics = get_resource_metrics(
    metrics=[
        'os.cpuUtilization.total.avg',
        'os.memory.free.avg',
        'os.diskIO.readLatency.avg',
        'os.diskIO.writeLatency.avg'
    ]
)
```

**Use Case:** Correlate database load with OS-level resource usage

### 5. Track Load Over Time
```python
# Get time-series data for database load
load_history = get_resource_metrics(
    metrics=['db.load.avg', 'db.load.max']
)
```

**Use Case:** Identify peak load times and trends

---

## What You CANNOT Do with PI API ❌

### 1. Get SQL Execution Statistics
- ❌ How many times a query executed
- ❌ Average execution time per call
- ❌ Total execution time
- ❌ Executions per second

**Why:** These metrics come from `pg_stat_statements` which is not exposed via PI API

### 2. Get SQL I/O Statistics
- ❌ Read time per call
- ❌ Write time per call
- ❌ Blocks read/written
- ❌ Buffer cache hit ratio per query

**Why:** These metrics come from `pg_stat_statements` which is not exposed via PI API

### 3. Get SQL Row Statistics
- ❌ Rows examined per execution
- ❌ Rows returned per execution
- ❌ Rows per second
- ❌ Efficiency ratio (returned/examined)

**Why:** These metrics come from `pg_stat_statements` which is not exposed via PI API

### 4. Group by Database
- ❌ Top databases by load
- ❌ Per-database metrics

**Why:** `db.name` and `db.database` dimension groups not supported

---

## Why AWS Console Shows More Data

The AWS Performance Insights console displays metrics like:
- Average latency (ms)
- Read time (ms/call)
- Write time (ms/call)
- Rows/sec
- Calls/sec

**How does it get this data?**

The AWS Console has **direct access to PostgreSQL's internal statistics tables**:
- `pg_stat_statements` - Query execution statistics
- `pg_stat_database` - Database-level statistics
- `pg_stat_user_tables` - Table access statistics

The Console queries these tables directly, which is why it can show detailed execution metrics.

**Why can't the PI API provide this?**

The Performance Insights API is designed to be database-agnostic and provide a consistent interface across different database engines. It focuses on:
- Load metrics (what's consuming resources)
- Wait events (what's blocking work)
- OS metrics (system-level performance)

Engine-specific statistics (like `pg_stat_statements`) are not exposed through the API.

---

## Workarounds to Get Missing Metrics

### Option 1: Direct PostgreSQL Connection ⭐ RECOMMENDED
Connect directly to PostgreSQL and query `pg_stat_statements`:

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
- All metrics available
- Real-time data
- Most accurate

**Cons:**
- Requires database credentials
- Requires network access
- Requires `pg_stat_statements` extension enabled

### Option 2: CloudWatch Logs Insights
Enable slow query logging and parse logs:

**Pros:**
- No database access needed
- Uses AWS APIs

**Cons:**
- Only captures slow queries
- Requires log configuration
- Less real-time

### Option 3: Enhanced CloudWatch Metrics
Use additional CloudWatch metrics:

**Metrics Available:**
- `SelectLatency` - SELECT query latency
- `DMLLatency` - INSERT/UPDATE/DELETE latency
- `ReadLatency` - Read operation latency
- `WriteLatency` - Write operation latency
- `SelectThroughput` - SELECT queries per second
- `DMLThroughput` - DML operations per second

**Pros:**
- No database access needed
- Uses existing AWS APIs
- Easy to implement

**Cons:**
- Aggregated metrics (not per-query)
- Less detailed than pg_stat_statements

### Option 4: Use AWS Console
For ad-hoc analysis, use the AWS Console Performance Insights UI.

**Pros:**
- All metrics visible
- No code changes needed

**Cons:**
- Manual process
- Not programmatic
- Not suitable for automation

---

## Recommendations

### For Your Current Situation

Based on your requirements to see metrics like "Read time (ms/call)", "Average latency", "Rows/sec":

1. **Short-term:** Use AWS Console for detailed SQL analysis
2. **Medium-term:** Implement Option 3 (Enhanced CloudWatch Metrics) for programmatic access to latency metrics
3. **Long-term:** Implement Option 1 (Direct PostgreSQL connection) for complete metrics

### What the Tool Currently Provides

Your RDS Diagnostics Tool currently provides:
- ✅ SQL query identification (which queries are running)
- ✅ Load contribution (which queries consume most resources)
- ✅ Top users (which users generate most load)
- ✅ Wait events (CPU, I/O, locks)
- ✅ CloudWatch metrics (CPU, memory, connections, IOPS)
- ✅ OS-level metrics (74 metrics)
- ✅ Threshold violations and trends

### What's Missing

- ❌ SQL execution statistics (calls/sec, latency, rows)
- ❌ SQL I/O statistics (read/write time per query)
- ❌ Top databases

---

## Testing Script

To verify what metrics are available for your instance, run:

```bash
python list_all_pi_metrics.py
```

Or use the batch file:

```bash
list-pi-metrics.bat
```

This will:
1. List all available dimension groups
2. List all available resource metrics
3. Test each dimension group
4. Show sample data
5. Provide a summary

---

## References

- [AWS Performance Insights Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.html)
- [PostgreSQL pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html)
- [Aurora PostgreSQL Performance Insights](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/USER_PerfInsights.html)

---

**Last Updated:** February 27, 2026  
**Tested With:** Aurora PostgreSQL 17.5  
**Instance:** ielts-ses-sit-v1-clusterinstance1
