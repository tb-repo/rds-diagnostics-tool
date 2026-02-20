# Implementation Plan: RDS Diagnostics and Reporting Tool

## Overview

This implementation plan breaks down the RDS Diagnostics and Reporting Tool into incremental, testable steps. The approach follows a bottom-up strategy: building core data models and AWS clients first, then data collection, analysis, reporting, and finally the CLI interface. Each major component includes property-based tests to validate correctness properties from the design document.

The implementation uses Python with boto3 for AWS integration, Hypothesis for property-based testing, and Click for the CLI framework.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create Python package structure with appropriate directories (cli/, core/, aws/, collectors/, analysis/, reporting/, tests/)
  - Create pyproject.toml or setup.py with all required dependencies (boto3, click, pydantic, hypothesis, pytest)
  - Set up pytest configuration for unit and property tests
  - Create initial __init__.py files for all packages
  - _Requirements: All (foundational)_

- [x] 2. Implement core data models
  - [x] 2.1 Create data model classes using dataclasses or Pydantic
    - Implement TimeRange, RDSInstanceInfo, MetricDataPoint, MetricSeries, IOPSMetrics, StorageMetrics, CloudWatchMetrics
    - Implement SQLQuery, WaitEvent, Violation, TrendAnalysis, MetricAnalysis, DiagnosticData, Report
    - Implement enums: Severity, Trend, ReportType, OutputFormat
    - Add helper methods (get_average, get_max, get_min, get_latest, get_usage_percentage, etc.)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.2, 3.3, 3.4, 4.1, 4.2, 5.1_
  
  - [ ]* 2.2 Write property test for TimeRange parsing
    - **Property: Time range parsing should handle various duration formats**
    - Test that parsing "1h", "24h", "7d" produces correct start/end times
    - _Requirements: 2.6, 2.7_
  
  - [ ]* 2.3 Write unit tests for data model helper methods
    - Test MetricSeries aggregation methods (average, max, min, latest)
    - Test StorageMetrics usage percentage calculation
    - Test IOPSMetrics total IOPS calculation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Implement configuration management
  - [x] 3.1 Create Configuration and MetricThresholds classes
    - Implement Configuration class with all settings (aws_profile, default_region, default_time_range, metric_thresholds, output_format)
    - Implement MetricThresholds class with default values
    - Implement load_from_file() to parse YAML configuration files
    - Implement load_defaults() to return default configuration
    - Implement merge_with_cli_args() to handle command-line overrides
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [ ]* 3.2 Write property test for configuration loading
    - **Property 19: Configuration File Loading**
    - **Validates: Requirements 7.1, 7.4, 7.5**
    - Test that loading valid config files produces correct Configuration objects
  
  - [ ]* 3.3 Write property test for configuration override precedence
    - **Property 20: Configuration Override Precedence**
    - **Validates: Requirements 7.3**
    - Test that command-line values override config file values
  
  - [ ]* 3.4 Write property test for invalid configuration handling
    - **Property 21: Invalid Configuration Handling**
    - **Validates: Requirements 7.6**
    - Test that invalid config values result in errors and defaults
  
  - [ ]* 3.5 Write unit tests for default configuration
    - **Example 3: Default Configuration Values**
    - Test that load_defaults() returns expected threshold values
    - _Requirements: 7.2_

