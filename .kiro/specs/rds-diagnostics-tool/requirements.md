# Requirements Document: RDS Diagnostics and Reporting Tool

## Introduction

The RDS Diagnostics and Reporting Tool is a command-line utility designed to help Database Management (DBM) teams quickly diagnose, analyze, and report on AWS RDS instance performance issues across multiple AWS accounts and environments. The tool retrieves performance metrics, identifies problematic queries, and generates formatted reports suitable for both technical teams and management audiences.

## Glossary

- **RDS_Tool**: The RDS Diagnostics and Reporting Tool system
- **RDS_Instance**: An Amazon Relational Database Service database instance
- **Performance_Insights**: AWS service providing database performance monitoring and analysis
- **CloudWatch_Metrics**: AWS CloudWatch monitoring data for RDS instances
- **Diagnostic_Report**: A formatted output containing RDS performance analysis
- **AWS_Profile**: A named configuration in AWS CLI for authentication
- **Target_Account**: One of the managed AWS accounts (LT-DEV, LT-SIT, LT-UAT, LT-PRD, DM-DEV, DM-STG, DM-PRD, SP-DEV, SP-STG, SP-UAT, SP-PRD)
- **Primary_Region**: The AWS region ap-southeast-1 (Singapore)
- **Top_Query**: A SQL query identified as consuming significant database resources
- **Metric_Threshold**: A configurable limit that triggers alerts or highlights in reports

## Requirements

### Requirement 1: RDS Instance Discovery and Selection

**User Story:** As a DBM team member, I want to discover and select RDS instances across multiple AWS accounts, so that I can quickly target the instance I need to diagnose.

#### Acceptance Criteria

1. WHEN the user specifies an AWS profile, THE RDS_Tool SHALL retrieve all RDS instances in the Primary_Region
2. WHEN multiple RDS instances are found, THE RDS_Tool SHALL display a list with instance identifiers, engine types, and status
3. WHEN the user provides an instance identifier, THE RDS_Tool SHALL validate that the instance exists in the specified account and region
4. IF an invalid instance identifier is provided, THEN THE RDS_Tool SHALL return a descriptive error message
5. WHERE the user specifies a different region, THE RDS_Tool SHALL support querying RDS instances in that region

### Requirement 2: Performance Metrics Collection

**User Story:** As a DBM team member, I want to collect key RDS performance metrics, so that I can understand the current and historical performance state of the database.

#### Acceptance Criteria

1. WHEN diagnostics are requested, THE RDS_Tool SHALL retrieve CPU utilization metrics from CloudWatch_Metrics
2. WHEN diagnostics are requested, THE RDS_Tool SHALL retrieve memory utilization metrics from CloudWatch_Metrics
3. WHEN diagnostics are requested, THE RDS_Tool SHALL retrieve database connection count metrics from CloudWatch_Metrics
4. WHEN diagnostics are requested, THE RDS_Tool SHALL retrieve IOPS (read and write) metrics from CloudWatch_Metrics
5. WHEN diagnostics are requested, THE RDS_Tool SHALL retrieve storage metrics including free space from CloudWatch_Metrics
6. WHERE a time range is specified, THE RDS_Tool SHALL retrieve metrics for that specific time period
7. WHERE no time range is specified, THE RDS_Tool SHALL default to the last 1 hour of metrics
8. WHEN retrieving metrics, THE RDS_Tool SHALL handle API rate limits gracefully and retry with exponential backoff

### Requirement 3: Performance Insights Data Retrieval

**User Story:** As a DBM team member, I want to retrieve Performance Insights data including top SQL queries, so that I can identify the root cause of performance issues.

#### Acceptance Criteria

1. WHEN Performance Insights is enabled on the RDS_Instance, THE RDS_Tool SHALL retrieve top database load contributors
2. WHEN retrieving Performance Insights data, THE RDS_Tool SHALL identify the top 10 SQL queries by total execution time
3. WHEN retrieving Performance Insights data, THE RDS_Tool SHALL identify the top 10 SQL queries by average execution time
4. WHEN retrieving Performance Insights data, THE RDS_Tool SHALL include wait events associated with each Top_Query
5. IF Performance Insights is not enabled, THEN THE RDS_Tool SHALL inform the user and continue with available metrics
6. WHERE a time range is specified, THE RDS_Tool SHALL retrieve Performance Insights data for that period
7. WHEN retrieving query data, THE RDS_Tool SHALL include query execution counts and row counts where available
8. WHEN retrieving Performance Insights data, THE RDS_Tool SHALL retrieve top databases by database load
9. WHEN retrieving Performance Insights data, THE RDS_Tool SHALL retrieve top users by database load
10. WHEN retrieving Performance Insights data, THE RDS_Tool SHALL deduplicate queries to avoid showing the same query multiple times

### Requirement 4: Report Generation for Technical Audiences

**User Story:** As a DBM engineer, I want detailed technical reports with raw metrics and query details, so that I can perform in-depth troubleshooting and analysis.

#### Acceptance Criteria

1. WHEN generating a technical report, THE RDS_Tool SHALL include all collected CloudWatch_Metrics with timestamps and values
2. WHEN generating a technical report, THE RDS_Tool SHALL include full SQL query text for Top_Query entries
3. WHEN generating a technical report, THE RDS_Tool SHALL include wait event details and statistics
4. WHEN generating a technical report, THE RDS_Tool SHALL format output in a structured, readable text format
5. WHERE the user specifies JSON output format, THE RDS_Tool SHALL generate the report in valid JSON format
6. WHEN metrics exceed Metric_Threshold values, THE RDS_Tool SHALL highlight these in the technical report
7. WHEN generating a technical report, THE RDS_Tool SHALL include RDS instance configuration details (instance class, engine version, storage type)
8. WHEN generating a technical report, THE RDS_Tool SHALL include top databases and top users from Performance Insights data
9. WHEN generating a technical report for Aurora instances, THE RDS_Tool SHALL display actual storage usage from CloudWatch metrics instead of allocated storage API value
10. WHEN generating a technical report, THE RDS_Tool SHALL query actual max_connections value from parameter group or omit if unavailable

