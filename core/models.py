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
        
        Supported formats: "1h", "24h", "7d", "30d"
        """
        pattern = r"^(\d+)([hd])$"
        match = re.match(pattern, duration_str.lower())
        
        if not match:
            raise ValueError(
                f"Invalid duration format: {duration_str}. "
                "Expected format: <number><h|d> (e.g., '1h', '24h', '7d')"
            )
        
        value = int(match.group(1))
        unit = match.group(2)
        
        end = datetime.now()
        
        if unit == "h":
            start = end - timedelta(hours=value)
        elif unit == "d":
            start = end - timedelta(days=value)
        else:
            raise ValueError(f"Unsupported time unit: {unit}")
        
        return TimeRange(start=start, end=end)


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
    """Information about a SQL query from Performance Insights."""
    query_id: str
    query_text: str
    total_execution_time: float
    average_execution_time: float
    execution_count: int
    rows_affected: Optional[int] = None
    wait_events: List[str] = field(default_factory=list)


@dataclass
class WaitEvent:
    """Wait event information from Performance Insights."""
    event_name: str
    total_wait_time: float
    wait_count: int


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
    analysis: MetricAnalysis
    recommendations: List[str]
    collection_timestamp: datetime


# Report
@dataclass
class Report:
    """A generated report."""
    report_type: ReportType
    content: str
    format: OutputFormat
    generated_at: datetime
