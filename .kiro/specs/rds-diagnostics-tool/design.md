# Design Document: RDS Diagnostics and Reporting Tool

## Overview

The RDS Diagnostics and Reporting Tool is a Python-based command-line application that provides DBM teams with rapid RDS performance diagnostics and flexible reporting capabilities. The tool leverages AWS SDK (boto3) to interact with RDS, CloudWatch, and Performance Insights APIs, presenting data in formats suitable for both technical troubleshooting and management communication.

The design emphasizes modularity, testability, and clear separation between data collection, analysis, and presentation layers. The tool operates as a stateless CLI application that can be easily integrated into incident response workflows and automation pipelines.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Interface Layer                      │
│  (Argument parsing, command routing, user interaction)       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Application Core Layer                     │
│  (Orchestration, configuration, error handling)              │
└─────┬──────────────────┬──────────────────┬─────────────────┘
      │                  │                  │
┌─────▼─────┐   ┌────────▼────────┐   ┌────▼──────────┐
│   Data    │   │    Analysis     │   │   Reporting   │
│ Collection│   │     Engine      │   │    Engine     │
│  Module   │   │                 │   │               │
└─────┬─────┘   └────────┬────────┘   └────┬──────────┘
      │                  │                  │
┌─────▼──────────────────▼──────────────────▼─────────────────┐
│                    AWS Service Clients                       │
│         (RDS, CloudWatch, Performance Insights)              │
└──────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

1. **CLI Interface Layer**: Handles user input, command parsing, and output display
2. **Application Core**: Orchestrates workflow, manages configuration, handles cross-cutting concerns
3. **Data Collection Module**: Retrieves metrics and data from AWS services
4. **Analysis Engine**: Processes raw data, identifies issues, calculates trends
5. **Reporting Engine**: Formats data for different audiences and output formats
6. **AWS Service Clients**: Thin wrappers around boto3 for testability and error handling

## Components and Interfaces

### 1. CLI Interface (`cli.py`)

**Purpose**: Entry point for the application, handles command-line argument parsing and user interaction.

**Key Classes**:
- `RDSToolCLI`: Main CLI controller

**Key Methods**:
```python
class RDSToolCLI:
    def parse_arguments(args: List[str]) -> argparse.Namespace
    def execute_command(parsed_args: argparse.Namespace) -> int
    def display_output(report: Report, format: OutputFormat) -> None
```

**Commands**:
- `list`: List RDS instances in an account/region
- `diagnose`: Run diagnostics on a specific RDS instance
- `report`: Generate a formatted report (technical or management)

**Key Arguments**:
- `--profile, -p`: AWS CLI profile name
- `--region, -r`: AWS region (default: ap-southeast-1)
- `--instance, -i`: RDS instance identifier
- `--time-range, -t`: Time range for metrics (e.g., "1h", "24h", "7d")
- `--format, -f`: Output format (text, json)
- `--output, -o`: Output file path
- `--report-type`: Report type (technical, management)
- `--verbose, -v`: Verbose output
- `--config, -c`: Configuration file path

### 2. Application Core (`core/app.py`)

**Purpose**: Orchestrates the main application workflow and manages dependencies.

**Key Classes**:
```python
class RDSDiagnosticsApp:
    def __init__(config: Configuration, aws_clients: AWSClientFactory)
    def list_instances(region: str) -> List[RDSInstanceInfo]
    def run_diagnostics(instance_id: str, time_range: TimeRange) -> DiagnosticData
    def generate_report(diagnostic_data: DiagnosticData, report_type: ReportType) -> Report
```

### 3. Configuration Management (`core/config.py`)

**Purpose**: Manages application configuration from files, environment, and command-line overrides.

