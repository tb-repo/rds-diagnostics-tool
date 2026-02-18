"""Unit tests for core data models."""

import pytest
from datetime import datetime, timedelta
from core.models import (
    TimeRange, MetricDataPoint, MetricSeries, IOPSMetrics,
    StorageMetrics, Severity, Trend, ReportType, OutputFormat
)


class TestTimeRange:
    """Tests for TimeRange model."""
    
    def test_from_duration_hours(self):
        """Test parsing hour duration."""
        time_range = TimeRange.from_duration("1h")
        duration = time_range.end - time_range.start
        assert abs(duration.total_seconds() - 3600) < 10  # Within 10 seconds
    
    def test_from_duration_days(self):
        """Test parsing day duration."""
        time_range = TimeRange.from_duration("7d")
        duration = time_range.end - time_range.start
        assert abs(duration.total_seconds() - (7 * 24 * 3600)) < 10
    
    def test_from_duration_invalid_format(self):
        """Test invalid duration format raises error."""
        with pytest.raises(ValueError, match="Invalid duration format"):
            TimeRange.from_duration("invalid")
    
    def test_from_duration_invalid_unit(self):
        """Test invalid time unit raises error."""
        with pytest.raises(ValueError, match="Invalid duration format"):
            TimeRange.from_duration("5m")


class TestMetricSeries:
    """Tests for MetricSeries model."""
    
    def test_get_average_empty(self):
        """Test average of empty series."""
        series = MetricSeries("TestMetric", [], "Count")
        assert series.get_average() == 0.0
    
    def test_get_average(self):
        """Test average calculation."""
        points = [
            MetricDataPoint(datetime.now(), 10.0, "Count"),
            MetricDataPoint(datetime.now(), 20.0, "Count"),
            MetricDataPoint(datetime.now(), 30.0, "Count"),
        ]
        series = MetricSeries("TestMetric", points, "Count")
        assert series.get_average() == 20.0
    
    def test_get_max(self):
        """Test max calculation."""
        points = [
            MetricDataPoint(datetime.now(), 10.0, "Count"),
            MetricDataPoint(datetime.now(), 50.0, "Count"),
            MetricDataPoint(datetime.now(), 30.0, "Count"),
        ]
        series = MetricSeries("TestMetric", points, "Count")
        assert series.get_max() == 50.0
    
    def test_get_min(self):
        """Test min calculation."""
        points = [
            MetricDataPoint(datetime.now(), 10.0, "Count"),
            MetricDataPoint(datetime.now(), 50.0, "Count"),
            MetricDataPoint(datetime.now(), 30.0, "Count"),
        ]
        series = MetricSeries("TestMetric", points, "Count")
        assert series.get_min() == 10.0
    
    def test_get_latest(self):
        """Test getting latest data point."""
        now = datetime.now()
        points = [
            MetricDataPoint(now - timedelta(minutes=10), 10.0, "Count"),
            MetricDataPoint(now - timedelta(minutes=5), 20.0, "Count"),
            MetricDataPoint(now, 30.0, "Count"),
        ]
        series = MetricSeries("TestMetric", points, "Count")
        latest = series.get_latest()
        assert latest.value == 30.0
    
    def test_get_latest_empty(self):
        """Test getting latest from empty series."""
        series = MetricSeries("TestMetric", [], "Count")
        assert series.get_latest() is None


class TestIOPSMetrics:
    """Tests for IOPSMetrics model."""
    
    def test_get_total_iops_series(self):
        """Test combining read and write IOPS."""
        now = datetime.now()
        read_points = [
            MetricDataPoint(now, 100.0, "Count/Second"),
            MetricDataPoint(now + timedelta(minutes=5), 150.0, "Count/Second"),
        ]
        write_points = [
            MetricDataPoint(now, 50.0, "Count/Second"),
            MetricDataPoint(now + timedelta(minutes=5), 75.0, "Count/Second"),
        ]
        
        read_series = MetricSeries("ReadIOPS", read_points, "Count/Second")
        write_series = MetricSeries("WriteIOPS", write_points, "Count/Second")
        iops = IOPSMetrics(read_series, write_series)
        
        total = iops.get_total_iops_series()
        assert len(total.data_points) == 2
        assert total.data_points[0].value == 150.0
        assert total.data_points[1].value == 225.0


class TestStorageMetrics:
    """Tests for StorageMetrics model."""
    
    def test_get_usage_percentage(self):
        """Test storage usage percentage calculation."""
        now = datetime.now()
        free_points = [MetricDataPoint(now, 20_000_000_000, "Bytes")]
        used_points = [MetricDataPoint(now, 80_000_000_000, "Bytes")]
        
        free_series = MetricSeries("FreeStorage", free_points, "Bytes")
        used_series = MetricSeries("UsedStorage", used_points, "Bytes")
        storage = StorageMetrics(free_series, used_series, 100_000_000_000)
        
        usage = storage.get_usage_percentage()
        assert usage == 80.0
    
    def test_get_usage_percentage_zero_total(self):
        """Test usage percentage with zero total storage."""
        free_series = MetricSeries("FreeStorage", [], "Bytes")
        used_series = MetricSeries("UsedStorage", [], "Bytes")
        storage = StorageMetrics(free_series, used_series, 0)
        
        assert storage.get_usage_percentage() == 0.0


class TestEnums:
    """Tests for enum types."""
    
    def test_severity_enum(self):
        """Test Severity enum values."""
        assert Severity.NORMAL.value == "normal"
        assert Severity.WARNING.value == "warning"
        assert Severity.CRITICAL.value == "critical"
    
    def test_trend_enum(self):
        """Test Trend enum values."""
        assert Trend.IMPROVING.value == "improving"
        assert Trend.DEGRADING.value == "degrading"
        assert Trend.STABLE.value == "stable"
    
    def test_report_type_enum(self):
        """Test ReportType enum values."""
        assert ReportType.TECHNICAL.value == "technical"
        assert ReportType.MANAGEMENT.value == "management"
    
    def test_output_format_enum(self):
        """Test OutputFormat enum values."""
        assert OutputFormat.TEXT.value == "text"
        assert OutputFormat.JSON.value == "json"
