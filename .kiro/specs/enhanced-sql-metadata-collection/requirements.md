# Requirements Document

## Introduction

This document specifies requirements for enhancing SQL query details and metadata collection from AWS Performance Insights in the RDS Diagnostics Tool. The enhancement addresses current limitations in SQL text truncation, limited metadata collection, and lack of flexibility across different RDS engine types (Standard RDS vs Aurora).

## Glossary

- **Performance_Insights_API**: AWS service API that provides database performance monitoring and analysis capabilities
- **SQL_Query_Collector**: Component responsible for retrieving SQL query information from Performance Insights API
- **SQL_Metadata**: Comprehensive execution metrics associated with a SQL query (execution time, calls per second, CPU time, etc.)
- **RDS_Engine**: Database engine type (MySQL, PostgreSQL, Oracle, SQL Server, MariaDB, Aurora MySQL, Aurora PostgreSQL)
- **SQL_ID**: Unique identifier for a SQL query in Performance Insights
- **Dimension_Key**: Performance Insights API concept representing a specific dimension value (e.g., a specific SQL statement)
- **Metric_Query**: Performance Insights API request for specific performance metrics
- **Report_Formatter**: Component responsible for displaying SQL query information in diagnostic reports
- **SQLQuery_Model**: Pydantic data model representing SQL query information and metadata

## Requirements

### Requirement 1: Collect Full SQL Query Text

**User Story:** As a database administrator, I want to see the complete SQL query text without truncation, so that I can understand the full context of complex queries causing performance issues.

#### Acceptance Criteria

1. WHEN Performance Insights API returns SQL query text, THE SQL_Query_Collector SHALL retrieve the complete text without truncation
2. WHEN a SQL query exceeds 500 characters, THE SQL_Query_Collector SHALL store the full text in the SQLQuery_Model
3. WHEN Performance Insights API provides truncated text, THE SQL_Query_Collector SHALL attempt to retrieve the full text using the SQL_ID
4. THE SQLQuery_Model SHALL support storing SQL query text of at least 10,000 characters
5. FOR ALL collected SQL queries, storing then retrieving the text SHALL preserve the exact original content (round-trip property)

### Requirement 2: Collect SQL Execution Metrics

**User Story:** As a database administrator, I want to see comprehensive execution metrics for each SQL query, so that I can identify which queries consume the most resources.

#### Acceptance Criteria

1. WHEN querying Performance Insights API, THE SQL_Query_Collector SHALL request SQL_ID for each query
2. WHEN querying Performance Insights API, THE SQL_Query_Collector SHALL request executions per second (calls/sec) for each query if available
3. WHEN querying Performance Insights API, THE SQL_Query_Collector SHALL request total execution time for each query
4. WHEN querying Performance Insights API, THE SQL_Query_Collector SHALL request average execution time per call if available from the API
5. WHEN querying Performance Insights API, THE SQL_Query_Collector SHALL request execution count for each query
6. THE SQLQuery_Model SHALL include fields for SQL_ID, executions_per_second, total_execution_time, average_execution_time, and execution_count
7. WHEN a metric is not provided by Performance_Insights_API, THE SQL_Query_Collector SHALL store null for that field without calculation

### Requirement 3: Collect Advanced SQL Metrics

**User Story:** As a database administrator, I want to see detailed resource consumption metrics for SQL queries, so that I can understand CPU usage, I/O patterns, and locking behavior.

#### Acceptance Criteria

1. WHEN the RDS_Engine supports CPU time metrics, THE SQL_Query_Collector SHALL request CPU time for each query
2. WHEN the RDS_Engine supports lock time metrics, THE SQL_Query_Collector SHALL request lock time for each query
3. WHEN the RDS_Engine supports rows examined metrics, THE SQL_Query_Collector SHALL request rows examined for each query
4. WHEN the RDS_Engine supports rows returned metrics, THE SQL_Query_Collector SHALL request rows returned for each query
5. WHEN the RDS_Engine supports I/O metrics, THE SQL_Query_Collector SHALL request read and write I/O statistics for each query
6. THE SQLQuery_Model SHALL include optional fields for cpu_time, lock_time, rows_examined, rows_returned, and io_statistics

### Requirement 4: Handle Engine-Specific Metric Availability

**User Story:** As a database administrator working with multiple RDS engine types, I want the tool to collect all available metrics for each engine type, so that I get the most comprehensive information regardless of the database engine.