**Key Classes**:
```python
class Configuration:
    aws_profile: str
    default_region: str
    default_time_range: TimeRange
    metric_thresholds: MetricThresholds
    output_format: OutputFormat
    
    @staticmethod
    def load_from_file(path: str) -> Configuration
    
    @staticmethod
    def load_defaults() -> Configuration
    
    def merge_with_cli_args(args: argparse.Namespace) -> Configuration

class MetricThresholds:
    cpu_warning: float = 70.0
    cpu_critical: float = 90.0
    memory_warning: float = 80.0
    memory_critical: float = 95.0
    connections_warning: int = 80  # percentage of max
    connections_critical: int = 95
    iops_warning: float = 80.0  # percentage of provisioned
    iops_critical: float = 95.0
    storage_warning: float = 80.0  # percentage used
    storage_critical: float = 90.0
```

### 4. AWS Service Clients (`aws/clients.py`)

**Purpose**: Provides abstraction over boto3 clients with error handling and retry logic.

**Key Classes**:
```python
class AWSClientFactory:
    def __init__(profile: str, region: str)
    def create_rds_client() -> RDSClient
    def create_cloudwatch_client() -> CloudWatchClient
    def create_performance_insights_client() -> PerformanceInsightsClient

class RDSClient:
    def list_instances() -> List[Dict]
    def describe_instance(instance_id: str) -> Dict
    def get_instance_resource_id(instance_id: str) -> str

class CloudWatchClient:
    def get_metric_statistics(
        namespace: str,
        metric_name: str,
        dimensions: List[Dict],
        start_time: datetime,
        end_time: datetime,
        period: int,
        statistics: List[str]
    ) -> List[MetricDataPoint]

class PerformanceInsightsClient:
    def get_resource_metrics(
        resource_id: str,
        metric_queries: List[Dict],
        start_time: datetime,
        end_time: datetime
    ) -> Dict
    
    def describe_dimension_keys(
        resource_id: str,
        group_by: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]
```

### 5. Data Collection Module (`collectors/`)

**Purpose**: Retrieves and structures data from AWS services.

**Key Classes**:
```python
class MetricsCollector:
    def __init__(cloudwatch_client: CloudWatchClient, rds_client: RDSClient)
    
    def collect_cpu_metrics(instance_id: str, time_range: TimeRange) -> MetricSeries
    def collect_memory_metrics(instance_id: str, time_range: TimeRange) -> MetricSeries
    def collect_connection_metrics(instance_id: str, time_range: TimeRange) -> MetricSeries
    def collect_iops_metrics(instance_id: str, time_range: TimeRange) -> IOPSMetrics
    def collect_storage_metrics(instance_id: str, time_range: TimeRange) -> StorageMetrics
    def collect_all_metrics(instance_id: str, time_range: TimeRange) -> CloudWatchMetrics

class PerformanceInsightsCollector:
    def __init__(pi_client: PerformanceInsightsClient, rds_client: RDSClient)
    
    def collect_top_sql_queries(
        instance_id: str,
        time_range: TimeRange,
        limit: int = 10
    ) -> List[SQLQuery]
    
    def collect_wait_events(
        instance_id: str,
        time_range: TimeRange
    ) -> List[WaitEvent]
    
    def is_performance_insights_enabled(instance_id: str) -> bool

class InstanceInfoCollector:
    def __init__(rds_client: RDSClient)
    
    def get_instance_details(instance_id: str) -> RDSInstanceInfo
    def list_all_instances() -> List[RDSInstanceInfo]
```

### 6. Analysis Engine (`analysis/analyzer.py`)

**Purpose**: Processes collected data to identify issues, calculate trends, and assess severity.

**Key Classes**:
```python
class DiagnosticAnalyzer:
    def __init__(thresholds: MetricThresholds)
    
    def analyze_metrics(metrics: CloudWatchMetrics) -> MetricAnalysis
    def identify_threshold_violations(metrics: CloudWatchMetrics) -> List[Violation]
    def calculate_trends(metrics: CloudWatchMetrics) -> TrendAnalysis
    def assess_overall_severity(analysis: MetricAnalysis) -> Severity
    def generate_recommendations(analysis: MetricAnalysis, queries: List[SQLQuery]) -> List[str]

class QueryAnalyzer:
    def rank_queries_by_impact(queries: List[SQLQuery]) -> List[RankedQuery]
    def identify_problematic_queries(queries: List[SQLQuery], threshold: float) -> List[SQLQuery]
```