### Requirement 5: Report Generation for Management Audiences

**User Story:** As a DBM team lead, I want executive summary reports with key findings and recommendations, so that I can communicate issues and impact to management.

#### Acceptance Criteria

1. WHEN generating a management report, THE RDS_Tool SHALL provide a summary section with key findings
2. WHEN generating a management report, THE RDS_Tool SHALL highlight critical metrics that exceed thresholds
3. WHEN generating a management report, THE RDS_Tool SHALL present data using percentages and trends rather than raw values
4. WHEN generating a management report, THE RDS_Tool SHALL include a severity assessment (Critical, Warning, Normal)
5. WHEN generating a management report, THE RDS_Tool SHALL provide actionable recommendations based on findings
6. WHEN generating a management report, THE RDS_Tool SHALL format output in a concise, business-friendly format
7. WHERE multiple time periods are analyzed, THE RDS_Tool SHALL include trend comparisons (improving, degrading, stable)

### Requirement 6: AWS Authentication and Multi-Account Support

**User Story:** As a DBM team member, I want to use my existing AWS CLI profiles for authentication, so that I can seamlessly work across multiple accounts without managing separate credentials.

#### Acceptance Criteria

1. WHEN the user specifies an AWS_Profile, THE RDS_Tool SHALL use that profile for AWS API authentication
2. WHERE no AWS_Profile is specified, THE RDS_Tool SHALL use the default AWS CLI profile
3. WHEN authentication fails, THE RDS_Tool SHALL return a clear error message indicating the authentication issue
4. THE RDS_Tool SHALL support all Target_Account profiles configured in the user's AWS CLI
5. WHEN switching between accounts, THE RDS_Tool SHALL validate permissions for RDS and CloudWatch access
6. IF insufficient permissions are detected, THEN THE RDS_Tool SHALL inform the user which permissions are missing

### Requirement 7: Configuration and Customization

**User Story:** As a DBM team member, I want to configure metric thresholds and default settings, so that I can customize the tool to match our team's standards and alert levels.

#### Acceptance Criteria

1. WHERE a configuration file exists, THE RDS_Tool SHALL load Metric_Threshold values from that file
2. WHERE no configuration file exists, THE RDS_Tool SHALL use sensible default threshold values
3. WHEN the user provides command-line threshold overrides, THE RDS_Tool SHALL use those values instead of configuration file values
4. THE RDS_Tool SHALL support configuring default time ranges for metric collection
5. THE RDS_Tool SHALL support configuring default output formats (text, JSON)
6. WHEN configuration values are invalid, THE RDS_Tool SHALL return descriptive error messages and use defaults

### Requirement 8: Error Handling and Resilience

**User Story:** As a DBM team member, I want the tool to handle errors gracefully and provide clear feedback, so that I can quickly understand and resolve issues when they occur.

#### Acceptance Criteria

1. WHEN AWS API calls fail, THE RDS_Tool SHALL log the error details and continue with available data
2. WHEN network connectivity issues occur, THE RDS_Tool SHALL retry failed requests with exponential backoff
3. IF critical data cannot be retrieved, THEN THE RDS_Tool SHALL inform the user and indicate which sections of the report are incomplete
4. WHEN partial data is available, THE RDS_Tool SHALL generate a report with the available information and note missing sections
5. WHEN encountering rate limiting, THE RDS_Tool SHALL respect AWS API rate limits and retry appropriately
6. THE RDS_Tool SHALL validate all user inputs and provide clear error messages for invalid inputs
7. WHEN exceptions occur, THE RDS_Tool SHALL log detailed error information for troubleshooting

### Requirement 9: Output and Export Options

**User Story:** As a DBM team member, I want to save reports to files and export data in different formats, so that I can share findings with team members and integrate with other tools.

#### Acceptance Criteria

1. WHERE the user specifies an output file path, THE RDS_Tool SHALL write the Diagnostic_Report to that file
2. WHERE no output file is specified, THE RDS_Tool SHALL display the report to standard output
3. WHEN writing to a file, THE RDS_Tool SHALL create parent directories if they do not exist
4. IF the output file already exists, THEN THE RDS_Tool SHALL prompt for confirmation before overwriting
5. THE RDS_Tool SHALL support exporting reports in plain text format
6. THE RDS_Tool SHALL support exporting reports in JSON format for programmatic processing
7. WHERE JSON format is selected, THE RDS_Tool SHALL ensure all output is valid, parseable JSON

### Requirement 10: Command-Line Interface Design

**User Story:** As a DBM team member, I want an intuitive command-line interface with clear options and help documentation, so that I can quickly learn and use the tool effectively.

#### Acceptance Criteria

1. WHEN the user runs the tool with --help flag, THE RDS_Tool SHALL display comprehensive usage documentation
2. THE RDS_Tool SHALL support a command structure with clear subcommands (e.g., diagnose, report, list)
3. WHEN required parameters are missing, THE RDS_Tool SHALL display an error message and usage hints
4. THE RDS_Tool SHALL support both short (-p) and long (--profile) option formats
5. WHEN the user requests verbose output, THE RDS_Tool SHALL display detailed progress information
6. THE RDS_Tool SHALL provide examples in the help documentation for common use cases
7. WHEN invalid command combinations are provided, THE RDS_Tool SHALL suggest correct usage patterns