#### Acceptance Criteria

1. WHEN collecting metrics for a specific RDS_Engine, THE SQL_Query_Collector SHALL query only metrics supported by that engine type
2. WHEN a metric is not available for an RDS_Engine, THE SQL_Query_Collector SHALL continue collection without errors
3. WHEN a metric is not available for an RDS_Engine, THE SQLQuery_Model SHALL store null for that metric field
4. THE SQL_Query_Collector SHALL maintain a mapping of available metrics per RDS_Engine type
5. WHEN encountering an unknown RDS_Engine type, THE SQL_Query_Collector SHALL attempt to collect all standard metrics and log unavailable metrics

### Requirement 5: Parse Performance Insights API Response

**User Story:** As a developer, I want the SQL query collector to correctly parse Performance Insights API responses, so that all available metadata is extracted and stored accurately.

#### Acceptance Criteria

1. WHEN Performance_Insights_API returns dimension keys, THE SQL_Query_Collector SHALL extract SQL_ID from each dimension key
2. WHEN Performance_Insights_API returns metric data, THE SQL_Query_Collector SHALL parse all requested metrics for each SQL_ID
3. WHEN Performance_Insights_API returns metric data, THE SQL_Query_Collector SHALL store the values exactly as provided by the API without aggregation or calculation
4. IF Performance_Insights_API returns incomplete metric data, THEN THE SQL_Query_Collector SHALL log a warning and store available metrics
5. THE SQL_Query_Collector SHALL validate that parsed metric values are within expected ranges (non-negative for counts and times)

### Requirement 6: Format Enhanced SQL Information in Reports

**User Story:** As a database administrator, I want diagnostic reports to display the enhanced SQL information in a clear and readable format, so that I can quickly identify problematic queries.

#### Acceptance Criteria

1. WHEN generating a technical report, THE Report_Formatter SHALL display the full SQL query text with proper formatting
2. WHEN generating a technical report, THE Report_Formatter SHALL display all collected SQL_Metadata in a structured table format
3. WHEN SQL query text exceeds 100 lines, THE Report_Formatter SHALL provide a summary view with an option to see full text
4. WHEN displaying multiple SQL queries, THE Report_Formatter SHALL sort them by total execution time in descending order
5. WHEN a metric is not available for a query, THE Report_Formatter SHALL display "N/A" instead of null or empty values
6. THE Report_Formatter SHALL include metric units in the display (e.g., "ms" for milliseconds, "calls/sec" for execution rate)

### Requirement 7: Maintain Backward Compatibility

**User Story:** As an existing user of the RDS Diagnostics Tool, I want the enhanced SQL collection to work seamlessly with my existing configurations and workflows, so that I don't need to modify my setup.

#### Acceptance Criteria

1. WHEN Performance Insights is not enabled for an RDS instance, THE SQL_Query_Collector SHALL handle the error gracefully as before
2. WHEN the enhanced collection fails, THE SQL_Query_Collector SHALL fall back to the previous collection method
3. THE SQLQuery_Model SHALL maintain all existing fields from the previous version
4. WHEN generating reports with enhanced data, THE Report_Formatter SHALL maintain the existing report structure and add new sections for enhanced metrics
5. THE SQL_Query_Collector SHALL maintain the existing configuration options for time ranges and query limits

### Requirement 8: Handle API Rate Limits and Errors

**User Story:** As a database administrator querying multiple RDS instances, I want the tool to handle AWS API rate limits gracefully, so that my diagnostic runs complete successfully without manual intervention.

#### Acceptance Criteria

1. WHEN Performance_Insights_API returns a rate limit error, THE SQL_Query_Collector SHALL implement exponential backoff retry logic
2. WHEN Performance_Insights_API returns a rate limit error, THE SQL_Query_Collector SHALL retry up to 3 times before failing
3. IF Performance_Insights_API returns an authentication error, THEN THE SQL_Query_Collector SHALL provide a clear error message with remediation steps
4. IF Performance_Insights_API returns a service unavailable error, THEN THE SQL_Query_Collector SHALL log the error and continue with remaining instances
5. WHEN collecting metrics for multiple SQL queries, THE SQL_Query_Collector SHALL batch API requests to minimize API calls

### Requirement 9: Optimize API Call Efficiency