### 7. Reporting Engine (`reporting/`)

**Purpose**: Formats diagnostic data into reports for different audiences.

**Key Classes**:
```python
class ReportGenerator:
    def generate_report(
        diagnostic_data: DiagnosticData,
        report_type: ReportType
    ) -> Report

class TechnicalReportFormatter:
    def format(diagnostic_data: DiagnosticData) -> str
    def format_json(diagnostic_data: DiagnosticData) -> str

class ManagementReportFormatter:
    def format(diagnostic_data: DiagnosticData) -> str
    def create_executive_summary(analysis: MetricAnalysis) -> str
    def format_key_findings(violations: List[Violation]) -> str
    def format_recommendations(recommendations: List[str]) -> str
```

## Data Models

### Core Data Structures

```python
@dataclass
class TimeRange:
    start: datetime
    end: datetime
    
    @staticmethod
    def from_duration(duration_str: str) -> TimeRange
    # Parses "1h", "24h", "7d" etc.

@dataclass
class RDSInstanceInfo:
    instance_id: str
    resource_id: str
    engine: str
    engine_version: str
    instance_class: str
    status: str
    storage_type: str
    allocated_storage: int
    max_connections: int
    availability_zone: str

@dataclass
class MetricDataPoint:
    timestamp: datetime
    value: float
    unit: str

@dataclass
class MetricSeries:
    metric_name: str
    data_points: List[MetricDataPoint]
    unit: str
    
    def get_average() -> float
    def get_max() -> float
    def get_min() -> float
    def get_latest() -> Optional[MetricDataPoint]

@dataclass
class IOPSMetrics:
    read_iops: MetricSeries
    write_iops: MetricSeries
    
    def get_total_iops_series() -> MetricSeries

@dataclass
class StorageMetrics:
    free_storage: MetricSeries
    used_storage: MetricSeries
    total_storage: int
    
    def get_usage_percentage() -> float

@dataclass
class CloudWatchMetrics:
    instance_info: RDSInstanceInfo
    cpu_utilization: MetricSeries
    freeable_memory: MetricSeries
    database_connections: MetricSeries
    iops: IOPSMetrics
    storage: StorageMetrics
    collection_time: datetime

@dataclass
class SQLQuery:
    query_id: str
    query_text: str
    total_execution_time: float
    average_execution_time: float
    execution_count: int
    rows_affected: Optional[int]
    wait_events: List[str]

@dataclass
class WaitEvent:
    event_name: str
    total_wait_time: float
    wait_count: int

@dataclass
class Violation:
    metric_name: str
    severity: Severity
    current_value: float
    threshold_value: float
    timestamp: datetime
    message: str

@dataclass
class TrendAnalysis:
    metric_name: str
    trend: Trend  # IMPROVING, DEGRADING, STABLE
    change_percentage: float
    description: str

@dataclass
class MetricAnalysis:
    violations: List[Violation]
    trends: List[TrendAnalysis]
    overall_severity: Severity
    summary: str

@dataclass
class DiagnosticData:
    instance_info: RDSInstanceInfo
    cloudwatch_metrics: CloudWatchMetrics
    performance_insights_queries: Optional[List[SQLQuery]]
    wait_events: Optional[List[WaitEvent]]
    analysis: MetricAnalysis
    recommendations: List[str]
    collection_timestamp: datetime

@dataclass
class Report:
    report_type: ReportType
    content: str
    format: OutputFormat
    generated_at: datetime

# Enums
class Severity(Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"

class Trend(Enum):
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"

class ReportType(Enum):
    TECHNICAL = "technical"
    MANAGEMENT = "management"

class OutputFormat(Enum):
    TEXT = "text"
    JSON = "json"
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I've identified several areas of redundancy:

1. **Metrics Collection (2.1-2.5)**: All five criteria test that specific metrics are retrieved. These can be combined into a single property that verifies all required metrics are present.

2. **Rate Limiting (2.8 and 8.5)**: Both test rate limit handling with retry logic. These are identical and can be represented by a single property.

3. **Report Content Requirements (4.1-4.3, 4.7)**: Multiple criteria test that specific data is included in technical reports. These can be combined into one comprehensive property.

4. **JSON Output Validation (4.5 and 9.7)**: Both test that JSON output is valid and parseable. One property covers this.

5. **Profile Support (6.1 and 6.4)**: 6.4 is a general statement that's covered by testing 6.1 with various profiles.

6. **Configuration Loading (7.1, 7.4, 7.5)**: All test configuration loading from files. Can be combined into one property about configuration persistence.

7. **Performance Insights Data Fields (3.2-3.4, 3.7)**: Multiple criteria test that specific fields are included in PI data. Can be combined.

The refined property set eliminates these redundancies while maintaining complete coverage of testable requirements.

### Correctness Properties

**Property 1: Instance Discovery Completeness**
*For any* valid AWS profile and region, when listing RDS instances, all instances in that region should be returned with complete information (instance ID, engine type, status).
**Validates: Requirements 1.1, 1.2**

**Property 2: Instance Validation**
*For any* instance identifier, the validation function should return true if and only if the instance exists in the specified account and region.
**Validates: Requirements 1.3, 1.4**

**Property 3: Region Support**
*For any* valid AWS region, the tool should successfully query RDS instances in that region when specified.
**Validates: Requirements 1.5**

**Property 4: Complete Metrics Collection**
*For any* RDS instance and time range, when collecting CloudWatch metrics, the result should include all required metrics: CPU utilization, freeable memory, database connections, read IOPS, write IOPS, and storage metrics.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

**Property 5: Time Range Filtering**
*For any* specified time range, all collected metrics should have timestamps within that time range (inclusive).
**Validates: Requirements 2.6, 3.6**

**Property 6: Retry with Exponential Backoff**
*For any* API call that encounters rate limiting or transient failures, the retry delays should follow exponential backoff pattern (each retry delay should be approximately double the previous delay).
**Validates: Requirements 2.8, 8.2, 8.5**

**Property 7: Performance Insights Data Completeness**
*For any* RDS instance with Performance Insights enabled, when retrieving PI data, the result should include top SQL queries with execution times, execution counts, and associated wait events.
**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.7**

**Property 8: Graceful Degradation for Disabled Performance Insights**
*For any* RDS instance with Performance Insights disabled, the tool should continue execution and generate a report with available CloudWatch metrics, noting that PI data is unavailable.
**Validates: Requirements 3.5, 8.3, 8.4**

**Property 9: Technical Report Completeness**
*For any* diagnostic data, a generated technical report should include all collected CloudWatch metrics, Performance Insights data (if available), instance configuration details, and threshold violations.
**Validates: Requirements 4.1, 4.2, 4.3, 4.7**

**Property 10: Technical Report Structure**
*For any* technical report in text format, the output should contain clearly identifiable sections for: instance information, CloudWatch metrics, Performance Insights data, and analysis summary.
**Validates: Requirements 4.4**

**Property 11: JSON Output Round-Trip**
*For any* report generated in JSON format, parsing the output as JSON should succeed and produce a valid data structure containing all expected fields.
**Validates: Requirements 4.5, 9.7**

**Property 12: Threshold Violation Highlighting**
*For any* metric that exceeds its configured threshold, the technical report should include a violation entry with the metric name, current value, threshold value, and severity.
**Validates: Requirements 4.6**

**Property 13: Management Report Required Sections**
*For any* diagnostic data, a generated management report should include: executive summary, key findings, severity assessment, and actionable recommendations.
**Validates: Requirements 5.1, 5.2, 5.4, 5.5, 5.6**

**Property 14: Management Report Presentation Format**
*For any* management report, metrics should be presented as percentages or trends rather than raw values, and the overall length should be significantly shorter than the technical report for the same data.
**Validates: Requirements 5.3**

**Property 15: Trend Analysis Inclusion**
*For any* diagnostic data spanning multiple time periods, the management report should include trend analysis indicating whether key metrics are improving, degrading, or stable.
**Validates: Requirements 5.7**

**Property 16: AWS Profile Authentication**
*For any* valid AWS profile name, the tool should use that profile's credentials for all AWS API calls.
**Validates: Requirements 6.1**

**Property 17: Authentication Error Handling**
*For any* authentication failure (invalid credentials, expired tokens, insufficient permissions), the tool should return a descriptive error message indicating the specific authentication issue.
**Validates: Requirements 6.3, 6.6**

**Property 18: Permission Validation**
*For any* AWS profile, when validating permissions, the tool should check for required permissions (RDS describe, CloudWatch get metrics, Performance Insights access) and report any missing permissions.
**Validates: Requirements 6.5**

**Property 19: Configuration File Loading**
*For any* valid configuration file, loading the configuration should produce a Configuration object with all specified threshold values, default settings, and output preferences matching the file contents.
**Validates: Requirements 7.1, 7.4, 7.5**

**Property 20: Configuration Override Precedence**
*For any* configuration setting, if both a config file value and a command-line override are provided, the command-line value should take precedence in the final configuration.
**Validates: Requirements 7.3**

**Property 21: Invalid Configuration Handling**
*For any* configuration file with invalid values (negative thresholds, invalid formats, out-of-range values), the tool should log descriptive errors for each invalid value and use default values for those settings.
**Validates: Requirements 7.6**

**Property 22: Partial Data Report Generation**
*For any* diagnostic run where some data collection fails, the tool should generate a report containing all successfully collected data and clearly indicate which sections are incomplete or missing.
**Validates: Requirements 8.1, 8.4**

**Property 23: Input Validation**
*For any* user input (instance ID, time range, region, profile), the tool should validate the input format and return a clear error message for invalid inputs before attempting AWS API calls.
**Validates: Requirements 8.6**

**Property 24: Exception Logging**
*For any* exception that occurs during execution, the tool should log the exception type, message, and stack trace to enable troubleshooting.
**Validates: Requirements 8.7**

**Property 25: File Output with Directory Creation**
*For any* output file path, if the parent directories do not exist, the tool should create them before writing the report file.
**Validates: Requirements 9.1, 9.3**

**Property 26: CLI Option Equivalence**
*For any* command-line option that has both short and long forms (e.g., -p and --profile), using either form with the same value should produce identical behavior.
**Validates: Requirements 10.4**

**Property 27: Missing Required Parameter Handling**
*For any* command that requires specific parameters, if those parameters are missing, the tool should display an error message and usage hints without attempting execution.
**Validates: Requirements 10.3**

**Property 28: Verbose Mode Output Enhancement**
*For any* command executed with verbose mode enabled, the output should include additional progress information and debug details compared to the same command without verbose mode.
**Validates: Requirements 10.5**

**Property 29: Invalid Command Suggestion**
*For any* invalid command or incompatible option combination, the tool should provide a suggestion for the correct usage pattern.
**Validates: Requirements 10.7**

### Example-Based Test Cases

In addition to the properties above, the following specific examples should be tested:

**Example 1: Default Time Range**
When no time range is specified, the tool should collect metrics for the last 1 hour.
**Validates: Requirements 2.7**

**Example 2: Default AWS Profile**
When no AWS profile is specified, the tool should use the default AWS CLI profile.
**Validates: Requirements 6.2**

**Example 3: Default Configuration Values**
When no configuration file exists, the tool should use these default threshold values:
- CPU warning: 70%, critical: 90%
- Memory warning: 80%, critical: 95%
- Connections warning: 80%, critical: 95%
- IOPS warning: 80%, critical: 95%
- Storage warning: 80%, critical: 90%
**Validates: Requirements 7.2**

**Example 4: Standard Output Default**
When no output file is specified, the report should be displayed to standard output.
**Validates: Requirements 9.2**

**Example 5: Help Documentation**
When the tool is run with --help flag, it should display comprehensive usage documentation including all commands, options, and examples.
**Validates: Requirements 10.1**

## Error Handling

### Error Categories and Handling Strategies

1. **Authentication and Authorization Errors**
   - Invalid AWS profile: Return clear error with profile name
   - Expired credentials: Suggest credential refresh
   - Insufficient permissions: List specific missing permissions
   - Strategy: Fail fast with actionable error messages

2. **AWS API Errors**
   - Rate limiting: Retry with exponential backoff (max 5 retries)
   - Throttling: Respect retry-after headers
   - Service unavailable: Retry with backoff, then fail gracefully
   - Invalid parameters: Validate inputs before API calls
   - Strategy: Retry transient errors, fail fast on permanent errors

3. **Data Collection Errors**
   - Instance not found: Return descriptive error
   - Performance Insights disabled: Continue with CloudWatch metrics only
   - Partial metric collection failure: Generate report with available data
   - Strategy: Graceful degradation, maximize useful output

4. **Configuration Errors**
   - Missing config file: Use defaults
   - Invalid config values: Log warnings, use defaults for invalid values
   - Malformed JSON/YAML: Return parse error with line number
   - Strategy: Fail gracefully with defaults

5. **File I/O Errors**
   - Cannot create output directory: Return error with path and permissions info
   - Cannot write output file: Return error with path and permissions info
   - Disk full: Return clear error message
   - Strategy: Fail with clear error messages

6. **Input Validation Errors**
   - Invalid instance ID format: Return format requirements
   - Invalid time range: Return supported formats and examples
   - Invalid region: Return list of valid regions
   - Strategy: Fail fast with helpful guidance

### Error Message Format

All error messages should follow this structure:
```
ERROR: [Brief description]
Details: [Specific information about what went wrong]
Suggestion: [Actionable step to resolve the issue]
```

Example:
```
ERROR: Authentication failed for profile 'prod-account'
Details: The security token included in the request is expired
Suggestion: Run 'aws sso login --profile prod-account' to refresh credentials
```

## Testing Strategy

### Dual Testing Approach

The RDS Diagnostics Tool will employ both unit testing and property-based testing to ensure comprehensive coverage and correctness.

**Unit Tests** focus on:
- Specific examples and edge cases (e.g., default values, empty responses)
- Integration points between components
- Error conditions and exception handling
- Mock AWS API responses for deterministic testing

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Comprehensive input coverage through randomization
- Invariants and round-trip properties
- Behavior across wide ranges of valid inputs

Together, these approaches provide complementary coverage: unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across the input space.

### Property-Based Testing Configuration

**Framework**: We will use **Hypothesis** for Python, which is the standard property-based testing library.

**Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test must include a comment tag referencing the design document property
- Tag format: `# Feature: rds-diagnostics-tool, Property {number}: {property_text}`

