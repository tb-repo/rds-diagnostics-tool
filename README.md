# RDS Diagnostics and Reporting Tool

A command-line utility for diagnosing and reporting on AWS RDS instance performance across multiple accounts and environments. Built for Database Management (DBM) teams to quickly identify performance issues, analyze metrics, and generate reports for both technical and management audiences.

## Features

- 🔍 **Instance Discovery**: List all RDS instances across multiple AWS accounts and regions
- 📊 **Performance Metrics**: Collect CPU, memory, connections, IOPS, and storage metrics from CloudWatch
- 🔎 **Performance Insights**: Retrieve top SQL queries and wait events (when enabled)
- ⚡ **Enhanced SQL Metrics**: Collect detailed SQL performance data including CPU time, lock time, I/O metrics, and row statistics
- 🎯 **Smart SQL Recommendations**: Automatic detection of indexing opportunities, lock contention, caching candidates, and CPU-intensive queries
- 📈 **Intelligent Analysis**: Identify threshold violations, calculate trends, and assess severity
- 📝 **Flexible Reporting**: Generate technical or management reports in text or JSON format
- ⚙️ **Configurable Thresholds**: Customize alert thresholds via configuration files
- 🔐 **Multi-Account Support**: Seamlessly work across multiple AWS accounts using profiles

## Installation

### Prerequisites

