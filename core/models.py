"""Core data models for RDS Diagnostics Tool."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional
import re


# Enums
class Severity(Enum):
    """Severity levels for violations and overall assessment."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


class Trend(Enum):
    """Trend direction for metric analysis."""
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"


class ReportType(Enum):
    """Type of report to generate."""
    TECHNICAL = "technical"
    MANAGEMENT = "management"


class OutputFormat(Enum):
    """Output format for reports."""
    TEXT = "text"
    JSON = "json"


# Time Range
@dataclass
class TimeRange:
    """Represents a time range for metric collection."""
    start: datetime
    end: datetime
    
    @staticmethod
    def from_duration(duration_str: str) -> "TimeRange":
        """
        Parse duration string and create TimeRange.
        
        Supported formats: "15m", "1h", "24h", "7d", "30d"
        """
        pattern = r"^(\d+)([mhd])$"
        match = re.match(pattern, duration_str.lower())
        
        if not match:
            raise ValueError(
                f"Invalid duration format: {duration_str}. "
                "Expected format: <number><m|h|d> (e.g., '15m', '1h', '24h', '7d')"
            )
        
        value = int(match.group(1))
        unit = match.group(2)
        
        # Use UTC time to match AWS API expectations
        end = datetime.utcnow()
        
        if unit == "m":
            start = end - timedelta(minutes=value)
        elif unit == "h":
            start = end - timedelta(hours=value)
        elif unit == "d":
            start = end - timedelta(days=value)
        else:
            raise ValueError(f"Unsupported time unit: {unit}")
        
        return TimeRange(start=start, end=end)
    
    @staticmethod
    def from_timestamps(start_str: str, end_str: str) -> "TimeRange":
        """
        Parse start and end timestamp strings and create TimeRange.
        
        Supported formats:
        - ISO 8601: "2026-03-02T10:00:00" or "2026-03-02T10:00:00Z"
        - Date only: "2026-03-02" (assumes 00:00:00)
        - Date and time: "2026-03-02 10:00:00"
        
        Args:
            start_str: Start timestamp string
            end_str: End timestamp string
            
        Returns:
            TimeRange object with parsed start and end times
            
        Raises:
            ValueError: If timestamp format is invalid or end is before start
        """
        from dateutil import parser
        
        try:
            # Parse start time
            start = parser.parse(start_str)
            # If no timezone info, assume UTC
            if start.tzinfo is None:
                start = start.replace(tzinfo=None)
                # Convert to UTC-aware datetime
                start_utc = start
            else:
                # Convert to UTC
                start_utc = start.astimezone(None).replace(tzinfo=None)
            
            # Parse end time
            end = parser.parse(end_str)
            # If no timezone info, assume UTC
            if end.tzinfo is None:
                end = end.replace(tzinfo=None)
                end_utc = end
            else:
                end_utc = end.astimezone(None).replace(tzinfo=None)
            
            # Validate time range
            if end_utc <= start_utc:
                raise ValueError(
                    f"End time ({end_str}) must be after start time ({start_str})"
                )
            
            # Check if time range is too large (max 30 days)
            duration = end_utc - start_utc
            if duration.days > 30:
                raise ValueError(
                    f"Time range too large: {duration.days} days. Maximum is 30 days."
                )
            
            return TimeRange(start=start_utc, end=end_utc)
            
        except (ValueError, parser.ParserError) as e:
            raise ValueError(
                f"Invalid timestamp format: {e}. "
                "Expected formats: '2026-03-02T10:00:00', '2026-03-02 10:00:00', or '2026-03-02'"
            )


# RDS Instance Information
@dataclass
class RDSInstanceInfo:
    """Information about an RDS instance."""
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


# Metric Data Structures
@dataclass
class MetricDataPoint:
    """A single data point for a metric."""
    timestamp: datetime
    value: float
    unit: str