**Example**:
```python
from hypothesis import given, strategies as st

# Feature: rds-diagnostics-tool, Property 4: Complete Metrics Collection
@given(
    instance_id=st.text(min_size=1, max_size=63),
    time_range=st.builds(TimeRange, ...)
)
@settings(max_examples=100)
def test_complete_metrics_collection(instance_id, time_range):
    """For any RDS instance and time range, collected metrics should include
    all required metrics: CPU, memory, connections, IOPS, and storage."""
    metrics = collector.collect_all_metrics(instance_id, time_range)
    
    assert metrics.cpu_utilization is not None
    assert metrics.freeable_memory is not None
    assert metrics.database_connections is not None
    assert metrics.iops.read_iops is not None
    assert metrics.iops.write_iops is not None
    assert metrics.storage is not None
```

### Test Organization

```
tests/
├── unit/
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_collectors.py
│   ├── test_analyzer.py
│   └── test_reporters.py
├── property/
│   ├── test_properties_discovery.py      # Properties 1-3
│   ├── test_properties_collection.py     # Properties 4-8
│   ├── test_properties_reporting.py      # Properties 9-15
│   ├── test_properties_auth.py           # Properties 16-18
│   ├── test_properties_config.py         # Properties 19-21
│   ├── test_properties_errors.py         # Properties 22-24
│   └── test_properties_cli.py            # Properties 25-29
├── integration/
│   ├── test_end_to_end.py
│   └── test_aws_integration.py
└── fixtures/
    ├── sample_configs.py
    ├── mock_aws_responses.py
    └── test_data.py
```