- [x] 4. Implement AWS service clients with error handling
  - [x] 4.1 Create AWSClientFactory and base client classes
    - Implement AWSClientFactory with profile and region initialization
    - Implement create_rds_client(), create_cloudwatch_client(), create_performance_insights_client()
    - Add retry logic with exponential backoff for transient errors
    - Add error handling for authentication and authorization failures
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6, 8.2, 8.5_
  
  - [x] 4.2 Implement RDSClient wrapper
    - Implement list_instances() to retrieve all RDS instances
    - Implement describe_instance() to get instance details
    - Implement get_instance_resource_id() for Performance Insights
    - Add error handling for invalid instance IDs
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 4.3 Implement CloudWatchClient wrapper
    - Implement get_metric_statistics() with proper parameter handling
    - Add pagination support for large result sets
    - Add rate limit handling with exponential backoff
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8_
  
  - [x] 4.4 Implement PerformanceInsightsClient wrapper
    - Implement get_resource_metrics() for PI data retrieval
    - Implement describe_dimension_keys() for top queries
    - Add check for Performance Insights availability
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [ ]* 4.5 Write property test for retry with exponential backoff
    - **Property 6: Retry with Exponential Backoff**
    - **Validates: Requirements 2.8, 8.2, 8.5**
    - Test that retry delays follow exponential backoff pattern
  
  - [ ]* 4.6 Write property test for AWS profile authentication
    - **Property 16: AWS Profile Authentication**
    - **Validates: Requirements 6.1**
    - Test that specified profiles are used for API calls
  
  - [ ]* 4.7 Write property test for authentication error handling
    - **Property 17: Authentication Error Handling**
    - **Validates: Requirements 6.3, 6.6**
    - Test that auth failures produce descriptive error messages
  
  - [ ]* 4.8 Write unit test for default AWS profile
    - **Example 2: Default AWS Profile**
    - Test that no profile specified uses default
    - _Requirements: 6.2_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement data collection modules
  - [x] 6.1 Create InstanceInfoCollector
    - Implement get_instance_details() to retrieve RDS instance configuration
    - Implement list_all_instances() to list instances in a region
    - Map AWS API responses to RDSInstanceInfo data model
    - _Requirements: 1.1, 1.2, 1.3, 4.7_
  
  - [x] 6.2 Create MetricsCollector
    - Implement collect_cpu_metrics() for CPU utilization
    - Implement collect_memory_metrics() for freeable memory
    - Implement collect_connection_metrics() for database connections
    - Implement collect_iops_metrics() for read/write IOPS
    - Implement collect_storage_metrics() for storage usage
    - Implement collect_all_metrics() to orchestrate all metric collection
    - Add time range filtering for all metrics
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 6.3 Create PerformanceInsightsCollector
    - Implement is_performance_insights_enabled() check
    - Implement collect_top_sql_queries() to get top 10 queries by execution time
    - Implement collect_wait_events() for wait event data
    - Map PI API responses to SQLQuery and WaitEvent data models
    - Handle cases where PI is disabled gracefully
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [ ]* 6.4 Write property test for instance discovery completeness
    - **Property 1: Instance Discovery Completeness**
    - **Validates: Requirements 1.1, 1.2**
    - Test that all instances are returned with complete information
  
  - [ ]* 6.5 Write property test for instance validation
    - **Property 2: Instance Validation**
    - **Validates: Requirements 1.3, 1.4**
    - Test that validation correctly identifies valid/invalid instances
  
  - [ ]* 6.6 Write property test for region support
    - **Property 3: Region Support**
    - **Validates: Requirements 1.5**
    - Test that any valid region can be queried
  
  - [ ]* 6.7 Write property test for complete metrics collection
    - **Property 4: Complete Metrics Collection**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    - Test that all required metrics are collected
  
  - [ ]* 6.8 Write property test for time range filtering
    - **Property 5: Time Range Filtering**
    - **Validates: Requirements 2.6, 3.6**
    - Test that metrics have timestamps within specified range
  
  - [ ]* 6.9 Write property test for Performance Insights data completeness
    - **Property 7: Performance Insights Data Completeness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.7**
    - Test that PI data includes all required fields
  
  - [ ]* 6.10 Write property test for graceful degradation with disabled PI
    - **Property 8: Graceful Degradation for Disabled Performance Insights**
    - **Validates: Requirements 3.5, 8.3, 8.4**
    - Test that tool continues with CloudWatch metrics when PI is disabled
  
  - [ ]* 6.11 Write unit test for default time range
    - **Example 1: Default Time Range**
    - Test that no time range specified defaults to 1 hour
    - _Requirements: 2.7_

