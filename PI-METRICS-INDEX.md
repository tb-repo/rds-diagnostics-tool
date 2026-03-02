# Performance Insights Metrics - Documentation Index

## 📚 Complete Documentation Set

This is your complete guide to understanding what Performance Insights metrics are available for Aurora PostgreSQL 17.5.

---

## 🚀 Quick Start (5 minutes)

1. **Read:** [PI-METRICS-VISUAL.txt](PI-METRICS-VISUAL.txt) - Visual guide showing what you can and cannot get
2. **Read:** [PI-METRICS-SUMMARY.txt](PI-METRICS-SUMMARY.txt) - Quick reference with all metrics listed
3. **Run:** `list-pi-metrics.bat` - Test your instance to verify available metrics

---

## 📖 Documentation Files

### 1. README-PI-METRICS.md ⭐ START HERE
**Purpose:** Complete overview and guide  
**Best for:** Understanding the big picture  
**Contents:**
- What PI API provides vs. what it doesn't
- Why AWS Console shows more data
- Visual architecture diagrams
- Next steps and recommendations
- FAQ

**Read this if:** You want a comprehensive understanding of PI metrics

---

### 2. PI-METRICS-VISUAL.txt 🎨
**Purpose:** Visual guide with ASCII diagrams  
**Best for:** Quick visual understanding  
**Contents:**
- Visual representation of available metrics
- Data flow comparison (Your Tool vs AWS Console)
- Solution options with pros/cons
- Testing instructions

**Read this if:** You prefer visual explanations

---

### 3. PI-METRICS-SUMMARY.txt 📋
**Purpose:** Quick reference guide  
**Best for:** Looking up specific metrics  
**Contents:**
- Complete list of available metrics
- Complete list of unavailable metrics
- Metric categories (CPU, Memory, Disk, Network, etc.)
- Workarounds for missing metrics
- Testing instructions

**Read this if:** You need to quickly check if a specific metric is available

---

### 4. PI-METRICS-REFERENCE.md 📚
**Purpose:** Detailed technical documentation  
**Best for:** Implementation and coding  
**Contents:**
- Detailed metric descriptions
- Code examples for each metric type
- API call examples
- Parameter explanations
- Return value structures
- 74 OS-level metrics catalog

**Read this if:** You're implementing code to collect metrics

---

### 5. PI-METRICS-COMPARISON.md ⚖️
**Purpose:** Side-by-side comparison  
**Best for:** Understanding limitations  
**Contents:**
- AWS Console vs PI API comparison tables
- Feature availability matrix
- Data source identification
- Metric-by-metric comparison

**Read this if:** You want to understand exactly what's different between Console and API

---

### 6. AURORA-POSTGRESQL-LIMITATIONS.md 🔍
**Purpose:** Technical analysis of limitations  
**Best for:** Deep technical understanding  
**Contents:**
- API test results
- Root cause analysis
- Aurora MySQL vs PostgreSQL comparison
- Why metrics are missing
- Technical workarounds

**Read this if:** You want to understand WHY certain metrics aren't available

---

### 7. ALTERNATIVE-OPTIONS.md 💡
**Purpose:** Solutions for getting missing metrics  
**Best for:** Planning next steps  
**Contents:**
- 6 different approaches
- Detailed pros/cons for each
- Implementation effort estimates
- Code examples
- Recommendations

**Read this if:** You want to get the missing metrics (latency, I/O time, etc.)

---

## 🧪 Testing Scripts

### list_all_pi_metrics.py
**Purpose:** Comprehensive test of available metrics  
**What it does:**
- Lists all available dimension groups
- Lists all available resource metrics
- Tests each dimension group
- Shows sample data
- Provides summary

**Run with:**
```bash
python list_all_pi_metrics.py
```

### list-pi-metrics.bat
**Purpose:** Windows batch file to run the test  
**What it does:**
- Runs list_all_pi_metrics.py
- Displays results
- Pauses for review

**Run with:**
```bash
list-pi-metrics.bat
```

---

## 📊 What You'll Learn

### Available Metrics ✅

**SQL Query Identification:**
- Which queries are running
- SQL query text
- Load contribution (AAS)

**Top Users:**
- Database usernames
- Load per user
- Load percentage

**Wait Events:**
- CPU, I/O, Lock waits
- Load per wait event

**Database Load:**
- db.load.avg, db.load.max, db.load.min

**OS Metrics (74 total):**
- CPU utilization (total, user, system, wait)
- Memory (free, active, cached, buffers)
- Disk I/O (IOPS, latency, throughput)
- Network (receive/transmit)
- Swap usage
- Load average

### Unavailable Metrics ❌

**SQL Execution:**
- Calls/sec
- Average latency
- Total execution time
- Execution count

**SQL I/O:**
- Read time (ms/call)
- Write time (ms/call)
- Blocks read/written
- Buffer cache hits

**SQL Rows:**
- Rows examined
- Rows returned
- Rows/sec
- Efficiency ratio

**Database Grouping:**
- Top databases
- Per-database metrics

---

## 🎯 Use Cases