- Python 3.8 or higher
- AWS CLI configured with appropriate credentials
- Required IAM permissions (see [IAM Permissions](#iam-permissions))

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd rds-diagnostics-tool

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
rds-diag version
# Output: RDS Diagnostics Tool v0.1.0
```

## Quick Start

### 1. List RDS Instances

```bash
# List instances in default region (ap-southeast-1)
rds-diag list

# List instances in a specific account and region
rds-diag list --profile lt-prd --region us-east-1
```

### 2. Run Diagnostics

```bash
# Run diagnostics with default 1-hour time range
rds-diag diagnose --instance my-db-instance

# Run diagnostics for the last 24 hours
rds-diag diagnose --instance my-db --time-range 24h --profile lt-prd

# Run with verbose output
rds-diag diagnose -i my-db -t 7d --verbose
```

### 3. Generate Reports

```bash
# Generate technical report to stdout
rds-diag report --instance my-db-instance

# Generate management report in JSON format
rds-diag report -i my-db --report-type management --format json

# Save technical report to file
rds-diag report -i my-db -t 24h -o report.txt

# Generate management report for 7 days and save as JSON
rds-diag report -i my-db -t 7d --report-type management -f json -o report.json
```

## Commands

### Global Options

Available for all commands:

- `--profile, -p`: AWS CLI profile name
- `--region, -r`: AWS region (default: ap-southeast-1)
- `--config, -c`: Path to configuration file
- `--verbose, -v`: Enable verbose output with detailed progress information
- `--help`: Display help information

### `list` - List RDS Instances

List all RDS instances in the configured region.

```bash
rds-diag list [OPTIONS]
```

**Examples:**
```bash
# List instances using default profile and region
rds-diag list

# List instances in a specific account and region
rds-diag list --profile lt-prd --region us-east-1
```

### `diagnose` - Run Diagnostics

Run diagnostics on a specific RDS instance and display a summary.

```bash
rds-diag diagnose --instance INSTANCE_ID [OPTIONS]
```

**Options:**
- `--instance, -i`: RDS instance identifier (required)
- `--time-range, -t`: Time range for metrics (e.g., "1h", "24h", "7d"). Default: 1h

**Examples:**
```bash
# Run diagnostics with default 1-hour time range
rds-diag diagnose --instance my-db-instance

# Run diagnostics for the last 24 hours
rds-diag diagnose --instance my-db --time-range 24h --profile lt-prd

# Run diagnostics for the last 7 days with verbose output
rds-diag diagnose -i my-db -t 7d --verbose
```

### `report` - Generate Reports

Generate formatted reports for an RDS instance.

```bash
rds-diag report --instance INSTANCE_ID [OPTIONS]
```

**Options:**
- `--instance, -i`: RDS instance identifier (required)
- `--time-range, -t`: Time range for metrics (default: 1h)
- `--report-type`: Type of report (technical, management). Default: technical
- `--format, -f`: Output format (text, json). Default: text
- `--output, -o`: Output file path (default: display to stdout)
- `--force`: Overwrite output file without confirmation

**Report Types:**
- **Technical**: Detailed metrics, SQL queries, wait events, and raw data for in-depth analysis
- **Management**: Executive summary with key findings, severity assessment, and recommendations

**Examples:**
```bash
# Generate technical report to stdout
rds-diag report --instance my-db-instance

# Generate management report in JSON format
rds-diag report -i my-db --report-type management --format json

# Save technical report to file
rds-diag report -i my-db -t 24h -o report.txt

# Generate management report for 7 days and save as JSON
rds-diag report -i my-db -t 7d --report-type management -f json -o report.json
```

### `version` - Display Version

Display version information.

```bash
rds-diag version
```

## Configuration

### Configuration File

Create a configuration file to customize default settings and thresholds.

**Default Location:** `~/.rds-diagnostics/config.yaml`

**Example Configuration:**

```yaml
# AWS Profile (optional)
aws_profile: lt-prd

# Default AWS Region
default_region: ap-southeast-1

# Default Time Range
default_time_range: 1h

# Default Output Format
output_format: text

# Performance Insights Configuration
performance_insights:
  enabled: true
  max_queries: 25
  collect_enhanced_metrics: true
  fallback_on_error: true
  collect_cpu_metrics: true
  collect_lock_metrics: true
  collect_io_metrics: true
  collect_row_metrics: true

# Metric Thresholds
thresholds:
  cpu:
    warning: 70.0
    critical: 90.0
  memory:
    warning: 80.0
    critical: 95.0
  connections:
    warning: 80
    critical: 95
  iops:
    warning: 80.0
    critical: 95.0
  storage:
    warning: 80.0
    critical: 90.0
```

See `config.example.yaml` for a complete example with all options.

### Performance Insights Configuration

The tool can collect enhanced SQL metrics when Performance Insights is enabled:

- `enabled`: Enable/disable Performance Insights collection (default: true)
- `max_queries`: Maximum number of SQL queries to collect (1-100, default: 25)
- `collect_enhanced_metrics`: Collect detailed metrics beyond basic query stats (default: true)
- `fallback_on_error`: Continue with basic metrics if enhanced collection fails (default: true)
- `collect_cpu_metrics`: Collect CPU time metrics (default: true)
- `collect_lock_metrics`: Collect lock time metrics (default: true)
- `collect_io_metrics`: Collect I/O metrics (default: true)
- `collect_row_metrics`: Collect row statistics (default: true)

**Note:** These settings control LOCAL tool behavior only and do NOT modify AWS resources.

### Using Configuration Files

```bash
# Use default config location (~/.rds-diagnostics/config.yaml)
rds-diag list

# Specify custom config file
rds-diag --config ./my-config.yaml list

# Override config settings from command line
rds-diag --config config.yaml --region us-east-1 list
```

### Configuration Precedence

Settings are applied in the following order (later overrides earlier):
1. Default values
2. Configuration file
3. Command-line arguments

## IAM Permissions

The tool requires the following IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:GetMetricData",
        "pi:DescribeDimensionKeys",
        "pi:GetResourceMetrics"
      ],
      "Resource": "*"
    }
  ]
}
```

### Permission Details

**Required for Basic Functionality:**
- `rds:DescribeDBInstances` - List and describe RDS instances
- `rds:DescribeDBClusters` - List and describe RDS clusters
- `cloudwatch:GetMetricStatistics` - Retrieve CloudWatch metrics
- `cloudwatch:GetMetricData` - Retrieve CloudWatch metric data

**Required for Performance Insights (Optional but Recommended):**
- `pi:DescribeDimensionKeys` - Identify top SQL queries and wait events
- `pi:GetResourceMetrics` - Retrieve detailed SQL performance metrics (CPU time, lock time, I/O, row statistics)

**Note:** The tool will work without Performance Insights permissions but will skip SQL query analysis and enhanced metrics collection. For full functionality including SQL recommendations, both `pi:DescribeDimensionKeys` and `pi:GetResourceMetrics` are required.

### Creating an IAM Policy

1. Go to AWS IAM Console
2. Create a new policy
3. Use the JSON above
4. Name it `RDSDiagnosticsToolPolicy`
5. Attach to your IAM user or role

## Troubleshooting

### Authentication Errors

**Error:** `Unable to locate credentials`

**Solution:**
```bash
# Configure AWS CLI
aws configure --profile your-profile

# Or use AWS SSO
aws sso login --profile your-profile
```

### Permission Errors

**Error:** `User is not authorized to perform: rds:DescribeDBInstances`

**Solution:** Ensure your IAM user/role has the required permissions (see [IAM Permissions](#iam-permissions))

### Instance Not Found

**Error:** `DBInstance not found`

**Solution:**
```bash
# List available instances to verify the instance ID
rds-diag list --profile your-profile --region your-region

# Ensure you're using the correct region
rds-diag diagnose --instance your-instance --region correct-region
```

### Rate Limiting

**Error:** `Rate exceeded` or `Throttling`

**Solution:** The tool automatically retries with exponential backoff. If the issue persists:
- Reduce the time range (use shorter periods like "1h" instead of "7d")
- Wait a few minutes before retrying
- Check if other processes are making AWS API calls

### Performance Insights Not Available

**Message:** `Performance Insights not enabled or no query data available`

**Solution:** This is informational. Performance Insights must be enabled on the RDS instance to retrieve SQL query data. The tool will continue with CloudWatch metrics only.

To enable Performance Insights:
1. Go to RDS Console
2. Select your instance
3. Modify instance settings
4. Enable Performance Insights
5. Wait for the modification to complete

**Note:** Enhanced SQL metrics require both Performance Insights to be enabled AND the `pi:GetResourceMetrics` IAM permission.

## Enhanced SQL Features

### What's New

The tool now collects detailed SQL performance metrics when Performance Insights is enabled:

**Enhanced Metrics:**
- Execution rate (queries per second)
- CPU time per query
- Lock time and contention
- Rows examined vs. rows returned (efficiency ratio)
- I/O metrics (read/write bytes)

**Smart Recommendations:**
- **INDEX**: Identifies queries with low efficiency ratios that may benefit from indexing
- **LOCK**: Detects queries with significant lock contention
- **CACHE**: Suggests high-frequency, fast queries suitable for caching
- **CPU**: Flags CPU-intensive queries that may need optimization

### Example Output

**Technical Report with Enhanced Metrics:**
```
SQL Query Performance
=====================

Query 1 (ID: 0x1A2B3C4D5E6F7890)
-----------------------------------
SQL: SELECT * FROM orders WHERE customer_id = ? AND status = 'pending'
Total Execution Time: 45,230.50 ms
Average Execution Time: 125.30 ms
Execution Count: 361

Execution Metrics:
  Executions/sec: 0.50 calls/sec
  Total Time: 45,230.50 ms

Resource Metrics:
  CPU Time: 38,450.20 ms (85.0%)
  Lock Time: 1,250.30 ms (2.8%)

Row Metrics:
  Rows Examined: 1,250,000
  Rows Returned: 1,250
  Efficiency Ratio: 0.10% ⚠️ LOW EFFICIENCY

I/O Metrics:
  Read I/O: 512.50 MB
  Write I/O: 0.00 MB

Recommendations:
  [CRITICAL] INDEX: Query examines 1,250,000 rows but returns only 1,250 (0.10% efficiency).
             Consider adding an index on customer_id and status columns.
             Potential impact: 45,230.50 ms total execution time
```

**Management Report with SQL Summary:**
```
SQL Performance Summary
=======================
Analyzed 25 queries with 3 performance issues identified

Top Issues:
1. Query 0x1A2B3C4D: Low efficiency (0.10%) - 1.25M rows examined
   SQL: SELECT * FROM orders WHERE customer_id = ?...
   Recommendation: Add index on customer_id, status

2. Query 0x9F8E7D6C: High lock contention (45.2%)
   SQL: UPDATE inventory SET quantity = quantity - ?...
   Recommendation: Review transaction isolation level

3. Query 0x5B4A3C2D: CPU-intensive (92.5% CPU time)
   SQL: SELECT * FROM products WHERE description LIKE...
   Recommendation: Optimize query or consider full-text search

Key Recommendations:
- INDEX: 5 queries could benefit from indexing
- LOCK: 2 queries experiencing lock contention
- CPU: 3 queries are CPU-intensive
```

For detailed usage examples, see [ENHANCED-SQL-GUIDE.md](ENHANCED-SQL-GUIDE.md) and [QUICK-REFERENCE.md](QUICK-REFERENCE.md).

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_config.py
```

### Code Formatting

```bash
# Format code with black
black .

# Lint with ruff
ruff check .
```

## Architecture

The tool follows a modular architecture:

```
cli/                    # Command-line interface
core/                   # Core application logic
  ├── app.py           # Main application orchestrator
  ├── config.py        # Configuration management
  └── models.py        # Data models
aws/                    # AWS service clients
  └── clients.py       # RDS, CloudWatch, Performance Insights clients
collectors/             # Data collection modules
  ├── instance_info.py # Instance information collector
  ├── metrics.py       # CloudWatch metrics collector
  └── performance_insights.py  # Performance Insights collector
analysis/               # Analysis engine
  └── analyzer.py      # Diagnostic analyzer
reporting/              # Reporting engine
  ├── formatters.py    # Report formatters
  └── generator.py     # Report generator
tests/                  # Test suite
  ├── unit/            # Unit tests
  ├── property/        # Property-based tests
  └── integration/     # Integration tests
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Format code with black
6. Submit a pull request

## License

[Add your license here]

## Support

For issues, questions, or contributions, please [open an issue](link-to-issues) or contact the development team.

---

**Version:** 0.1.0  
**Last Updated:** 2024