- [x] 7. Implement analysis engine
  - [x] 7.1 Create DiagnosticAnalyzer
    - Implement analyze_metrics() to process CloudWatch metrics
    - Implement identify_threshold_violations() to find metrics exceeding thresholds
    - Implement calculate_trends() to determine if metrics are improving/degrading/stable
    - Implement assess_overall_severity() to determine Critical/Warning/Normal status
    - Implement generate_recommendations() based on findings
    - _Requirements: 4.6, 5.1, 5.2, 5.4, 5.5, 5.7_
  
  - [x] 7.2 Create QueryAnalyzer
    - Implement rank_queries_by_impact() to sort queries by resource consumption
    - Implement identify_problematic_queries() to flag high-impact queries
    - _Requirements: 3.2, 3.3, 5.5_
  
  - [ ]* 7.3 Write property test for threshold violation highlighting
    - **Property 12: Threshold Violation Highlighting**
    - **Validates: Requirements 4.6**
    - Test that metrics exceeding thresholds are flagged
  
  - [ ]* 7.4 Write property test for trend analysis inclusion
    - **Property 15: Trend Analysis Inclusion**
    - **Validates: Requirements 5.7**
    - Test that multi-period data includes trend analysis
  
  - [ ]* 7.5 Write unit tests for severity assessment
    - Test that multiple critical violations result in Critical severity
    - Test that only warnings result in Warning severity
    - Test that no violations result in Normal severity
    - _Requirements: 5.4_

- [x] 8. Implement reporting engine
  - [x] 8.1 Create TechnicalReportFormatter
    - Implement format() to generate text-based technical reports
    - Implement format_json() to generate JSON technical reports
    - Include all CloudWatch metrics with timestamps and values
    - Include full SQL query text and wait events
    - Include instance configuration details
    - Include threshold violations with highlighting
    - Create structured sections for readability
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  
  - [x] 8.2 Create ManagementReportFormatter
    - Implement format() to generate management reports
    - Implement create_executive_summary() for high-level overview
    - Implement format_key_findings() to highlight critical issues
    - Implement format_recommendations() for actionable items
    - Present metrics as percentages and trends, not raw values
    - Keep report concise and business-friendly
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_
  
  - [x] 8.3 Create ReportGenerator orchestrator
    - Implement generate_report() to route to appropriate formatter
    - Handle both technical and management report types
    - Support both text and JSON output formats
    - _Requirements: 4.1, 4.5, 5.1, 9.5, 9.6_
  
  - [ ]* 8.4 Write property test for technical report completeness
    - **Property 9: Technical Report Completeness**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.7**
    - Test that technical reports include all required data
  
  - [ ]* 8.5 Write property test for technical report structure
    - **Property 10: Technical Report Structure**
    - **Validates: Requirements 4.4**
    - Test that reports contain identifiable sections
  
  - [ ]* 8.6 Write property test for JSON output round-trip
    - **Property 11: JSON Output Round-Trip**
    - **Validates: Requirements 4.5, 9.7**
    - Test that JSON output can be parsed successfully
  
  - [ ]* 8.7 Write property test for management report required sections
    - **Property 13: Management Report Required Sections**
    - **Validates: Requirements 5.1, 5.2, 5.4, 5.5, 5.6**
    - Test that management reports include all required sections
  
  - [ ]* 8.8 Write property test for management report presentation format
    - **Property 14: Management Report Presentation Format**
    - **Validates: Requirements 5.3**
    - Test that management reports use percentages/trends and are concise

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement application core orchestration
  - [x] 10.1 Create RDSDiagnosticsApp class
    - Implement __init__() to initialize with configuration and AWS clients
    - Implement list_instances() to orchestrate instance discovery
    - Implement run_diagnostics() to orchestrate full diagnostic workflow
    - Implement generate_report() to create formatted reports
    - Add comprehensive error handling and logging
    - Handle partial data collection failures gracefully
    - _Requirements: 1.1, 1.2, 8.1, 8.3, 8.4, 8.7_
  
  - [ ]* 10.2 Write property test for partial data report generation
    - **Property 22: Partial Data Report Generation**
    - **Validates: Requirements 8.1, 8.4**
    - Test that reports are generated with incomplete data
  
  - [ ]* 10.3 Write property test for exception logging
    - **Property 24: Exception Logging**
    - **Validates: Requirements 8.7**
    - Test that exceptions are logged with details