**User Story:** As a developer, I want the SQL query collector to minimize AWS API calls, so that diagnostic runs complete quickly and reduce AWS costs.

#### Acceptance Criteria

1. WHEN requesting multiple metrics for SQL queries, THE SQL_Query_Collector SHALL use a single Performance_Insights_API call with multiple metric specifications
2. WHEN collecting data for a time range, THE SQL_Query_Collector SHALL request all metrics for that time range in one batch
3. THE SQL_Query_Collector SHALL cache RDS_Engine type information to avoid repeated describe_db_instances calls
4. WHEN the same SQL_ID appears multiple times, THE SQL_Query_Collector SHALL deduplicate requests for full SQL text
5. THE SQL_Query_Collector SHALL limit the number of top SQL queries collected to a configurable maximum (default: 25)

### Requirement 10: Validate Collected Metrics

**User Story:** As a database administrator, I want the tool to validate collected metrics for basic sanity checks, so that I can trust the diagnostic results.

#### Acceptance Criteria

1. WHEN collecting time-based metrics, THE SQL_Query_Collector SHALL verify that values are non-negative
2. WHEN collecting rate-based metrics (calls/sec), THE SQL_Query_Collector SHALL verify that values are non-negative
3. WHEN collecting count-based metrics, THE SQL_Query_Collector SHALL verify that values are non-negative integers
4. IF a metric value is invalid (negative, infinity, NaN), THEN THE SQL_Query_Collector SHALL log a warning and set the metric to null
5. THE SQL_Query_Collector SHALL store all metrics exactly as provided by Performance_Insights_API without modification or calculation

### Requirement 11: Support JSON Report Format

**User Story:** As a developer integrating RDS diagnostics into automated workflows, I want enhanced SQL metadata available in JSON format, so that I can programmatically process the results.

#### Acceptance Criteria

1. WHEN generating a JSON report, THE Report_Formatter SHALL include all enhanced SQL_Metadata fields
2. WHEN generating a JSON report, THE Report_Formatter SHALL use consistent field naming (snake_case)
3. WHEN a metric is not available, THE Report_Formatter SHALL include the field with a null value in JSON output
4. THE Report_Formatter SHALL ensure JSON output is valid and parsable
5. FOR ALL JSON reports, parsing then serializing the report SHALL produce equivalent data (round-trip property)

### Requirement 12: Configure Metric Collection Preferences

**User Story:** As a database administrator, I want to configure which SQL metrics are collected, so that I can focus on the metrics most relevant to my troubleshooting needs.

#### Acceptance Criteria

1. WHERE metric collection preferences are configured, THE SQL_Query_Collector SHALL collect only the specified metrics
2. WHERE no metric preferences are configured, THE SQL_Query_Collector SHALL collect all available metrics for the RDS_Engine
3. THE Configuration SHALL support enabling or disabling collection of advanced metrics (CPU time, lock time, I/O statistics)
4. THE Configuration SHALL support setting the maximum number of SQL queries to collect per instance
5. THE Configuration SHALL validate that at least basic metrics (SQL text, execution time, execution count) are always collected

### Requirement 13: Generate SQL Performance Recommendations

**User Story:** As a database administrator, I want the tool to analyze SQL query metrics and provide actionable recommendations, so that I can identify optimization opportunities.

#### Acceptance Criteria

1. WHEN SQL queries have both total_execution_time and execution_count available, THE Recommendation_Generator SHALL calculate efficiency metrics and identify inefficient queries
2. WHEN a SQL query has high execution time but low execution count, THE Recommendation_Generator SHALL flag it as a candidate for optimization
3. WHEN a SQL query has high execution count but low individual execution time, THE Recommendation_Generator SHALL flag it as a candidate for caching or result set optimization
4. WHEN rows_examined is significantly higher than rows_returned, THE Recommendation_Generator SHALL suggest index optimization
5. WHEN lock_time is a significant percentage of total_execution_time, THE Recommendation_Generator SHALL suggest reviewing transaction isolation levels or query patterns
6. WHEN cpu_time is disproportionately high, THE Recommendation_Generator SHALL suggest query optimization or hardware scaling
7. THE Recommendation_Generator SHALL include calculated metrics (e.g., efficiency ratios, percentages) only in the recommendations section, not in the raw data display
8. THE Recommendation_Generator SHALL prioritize recommendations by potential impact (queries with highest total execution time first)
