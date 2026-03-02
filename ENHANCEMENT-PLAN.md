# Enhancement Plan: OS Disk I/O Metrics & Execution Count Fix

## Issues Identified

### Issue 1: OS Disk I/O Metrics Not Collected ❌
**Status:** Available but not being collected  
**Impact:** Missing critical I/O performance data  
**Priority:** HIGH

### Issue 2: Execution Count Always Shows 1 ❌
**Status:** Bug in calculation logic  
**Impact:** Inaccurate execution statistics  
**Priority:** HIGH

### Issue 3: Temp Usage Metrics Not Collected ❌
**Status:** Available but not being collected  
**Impact:** Missing temp space analysis  
**Priority:** MEDIUM

---

## Issue 1: OS Disk I/O Metrics

### What's Available ✅

Performance Insights provides these OS-level disk I/O metrics:

```python
# IOPS
'os.diskIO.readIOsPS.avg'      # Read IOPS
'os.diskIO.writeIOsPS.avg'     # Write IOPS

# Latency (THIS IS WHAT YOU NEED!)
'os.diskIO.readLatency.avg'    # Read latency (ms)
'os.diskIO.writeLatency.avg'   # Write latency (ms)

# Throughput
'os.diskIO.readKb.avg'         # KB/sec read
'os.diskIO.writeKb.avg'        # KB/sec written

# Queue and Utilization
'os.diskIO.diskQueueDepth.avg' # Queue depth
'os.diskIO.await.avg'          # Average wait time
'os.diskIO.util.avg'           # Disk utilization %
```

### Why This Helps 🎯

You're absolutely right! These metrics can help identify performance issues:

1. **High Read Latency** → Slow disk reads → Queries waiting for data
2. **High Write Latency** → Slow disk writes → Commits taking long
3. **High IOPS** → Heavy I/O workload → May need faster storage
4. **High Queue Depth** → I/O bottleneck → Queries queuing for disk access

### Correlation with SQL Performance

```
High SQL Load + High Read Latency = Queries waiting for disk reads
High SQL Load + High Write Latency = Queries waiting for commits
High SQL Load + Low I/O Latency = CPU-bound queries (not I/O issue)
```

### Current State

We're currently collecting:
- ✅ CloudWatch IOPS (ReadIOPS, WriteIOPS)
- ❌ OS-level disk I/O metrics (NOT collected)

CloudWatch IOPS are aggregated at instance level.  
OS-level metrics from PI are more granular and include latency!

---

## Issue 2: Execution Count Always Shows 1

### Root Cause

Looking at the code in `collect_top_sql_queries`:

```python
# Line 626-627
partitions = key.get('Partitions', [])
exec_count = len(partitions) if partitions else 1
```

**Problem:** `Partitions` represents time buckets, NOT execution count!

### What Partitions Actually Are

From AWS PI API documentation:
- `Partitions` = Array of time-series data points
- Each partition = One time bucket (e.g., 5-minute interval)
- `Total` = Sum of load across all partitions

**Example:**
```python
{
  'Total': 1.234,  # Total load (AAS)
  'Partitions': [
    {'Timestamp': '2026-02-27T06:00:00Z', 'Value': 0.5},
    {'Timestamp': '2026-02-27T06:05:00Z', 'Value': 0.4},
    {'Timestamp': '2026-02-27T06:10:00Z', 'Value': 0.334}
  ]
}
```

This means:
- Total load = 1.234 AAS
- 3 time buckets (not 3 executions!)
- Execution count = UNKNOWN (not available in PI API)

### Why It's Always 1

If there's only 1 time bucket in the response, `len(partitions) = 1`.  
This is NOT the execution count - it's the number of time samples!

### The Truth

**Execution count is NOT available from Performance Insights API for PostgreSQL.**

It's only available from:
1. `pg_stat_statements.calls` (direct PostgreSQL connection)
2. CloudWatch Logs (if slow query logging enabled)

---

## Issue 3: Temp Usage Metrics

### What's Available ✅

Performance Insights provides temp file metrics:

```python
# Temp blocks (PostgreSQL specific)
'os.diskIO.tempBlksRead.avg'     # Temp blocks read
'os.diskIO.tempBlksWritten.avg'  # Temp blocks written

# Swap usage (OS level)
'os.swap.total'                   # Total swap space
'os.swap.free.avg'                # Free swap space
'os.swap.cached.avg'              # Cached swap
'os.swap.in.avg'                  # Swap in rate
'os.swap.out.avg'                 # Swap out rate
```

### Why This Helps 🎯

1. **High Temp Blocks** → Queries spilling to disk → Need more work_mem
2. **Swap Usage** → Memory pressure → Need more RAM or optimize queries

---

## Solution: Collect OS Metrics from Performance Insights

### Implementation Plan

#### Step 1: Add OS Metrics Collection Method

Add new method to `PerformanceInsightsCollector`:

```python
def collect_os_metrics(
    self,
    instance_id: str,
    time_range: TimeRange
) -> Dict[str, float]:
    """
    Collect OS-level metrics from Performance Insights.
    
    Returns:
        Dictionary of metric names to average values
    """
```

#### Step 2: Define OS Metrics to Collect

```python
OS_METRICS = [
    # CPU
    'os.cpuUtilization.total.avg',
    'os.cpuUtilization.user.avg',
    'os.cpuUtilization.system.avg',
    'os.cpuUtilization.wait.avg',  # I/O wait - important!
    
    # Memory
    'os.memory.free.avg',
    'os.memory.active.avg',
    'os.memory.cached.avg',
    
    # Disk I/O - THE KEY METRICS YOU NEED!
    'os.diskIO.readIOsPS.avg',
    'os.diskIO.writeIOsPS.avg',
    'os.diskIO.readLatency.avg',   # ⭐ Read latency
    'os.diskIO.writeLatency.avg',  # ⭐ Write latency
    'os.diskIO.readKb.avg',
    'os.diskIO.writeKb.avg',
    'os.diskIO.diskQueueDepth.avg',
    'os.diskIO.await.avg',
    'os.diskIO.util.avg',
    
    # Temp usage
    'os.diskIO.tempBlksRead.avg',
    'os.diskIO.tempBlksWritten.avg',
    
    # Swap
    'os.swap.free.avg',
    'os.swap.in.avg',
    'os.swap.out.avg',
    
    # Load average
    'os.loadAverageMinute.one.avg',
    'os.loadAverageMinute.five.avg',
]
```

#### Step 3: Add to Data Model

Add new dataclass to `core/models.py`:

```python
@dataclass
class OSMetrics:
    """OS-level performance metrics from Performance Insights."""
    
    # CPU
    cpu_total: Optional[float] = None
    cpu_user: Optional[float] = None
    cpu_system: Optional[float] = None
    cpu_wait: Optional[float] = None  # I/O wait
    
    # Memory
    memory_free_gb: Optional[float] = None
    memory_active_gb: Optional[float] = None
    memory_cached_gb: Optional[float] = None
    
    # Disk I/O
    read_iops: Optional[float] = None
    write_iops: Optional[float] = None
    read_latency_ms: Optional[float] = None   # ⭐ Key metric
    write_latency_ms: Optional[float] = None  # ⭐ Key metric
    read_throughput_kbps: Optional[float] = None
    write_throughput_kbps: Optional[float] = None
    disk_queue_depth: Optional[float] = None
    disk_await_ms: Optional[float] = None
    disk_utilization_pct: Optional[float] = None
    
    # Temp usage
    temp_blocks_read: Optional[float] = None
    temp_blocks_written: Optional[float] = None
    
    # Swap
    swap_free_gb: Optional[float] = None
    swap_in_rate: Optional[float] = None
    swap_out_rate: Optional[float] = None
    
    # Load
    load_avg_1min: Optional[float] = None
    load_avg_5min: Optional[float] = None
```

#### Step 4: Integrate into Report

Add OS metrics section to report:

```
OS-LEVEL PERFORMANCE METRICS (Performance Insights)
--------------------------------------------------------------------------------
CPU:
  Total Utilization:  45.2%
  User Space:         30.1%
  System/Kernel:      10.5%
  I/O Wait:           4.6%  ⚠️ High I/O wait indicates disk bottleneck

Memory:
  Free:               0.75 GB
  Active:             1.20 GB
  Cached:             0.80 GB

Disk I/O:
  Read IOPS:          150
  Write IOPS:         50
  Read Latency:       12.3 ms  ⚠️ High latency - slow disk reads
  Write Latency:      8.5 ms   ⚠️ High latency - slow disk writes
  Read Throughput:    1.2 MB/s
  Write Throughput:   0.5 MB/s
  Queue Depth:        2.5      ⚠️ Queries waiting for disk
  Disk Utilization:   75%

Temp Usage:
  Temp Blocks Read:   1,250    ⚠️ Queries spilling to disk
  Temp Blocks Written: 850     ⚠️ Consider increasing work_mem

Swap:
  Free Swap:          2.0 GB
  Swap In Rate:       0.0 MB/s
  Swap Out Rate:      0.0 MB/s

Load Average:
  1-minute:           2.5
  5-minute:           2.3
```

#### Step 5: Add Analysis Logic

Add to `analysis/analyzer.py`:

```python
def analyze_os_metrics(self, os_metrics: OSMetrics) -> List[Finding]:
    """Analyze OS-level metrics for issues."""
    findings = []
    
    # High I/O wait
    if os_metrics.cpu_wait and os_metrics.cpu_wait > 10:
        findings.append(Finding(
            severity='WARNING',
            message=f'High I/O wait: {os_metrics.cpu_wait:.1f}%',
            recommendation='Database is waiting for disk I/O. Check disk latency metrics.'
        ))
    
    # High disk latency
    if os_metrics.read_latency_ms and os_metrics.read_latency_ms > 10:
        findings.append(Finding(
            severity='WARNING',
            message=f'High read latency: {os_metrics.read_latency_ms:.1f} ms',
            recommendation='Slow disk reads. Consider faster storage (io1/io2) or optimize queries.'
        ))
    
    if os_metrics.write_latency_ms and os_metrics.write_latency_ms > 10:
        findings.append(Finding(
            severity='WARNING',
            message=f'High write latency: {os_metrics.write_latency_ms:.1f} ms',
            recommendation='Slow disk writes. Consider faster storage or batch commits.'
        ))
    
    # High queue depth
    if os_metrics.disk_queue_depth and os_metrics.disk_queue_depth > 2:
        findings.append(Finding(
            severity='WARNING',
            message=f'High disk queue depth: {os_metrics.disk_queue_depth:.1f}',
            recommendation='I/O bottleneck. Queries are queuing for disk access.'
        ))
    
    # Temp blocks (spilling to disk)
    if os_metrics.temp_blocks_written and os_metrics.temp_blocks_written > 1000:
        findings.append(Finding(
            severity='WARNING',
            message=f'High temp blocks written: {os_metrics.temp_blocks_written:.0f}',
            recommendation='Queries spilling to disk. Increase work_mem parameter.'
        ))
    
    # Swap usage
    if os_metrics.swap_out_rate and os_metrics.swap_out_rate > 0:
        findings.append(Finding(
            severity='CRITICAL',
            message='System is swapping to disk',
            recommendation='Memory pressure. Increase instance size or optimize memory usage.'
        ))
    
    return findings
```

---

## Fix for Execution Count Issue

### Option 1: Remove Execution Count (Recommended)

Since execution count is not available from PI API, we should:

1. Remove `execution_count` from the report
2. Show only what's available: Load (AAS)
3. Add note explaining limitation

```
Execution Metrics:
  Total Load:             1.234 AAS (Average Active Sessions)
  Average Load:           0.411 AAS per time bucket
  Time Buckets:           3 (5-minute intervals)
  
  Note: Execution count not available from Performance Insights API.
        Use AWS Console or query pg_stat_statements for execution count.
```

### Option 2: Fix the Calculation

If we keep execution count, fix the logic:

```python
# BEFORE (WRONG)
exec_count = len(partitions) if partitions else 1

# AFTER (CORRECT)
# Execution count is NOT available from PI API
# This is the number of time buckets, not executions
time_buckets = len(partitions) if partitions else 1
exec_count = None  # Not available
```

### Option 3: Add Note to Report

Add clarification:

```python
if query.execution_count == 1:
    note = " (Note: This is the number of time samples, not actual executions)"
else:
    note = ""

print(f"Execution Count:        {query.execution_count}{note}")
```

---

## Implementation Effort

### Phase 1: OS Disk I/O Metrics (HIGH PRIORITY)
**Effort:** 3-4 hours  
**Impact:** HIGH - Provides critical I/O performance data

Tasks:
1. Add `collect_os_metrics` method (1 hour)
2. Add `OSMetrics` dataclass (30 min)
3. Integrate into report formatter (1 hour)
4. Add analysis logic (1 hour)
5. Testing (30 min)

### Phase 2: Fix Execution Count (MEDIUM PRIORITY)
**Effort:** 1 hour  
**Impact:** MEDIUM - Fixes misleading data

Tasks:
1. Update calculation logic (15 min)
2. Update report formatter (15 min)
3. Add explanatory notes (15 min)
4. Testing (15 min)

### Phase 3: Temp Usage Analysis (MEDIUM PRIORITY)
**Effort:** 1 hour  
**Impact:** MEDIUM - Helps identify memory issues

Tasks:
1. Include temp metrics in OS collection (already done in Phase 1)
2. Add temp-specific analysis (30 min)
3. Add recommendations (30 min)

---

## Expected Benefits

### With OS Disk I/O Metrics

**Before:**
```
Query #1: CALL usp_sesr_cron_pseudo_hub_live_dashboard_generate_cache_0001()
Total Load: 1.234 AAS
Executions/sec: N/A
Average Latency: N/A
Read I/O Time: N/A
Write I/O Time: N/A
```

**After:**
```
Query #1: CALL usp_sesr_cron_pseudo_hub_live_dashboard_generate_cache_0001()
Total Load: 1.234 AAS (High load detected)

OS-Level Disk I/O (during query execution):
  Read Latency:       12.3 ms  ⚠️ HIGH - Slow disk reads
  Write Latency:      8.5 ms   ⚠️ HIGH - Slow disk writes
  Read IOPS:          150
  Write IOPS:         50
  Queue Depth:        2.5      ⚠️ I/O bottleneck
  
Analysis:
  ⚠️ High query load combined with high disk latency indicates I/O-bound query.
  ⚠️ Disk queue depth of 2.5 shows queries waiting for disk access.
  
Recommendations:
  1. Consider faster storage (io1/io2 instead of gp2/gp3)
  2. Add indexes to reduce disk reads
  3. Optimize query to reduce I/O operations
  4. Consider caching frequently accessed data
```

### Correlation Analysis

You can now correlate:
- High SQL load + High read latency = I/O-bound query
- High SQL load + Low I/O latency = CPU-bound query
- High temp blocks + High load = Memory-constrained query

---

## Recommendation

**Implement Phase 1 (OS Disk I/O Metrics) immediately.**

This will give you:
1. ✅ Read/Write latency (what you asked for)
2. ✅ IOPS and throughput
3. ✅ Queue depth (I/O bottleneck indicator)
4. ✅ Temp usage (memory pressure indicator)
5. ✅ Correlation with SQL load

This is the BEST alternative to per-query execution metrics since:
- It's available NOW (no database connection needed)
- It provides actionable insights
- It helps identify I/O vs CPU vs memory issues
- It correlates with SQL load to pinpoint problems

---

## Next Steps

1. **Review this plan** - Confirm this addresses your needs
2. **Prioritize phases** - Which phase should we implement first?
3. **Implement Phase 1** - Add OS disk I/O metrics collection
4. **Test with your instance** - Verify metrics are collected
5. **Enhance analysis** - Add correlation logic

Would you like me to implement Phase 1 now?