- [x] 11. Implement CLI interface
  - [x] 11.1 Create main CLI entry point with Click framework
    - Create cli/main.py with Click-based CLI group
    - Implement main CLI group with global options (--profile, --region, --config, --verbose)
    - Add --help documentation for the main command
    - Support both short (-p, -r, -c, -v) and long (--profile, --region, --config, --verbose) option formats
    - _Requirements: 10.1, 10.2, 10.4, 10.6_
  
  - [x] 11.2 Implement 'list' command
    - Create 'list' subcommand to display all RDS instances in a region
    - Accept --profile and --region options
    - Display instance ID, engine type, status, and instance class in formatted output
    - Handle errors gracefully (authentication failures, no instances found)
    - _Requirements: 1.1, 1.2, 10.2_
  
  - [x] 11.3 Implement 'diagnose' command
    - Create 'diagnose' subcommand to run diagnostics on a specific instance
    - Accept required --instance option and optional --time-range option
    - Display diagnostic summary to stdout
    - Validate instance ID and time range format
    - _Requirements: 1.3, 2.6, 2.7, 8.6, 10.2, 10.3_
  
  - [x] 11.4 Implement 'report' command
    - Create 'report' subcommand to generate formatted reports
    - Accept --instance (required), --time-range, --report-type (technical/management), --format (text/json), --output options
    - Default to technical report in text format to stdout
    - Validate all input parameters before execution
    - _Requirements: 4.1, 4.5, 5.1, 9.1, 9.2, 9.5, 9.6, 10.2, 10.3_
  
  - [x] 11.5 Implement output file handling
    - Write reports to files when --output path is specified
    - Create parent directories if they don't exist
    - Prompt for confirmation before overwriting existing files (or add --force flag)
    - Handle file write errors with clear error messages
    - Display reports to stdout when no output file specified
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [x] 11.6 Implement verbose mode
    - Add progress information when --verbose is enabled
    - Show AWS API call details (which APIs are being called)
    - Display metric collection progress
    - Show timing information for each phase
    - _Requirements: 10.5_
  
  - [x] 11.7 Implement input validation and error handling
    - Validate instance IDs (format and existence)
    - Validate time ranges (format: "1h", "24h", "7d")
    - Validate regions (must be valid AWS region)
    - Validate AWS profiles (must exist in AWS CLI config)
    - Provide clear error messages for invalid inputs with examples
    - Suggest correct usage patterns for invalid command combinations
    - _Requirements: 8.6, 10.3, 10.7_
  
  - [x] 11.8 Wire CLI to application core
    - Connect all CLI commands to RDSDiagnosticsApp methods
    - Initialize Configuration from CLI arguments and config file
    - Initialize AWSClientFactory with selected profile and region
    - Handle application exceptions and display user-friendly errors
    - Ensure proper error message formatting for all error types
    - _Requirements: All (integration)_
  
  - [ ]* 11.9 Write property test for CLI option equivalence
    - **Property 26: CLI Option Equivalence**
    - **Validates: Requirements 10.4**
    - Test that short (-p) and long (--profile) options produce identical behavior
    - Test with multiple option pairs: -p/--profile, -r/--region, -i/--instance, -t/--time-range, -f/--format, -o/--output
  
  - [ ]* 11.10 Write property test for missing required parameter handling
    - **Property 27: Missing Required Parameter Handling**
    - **Validates: Requirements 10.3**
    - Test that missing --instance parameter produces error message with usage hints
    - Test that error message suggests correct usage pattern
  
  - [ ]* 11.11 Write property test for verbose mode output enhancement
    - **Property 28: Verbose Mode Output Enhancement**
    - **Validates: Requirements 10.5**
    - Test that verbose mode adds progress information and API call details
    - Test that output with --verbose is longer than without --verbose
  
  - [ ]* 11.12 Write property test for invalid command suggestion
    - **Property 29: Invalid Command Suggestion**
    - **Validates: Requirements 10.7**
    - Test that invalid commands provide suggestions for correct usage
    - Test that incompatible option combinations suggest valid alternatives
  
  - [ ]* 11.13 Write property test for file output with directory creation
    - **Property 25: File Output with Directory Creation**
    - **Validates: Requirements 9.1, 9.3**
    - Test that parent directories are created when writing output files
    - Test with nested directory paths that don't exist
  
  - [ ]* 11.14 Write property test for input validation
    - **Property 23: Input Validation**
    - **Validates: Requirements 8.6**
    - Test that invalid instance IDs produce clear error messages
    - Test that invalid time ranges produce error messages with format examples
    - Test that invalid regions produce error messages with valid region list
  
  - [ ]* 11.15 Write unit test for help documentation
    - **Example 5: Help Documentation**
    - Test that --help displays comprehensive documentation with all commands and options
    - Test that help includes usage examples
    - _Requirements: 10.1_
  
  - [ ]* 11.16 Write unit test for standard output default
    - **Example 4: Standard Output Default**
    - Test that no --output option displays report to stdout
    - _Requirements: 9.2_
  
  - [ ]* 11.17 Write unit test for file overwrite confirmation
    - Test that attempting to overwrite existing file prompts for confirmation
    - Test that --force flag bypasses confirmation
    - _Requirements: 9.4_