### Key Testing Scenarios

1. **Happy Path**: Valid instance, all metrics available, PI enabled
2. **Partial Data**: Some metrics unavailable, PI disabled
3. **Error Conditions**: Invalid credentials, rate limiting, network failures
4. **Edge Cases**: Empty metric responses, very large time ranges, many instances
5. **Configuration**: Various config file formats, overrides, invalid values
6. **Multi-Account**: Switching between different AWS profiles and regions
7. **Output Formats**: Text and JSON outputs for both report types

### Mocking Strategy

For unit and property tests, we will mock AWS API calls using `boto3` stubs:
- Use `botocore.stub.Stubber` for deterministic AWS responses
- Create reusable fixtures for common response patterns
- Test error conditions by stubbing error responses

For integration tests:
- Use actual AWS credentials (in CI/CD with test account)
- Test against real RDS instances in a test environment
- Validate end-to-end workflows

### Coverage Goals

- Line coverage: > 90%
- Branch coverage: > 85%
- All 29 correctness properties must have corresponding property tests
- All example test cases must have unit tests
- All error handling paths must be tested

## Implementation Notes

### Dependencies

**Core Dependencies**:
- `boto3`: AWS SDK for Python
- `botocore`: Low-level AWS service access
- `click`: CLI framework (alternative: `argparse`)
- `pydantic`: Data validation and settings management
- `python-dateutil`: Date/time parsing