### Use Case 1: "Which queries are consuming resources?"
**Solution:** ✅ PI API provides this  
**Read:** PI-METRICS-REFERENCE.md → Section "Identify Top SQL Queries by Load"

### Use Case 2: "How many times is this query executing?"
**Solution:** ❌ PI API doesn't provide this  
**Read:** ALTERNATIVE-OPTIONS.md → Option 1 (CloudWatch) or Option 6 (Direct Connection)

### Use Case 3: "What's the average latency of this query?"
**Solution:** ❌ PI API doesn't provide this  
**Read:** ALTERNATIVE-OPTIONS.md → Option 1 (CloudWatch) or Option 6 (Direct Connection)

### Use Case 4: "Is the database CPU-bound or I/O-bound?"
**Solution:** ✅ PI API provides this  
**Read:** PI-METRICS-REFERENCE.md → Section "Analyze Wait Events"

### Use Case 5: "Which users are generating the most load?"
**Solution:** ✅ PI API provides this  
**Read:** PI-METRICS-REFERENCE.md → Section "Identify Top Users by Load"

### Use Case 6: "What's the disk I/O latency?"
**Solution:** ✅ PI API provides this (OS metrics)  
**Read:** PI-METRICS-REFERENCE.md → Section "OS-Level Metrics" → "Disk I/O Metrics"

---

## 🔄 Reading Order

### For Quick Understanding (15 minutes)
1. PI-METRICS-VISUAL.txt (5 min)
2. PI-METRICS-SUMMARY.txt (10 min)

### For Complete Understanding (45 minutes)
1. README-PI-METRICS.md (15 min)
2. PI-METRICS-COMPARISON.md (15 min)
3. ALTERNATIVE-OPTIONS.md (15 min)

### For Implementation (2 hours)
1. README-PI-METRICS.md (15 min)
2. PI-METRICS-REFERENCE.md (45 min)
3. AURORA-POSTGRESQL-LIMITATIONS.md (30 min)
4. ALTERNATIVE-OPTIONS.md (30 min)

### For Decision Making (30 minutes)
1. PI-METRICS-SUMMARY.txt (10 min)
2. ALTERNATIVE-OPTIONS.md (20 min)

---

## 🎓 Key Takeaways

### What PI API Provides
- **Identification:** Which queries, users, wait events
- **Load:** How much each contributes to database load
- **OS Metrics:** System-level performance (CPU, memory, disk, network)

### What PI API Doesn't Provide
- **Execution:** How many times, how fast
- **I/O per Query:** Read/write time per query
- **Rows:** How many rows processed
- **Databases:** Top databases

### Why the Difference
- AWS Console has direct access to PostgreSQL internal tables (`pg_stat_statements`)
- PI API is database-agnostic and doesn't expose engine-specific tables
- This is by design, not a bug

### Solutions
1. **Accept limitations** - Use Console for SQL details
2. **Enhanced CloudWatch** - Get database-level latency (2-3 hours)
3. **Direct PostgreSQL** - Get all metrics (1-2 days)

---

## 📞 Support

### Questions About Metrics
- Check: PI-METRICS-SUMMARY.txt
- Read: PI-METRICS-REFERENCE.md

### Questions About Limitations
- Read: AURORA-POSTGRESQL-LIMITATIONS.md
- Read: PI-METRICS-COMPARISON.md

### Questions About Solutions
- Read: ALTERNATIVE-OPTIONS.md
- Read: README-PI-METRICS.md → "What You Can Do"

### Testing
- Run: `list-pi-metrics.bat`
- Review: Output shows exactly what's available for your instance

---

## 🔗 Related Files

### Configuration
- `config.yaml` - Tool configuration
- `config.example.yaml` - Configuration template

### Code
- `collectors/performance_insights.py` - PI data collection
- `aws/clients.py` - AWS client wrappers
- `core/models.py` - Data models

### Reports
- `test-report-fixed.txt` - Latest generated report
- `EXAMPLES.md` - Usage examples

---

## 📅 Last Updated

**Date:** February 27, 2026  
**Tested With:** Aurora PostgreSQL 17.5  
**Instance:** ielts-ses-sit-v1-clusterinstance1  
**Status:** Comprehensive testing completed

---

## ✅ Checklist

Before implementing changes, make sure you've:

- [ ] Read README-PI-METRICS.md
- [ ] Reviewed PI-METRICS-SUMMARY.txt
- [ ] Run list-pi-metrics.bat to verify your instance
- [ ] Reviewed ALTERNATIVE-OPTIONS.md
- [ ] Decided on approach (Accept / CloudWatch / Direct Connection)
- [ ] Understood limitations (AURORA-POSTGRESQL-LIMITATIONS.md)

---

## 🎯 Next Steps

1. **Understand what's available:**
   - Read: README-PI-METRICS.md
   - Run: list-pi-metrics.bat

2. **Decide on approach:**
   - Review: ALTERNATIVE-OPTIONS.md
   - Choose: Option A, B, or C

3. **Implement solution:**
   - Option A: No changes needed
   - Option B: 2-3 hours (Enhanced CloudWatch)
   - Option C: 1-2 days (Direct PostgreSQL)

---

**Happy metric hunting! 🚀**