@dataclass
class MetricSeries:
    """A time series of metric data points."""
    metric_name: str
    data_points: List[MetricDataPoint]
    unit: str
    
    def get_average(self) -> float:
        """Calculate average value across all data points."""
        if not self.data_points:
            return 0.0
        return sum(dp.value for dp in self.data_points) / len(self.data_points)
    
    def get_max(self) -> float:
        """Get maximum value from data points."""
        if not self.data_points:
            return 0.0
        return max(dp.value for dp in self.data_points)
    
    def get_min(self) -> float:
        """Get minimum value from data points."""
        if not self.data_points:
            return 0.0
        return min(dp.value for dp in self.data_points)
    
    def get_latest(self) -> Optional[MetricDataPoint]:
        """Get the most recent data point."""
        if not self.data_points:
            return None
        return max(self.data_points, key=lambda dp: dp.timestamp)


@dataclass
class IOPSMetrics:
    """IOPS metrics for read and write operations."""
    read_iops: MetricSeries
    write_iops: MetricSeries
    
    def get_total_iops_series(self) -> MetricSeries:
        """Calculate total IOPS by combining read and write."""
        if not self.read_iops.data_points or not self.write_iops.data_points:
            return MetricSeries(
                metric_name="TotalIOPS",
                data_points=[],
                unit="Count/Second"
            )
        
        # Create a map of timestamps to values
        read_map = {dp.timestamp: dp.value for dp in self.read_iops.data_points}
        write_map = {dp.timestamp: dp.value for dp in self.write_iops.data_points}
        
        # Combine at matching timestamps
        combined_points = []
        for timestamp in read_map.keys():
            if timestamp in write_map:
                combined_points.append(
                    MetricDataPoint(
                        timestamp=timestamp,
                        value=read_map[timestamp] + write_map[timestamp],
                        unit="Count/Second"
                    )
                )
        
        return MetricSeries(
            metric_name="TotalIOPS",
            data_points=combined_points,
            unit="Count/Second"
        )


@dataclass
class StorageMetrics:
    """Storage metrics for an RDS instance."""
    free_storage: MetricSeries
    used_storage: MetricSeries
    total_storage: int  # in bytes
    
    def get_usage_percentage(self) -> float:
        """Calculate storage usage as a percentage."""
        if self.total_storage == 0:
            return 0.0
        
        latest_used = self.used_storage.get_latest()
        if not latest_used:
            return 0.0
        
        return (latest_used.value / self.total_storage) * 100


@dataclass
class CloudWatchMetrics:
    """Complete set of CloudWatch metrics for an RDS instance."""
    instance_info: RDSInstanceInfo
    cpu_utilization: MetricSeries
    freeable_memory: MetricSeries
    database_connections: MetricSeries
    iops: IOPSMetrics
    storage: StorageMetrics
    collection_time: datetime


# Performance Insights Data
@dataclass
class SQLQuery:
    """
    Information about a SQL query from Performance Insights.
    
    Fields are divided into three categories:
    1. Core fields (always present) - query_id, query_text, execution metrics
    2. Basic metrics (usually present) - total_execution_time, average_execution_time, execution_count
    3. Enhanced metrics (engine-dependent, optional) - cpu_time, lock_time, rows metrics, I/O metrics
    
    All enhanced metrics are Optional to maintain backward compatibility and handle
    engine-specific metric availability gracefully.
    """
    # Core identification fields (required)
    query_id: str
    query_text: str
    total_execution_time: float
    average_execution_time: float
    execution_count: int
    
    # Basic optional fields (existing, maintained for backward compatibility)
    rows_affected: Optional[int] = None
    wait_events: List[str] = field(default_factory=list)
    
    # Enhanced optional fields (new - engine-dependent)
    engine_type: Optional[str] = None  # e.g., 'mysql', 'postgres', 'aurora-mysql'
    executions_per_second: Optional[float] = None  # Calls per second
    cpu_time: Optional[float] = None  # CPU time in milliseconds
    lock_time: Optional[float] = None  # Lock wait time in milliseconds
    rows_examined: Optional[int] = None  # Rows scanned
    rows_returned: Optional[int] = None  # Rows returned to client
    read_io_bytes: Optional[int] = None  # Bytes read from storage
    write_io_bytes: Optional[int] = None  # Bytes written to storage
    read_io_time: Optional[float] = None  # Read I/O time in milliseconds (Aurora PG 17+)
    write_io_time: Optional[float] = None  # Write I/O time in milliseconds (Aurora PG 17+)
    rows_per_second: Optional[float] = None  # Rows processed per second (Aurora PG 17+)


