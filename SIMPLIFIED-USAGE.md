# Simplified Usage Guide

## ✅ What We've Set Up

1. **config.yaml** - Contains your defaults (LT-DEV profile, ap-southeast-1 region)
2. **Shortcut scripts** - Simple batch files with consistent syntax
3. **Enhanced SQL Analysis** - Automatic collection of detailed SQL performance metrics

## 🚀 Consistent Command Syntax

All batch files now accept the same parameters as the main `rds-diag` command!

### List Instances
```bash
# Use defaults from config.yaml (LT-DEV, ap-southeast-1)
rds-list.bat

# Override profile
rds-list.bat --profile LT-SIT

# Override profile and region
rds-list.bat --profile LT-PRD --region us-east-1
```

### Diagnose an Instance
```bash
# Use defaults from config.yaml
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1

# With custom time range
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1 --time-range 24h

# Override profile
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1 --profile LT-SIT

# Full example with all options
rds-diagnose.bat --instance ielts-idv-dev-v1-clusterinstance1 --time-range 24h --profile LT-PRD --region ap-southeast-1
```

### Generate Report
```bash
# Use defaults (includes enhanced SQL metrics automatically)
rds-report.bat --instance ielts-idv-dev-v1-clusterinstance1 --output report.txt

# With custom time range and profile
rds-report.bat --instance ielts-idv-dev-v1-clusterinstance1 --output report.txt --time-range 24h --profile LT-SIT

# Generate management report (executive summary with SQL insights)
rds-report.bat --instance my-db --report-type management --output summary.txt

# Export as JSON for automation
rds-report.bat --instance my-db --format json --output metrics.json
```

### Check Permissions
```bash
# Use defaults
rds-check.bat

# Override profile
rds-check.bat --profile LT-PRD
```

## 🎯 Enhanced SQL Features (Automatic)

When Performance Insights is enabled, reports automatically include:

### What You Get
- **Detailed SQL Metrics**: CPU time, lock time, I/O, row statistics
- **Efficiency Analysis**: Rows examined vs. rows returned
- **Smart Recommendations**: INDEX, LOCK, CACHE, CPU optimization suggestions
- **Impact Estimates**: Potential performance improvements

### Example Output
```
SQL Query Performance
=====================

Query 1: SELECT * FROM orders WHERE customer_id = ?
  Total Time: 45,230 ms
  CPU Time: 38,450 ms (85%)
  Rows Examined: 1,250,000
  Rows Returned: 1,250
  Efficiency: 0.10% ⚠️ LOW

Recommendations:
  [CRITICAL] INDEX: Add index on customer_id
             Potential impact: 45,230 ms
```

### No Configuration Needed
Enhanced SQL metrics are collected automatically when:
1. Performance Insights is enabled on your RDS instance
2. You have `pi:GetResourceMetrics` IAM permission
3. `collect_enhanced_metrics: true` in config.yaml (default)

## 📝 Key Points

1. **Defaults from config.yaml**: If you don't specify `--profile` or `--region`, it uses values from config.yaml
2. **Consistent syntax**: All commands accept the same parameters as `rds-diag`
3. **Easy to override**: Just add `--profile` or `--region` when needed
4. **Automatic SQL analysis**: Enhanced metrics collected automatically when Performance Insights is enabled
5. **Graceful fallback**: If enhanced metrics unavailable, continues with basic metrics

## 🔧 Configuration (Optional)

To customize SQL metric collection, edit `config.yaml`:

```yaml
performance_insights:
  enabled: true                    # Enable/disable PI collection
  max_queries: 25                  # Number of queries to analyze
  collect_enhanced_metrics: true   # Collect detailed metrics
  collect_cpu_metrics: true        # Include CPU time
  collect_lock_metrics: true       # Include lock time
  collect_io_metrics: true         # Include I/O metrics
  collect_row_metrics: true        # Include row statistics
```

**Note:** These settings control LOCAL tool behavior only and do NOT modify AWS resources.

## 📚 More Information

- **Quick Reference**: See [QUICK-REFERENCE.md](QUICK-REFERENCE.md) for command cheat sheet
- **Detailed Examples**: See [EXAMPLES.md](EXAMPLES.md) for comprehensive examples
- **SQL Guide**: See [ENHANCED-SQL-GUIDE.md](ENHANCED-SQL-GUIDE.md) for SQL features
- **Full Documentation**: See [README.md](README.md) for complete documentation