- [x] 12. Add permission validation
  - [x] 12.1 Implement permission checking
    - Check for required IAM permissions (RDS describe, CloudWatch get metrics, PI access)
    - Report specific missing permissions when detected
    - _Requirements: 6.5, 6.6_
  
  - [ ]* 12.2 Write property test for permission validation
    - **Property 18: Permission Validation**
    - **Validates: Requirements 6.5**
    - Test that permission checks identify missing permissions

- [x] 13. Create CLI entry point and packaging
  - [x] 13.1 Create CLI entry point script
    - Add console_scripts entry point in pyproject.toml for 'rds-diag' command
    - Create main entry point function that calls CLI
    - Ensure proper exception handling at the top level
    - _Requirements: 10.1, 10.2_
  
  - [x] 13.2 Create example configuration file
    - Create example config.yaml with all settings documented
    - Include comments explaining each configuration option
    - Include examples for all threshold settings
    - Include examples for account-specific settings
    - _Requirements: 7.1, 7.2_
  
  - [x] 13.3 Create comprehensive documentation
    - Create or update README.md with installation instructions
    - Document all CLI commands with examples
    - Document required IAM permissions with example policy
    - Add troubleshooting guide for common errors (authentication, permissions, rate limiting)
    - Document configuration file format and options
    - Add examples for common use cases (list instances, run diagnostics, generate reports)
    - _Requirements: 10.1, 10.6, 6.5, 6.6_

- [-] 14. Final checkpoint - Integration testing and validation
  - [x] 14.1 Run end-to-end integration tests
    - Test 'list' command with mocked AWS responses
    - Test 'diagnose' command with complete workflow
    - Test 'report' command with both technical and management report types
    - Test with various option combinations (different regions, profiles, time ranges)
    - Test error scenarios (invalid credentials, missing permissions, instance not found)
    - _Requirements: All (integration)_
  
  - [ ]\* 14.2 Verify property-based test coverage
    - Ensure all 29 correctness properties have corresponding property tests
    - Run all property tests with minimum 100 iterations each
    - Verify all property tests pass
    - _Requirements: All (correctness validation)_
  
  - [ ]\* 14.3 Verify example test coverage
    - Ensure all 5 example test cases have corresponding unit tests
    - Verify all example tests pass
    - _Requirements: 2.7, 6.2, 7.2, 9.2, 10.1_
  
  - [x] 14.4 Verify code coverage goals
    - Run pytest with coverage reporting
    - Ensure line coverage > 90%
    - Ensure branch coverage > 85%
    - Identify and test any uncovered code paths
    - _Requirements: All (quality assurance)_
  
  - [ ]\* 14.5 Manual testing with real AWS account (optional)
    - Test against real RDS instances in a test AWS account
    - Verify CloudWatch metrics collection works correctly
    - Verify Performance Insights data collection (if enabled)
    - Verify report generation produces expected output
    - Test with multiple AWS profiles and regions
    - _Requirements: All (real-world validation)_
  
  - [x] 14.6 Final checkpoint
    - Ensure all tests pass
    - Verify all documentation is complete
    - Ask the user if questions arise or if ready for release