@dataclass
class WaitEvent:
    """Wait event information from Performance Insights."""
    event_name: str
    total_wait_time: float
    wait_count: int


@dataclass
class TopDatabase:
    """Top database by load from Performance Insights."""
    database_name: str
    total_load: float
    load_percentage: float


@dataclass
class TopUser:
    """Top user by load from Performance Insights."""
    user_name: str
    total_load: float
    load_percentage: float


@dataclass
class OSMetrics:
    """
    OS-level performance metrics from Performance Insights.
    
    These metrics provide system-level insights that help correlate
    database performance with underlying infrastructure health.
    """
    # CPU metrics
    cpu_total: Optional[float] = None  # Total CPU utilization %
    cpu_user: Optional[float] = None  # User space CPU %
    cpu_system: Optional[float] = None  # System/kernel CPU %
    cpu_wait: Optional[float] = None  # I/O wait % (key indicator of I/O bottleneck)
    
    # Memory metrics (in GB)
    memory_free_gb: Optional[float] = None
    memory_active_gb: Optional[float] = None
    memory_cached_gb: Optional[float] = None
    
    # Disk I/O metrics - KEY METRICS FOR PERFORMANCE ANALYSIS
    read_iops: Optional[float] = None  # Read operations per second
    write_iops: Optional[float] = None  # Write operations per second
    read_latency_ms: Optional[float] = None  # Read latency in milliseconds
    write_latency_ms: Optional[float] = None  # Write latency in milliseconds
    read_throughput_kbps: Optional[float] = None  # Read throughput in KB/s
    write_throughput_kbps: Optional[float] = None  # Write throughput in KB/s
    disk_queue_depth: Optional[float] = None  # Average queue depth (I/O bottleneck indicator)
    disk_await_ms: Optional[float] = None  # Average wait time in milliseconds
    disk_utilization_pct: Optional[float] = None  # Disk utilization percentage
    
    # Temp usage metrics (PostgreSQL specific)
    temp_blocks_read: Optional[float] = None  # Temp blocks read (queries spilling to disk)
    temp_blocks_written: Optional[float] = None  # Temp blocks written
    
    # Swap metrics (in GB)
    swap_free_gb: Optional[float] = None
    swap_in_rate: Optional[float] = None  # Swap in rate (memory pressure indicator)
    swap_out_rate: Optional[float] = None  # Swap out rate
    
    # Load average
    load_avg_1min: Optional[float] = None
    load_avg_5min: Optional[float] = None


# Analysis Results
@dataclass
class Violation:
    """Represents a threshold violation."""
    metric_name: str
    severity: Severity
    current_value: float
    threshold_value: float
    timestamp: datetime
    message: str


@dataclass
class TrendAnalysis:
    """Trend analysis for a metric."""
    metric_name: str
    trend: Trend
    change_percentage: float
    description: str


@dataclass
class MetricAnalysis:
    """Complete analysis of collected metrics."""
    violations: List[Violation]
    trends: List[TrendAnalysis]
    overall_severity: Severity
    summary: str


# Diagnostic Data
@dataclass
class DiagnosticData:
    """Complete diagnostic data for an RDS instance."""
    instance_info: RDSInstanceInfo
    cloudwatch_metrics: CloudWatchMetrics
    performance_insights_queries: Optional[List[SQLQuery]]
    wait_events: Optional[List[WaitEvent]]
    top_databases: Optional[List["TopDatabase"]]
    top_users: Optional[List["TopUser"]]
    analysis: MetricAnalysis
    recommendations: List[str]
    collection_timestamp: datetime
    os_metrics: Optional[OSMetrics] = None  # OS-level metrics from Performance Insights


# Report
@dataclass
class Report:
    """A generated report."""
    report_type: ReportType
    content: str
    format: OutputFormat
    generated_at: datetime