**Testing Dependencies**:
- `pytest`: Test framework
- `hypothesis`: Property-based testing
- `pytest-mock`: Mocking utilities
- `moto`: AWS service mocking (for integration tests)

**Optional Dependencies**:
- `rich`: Enhanced terminal output formatting
- `tabulate`: Table formatting for reports
- `pyyaml`: YAML configuration file support

### Configuration File Format

The tool will support YAML configuration files:

```yaml
# ~/.rds-diagnostics/config.yaml
default_region: ap-southeast-1
default_time_range: 1h
output_format: text

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

# Account-specific settings (optional)
accounts:
  lt-prd:
    profile: lt-prd
    region: ap-southeast-1
  dm-prd:
    profile: dm-prd
    region: ap-southeast-1
```

### CLI Command Examples

```bash
# List all RDS instances in default region
rds-diag list --profile lt-prd

# Run diagnostics on a specific instance
rds-diag diagnose --profile lt-prd --instance my-db-instance

# Generate technical report for last 24 hours
rds-diag report --profile lt-prd --instance my-db-instance \
  --time-range 24h --report-type technical --output report.txt

# Generate management report in JSON format
rds-diag report --profile dm-prd --instance prod-db \
  --time-range 7d --report-type management --format json \
  --output management-report.json

# Use custom config file
rds-diag diagnose --config ./custom-config.yaml \
  --instance my-db --profile sp-uat

# Override threshold from command line
rds-diag report --instance my-db --cpu-critical 85 \
  --memory-warning 75
```

### Performance Considerations

1. **Parallel Metric Collection**: Collect different metric types concurrently using `asyncio` or `concurrent.futures`
2. **Caching**: Cache instance metadata to avoid repeated describe calls
3. **Batch API Calls**: Use CloudWatch batch APIs when collecting multiple metrics
4. **Pagination**: Handle paginated responses for large result sets
5. **Connection Pooling**: Reuse boto3 client connections

### Security Considerations

1. **Credential Handling**: Never log or display AWS credentials
2. **Least Privilege**: Document minimum required IAM permissions
3. **Audit Logging**: Log all AWS API calls for audit trails
4. **Sensitive Data**: Sanitize SQL queries in reports (remove literals)
5. **Output Files**: Set appropriate file permissions on generated reports

### Required IAM Permissions

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

## Future Enhancements

Potential features for future iterations:
1. Support for Aurora clusters and read replicas
2. Historical trend analysis with data persistence
3. Automated alerting based on thresholds
4. Integration with incident management systems
5. Web-based dashboard for visualization
6. Comparative analysis across multiple instances
7. Query optimization recommendations
8. Cost analysis and optimization suggestions
9. Scheduled report generation
10. Export to additional formats (PDF, HTML, CSV)