- [x] 15. Fix data accuracy issues in reports
  - [x] 15.1 Fix max_connections display
    - Query actual max_connections value from RDS parameter group using describe_db_parameters API
    - Update InstanceInfoCollector to retrieve actual value instead of estimation
    - Handle cases where parameter group cannot be queried (show "N/A" or omit)
    - Update formatters to display actual value or indicate it's unavailable
    - _Requirements: 4.10_
  
  - [x] 15.2 Fix Performance Insights data accuracy
    - Research correct PI API response structure for execution counts
    - Fix calculation of execution_count in PerformanceInsightsCollector
    - Fix calculation of average_execution_time to be accurate
    - Ensure total_execution_time, average_execution_time, and execution_count are consistent
    - Add validation to ensure execution_count > 0 when execution_time > 0
    - _Requirements: 3.2, 3.3, 3.7_
  
  - [x] 15.3 Add top databases collection
    - Implement collect_top_databases() method in PerformanceInsightsCollector
    - Use PI API with group_by='db.name' to get database load
    - Add TopDatabase data model to core/models.py
    - Update DiagnosticData to include top_databases field
    - Display top databases in technical report formatter
    - _Requirements: 3.8, 4.8_
  
  - [x] 15.4 Add top users collection
    - Implement collect_top_users() method in PerformanceInsightsCollector
    - Use PI API with group_by='db.user' to get user load
    - Add TopUser data model to core/models.py
    - Update DiagnosticData to include top_users field
    - Display top users in technical report formatter
    - _Requirements: 3.9, 4.8_
  
  - [x] 15.5 Fix duplicate queries in reports
    - Add deduplication logic in collect_top_sql_queries()
    - Use query_id or query_text hash to identify duplicates
    - Keep the query with highest load when duplicates found
    - _Requirements: 3.10_
  
  - [x] 15.6 Complete Aurora storage fix in reports
    - Ensure all report sections show correct Aurora storage information
    - Remove "1 GB" display for Aurora allocated storage
    - Show "Auto-scaling (cluster-level)" consistently
    - Display actual current storage from CloudWatch metrics
    - _Requirements: 4.9_
  
  - [x] 15.7 Update application core to collect new data
    - Update RDSDiagnosticsApp.run_diagnostics() to collect top databases
    - Update RDSDiagnosticsApp.run_diagnostics() to collect top users
    - Ensure new data is passed to report generation
    - _Requirements: 3.8, 3.9_
  
  - [x] 15.8 Test data accuracy fixes
    - Write unit tests for max_connections retrieval
    - Write unit tests for PI data accuracy (execution counts)
    - Write unit tests for top databases collection
    - Write unit tests for top users collection
    - Write unit tests for query deduplication
    - Verify all tests pass
    - _Requirements: 3.2, 3.3, 3.7, 3.8, 3.9, 3.10, 4.8, 4.9, 4.10_

## Notes

- Tasks marked with `*` are optional property-based and unit tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major milestones
- Property tests validate universal correctness properties across input ranges
- Unit tests validate specific examples, edge cases, and error conditions
- The implementation follows a bottom-up approach: data models → AWS clients → collectors → analysis → reporting → CLI
- All AWS API interactions should be mockable for testing
- Error handling is integrated throughout, not as a separate phase
