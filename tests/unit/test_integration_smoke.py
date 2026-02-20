"""Smoke tests to verify components integrate correctly."""

import pytest
from datetime import datetime, timedelta

from core.models import (
    RDSInstanceInfo, CloudWatchMetrics, MetricSeries, MetricDataPoint,
    IOPSMetrics, StorageMetrics, DiagnosticData, MetricAnalysis,
    Severity, TimeRange
)
from core.config import MetricThresholds
from analysis.analyzer import DiagnosticAnalyzer, QueryAnalyzer
from reporting.generator import ReportGenerator
from reporting.formatters import TechnicalReportFormatter, ManagementReportFormatter
from core.models import ReportType, OutputFormat


class TestIntegrationSmoke:
    """Smoke tests for component integration."""
    
    def test_analyzer_with_sample_data(self):
        """Test analyzer can process sample metrics."""
        # Create sample instance info
        instance_info = RDSInstanceInfo(
            instance_id="test-db",
            resource_id="db-TEST123",
            engine="postgres",
            engine_version="14.7",
            instance_class="db.t3.medium",
            status="available",
            storage_type="gp2",
            allocated_storage=100,
            max_connections=500,
            availability_zone="ap-southeast-1a"
        )
        
        # Create sample metrics
        now = datetime.now()
        cpu_points = [
            MetricDataPoint(now - timedelta(minutes=10), 85.0, "Percent"),
            MetricDataPoint(now - timedelta(minutes=5), 90.0, "Percent"),
            MetricDataPoint(now, 95.0, "Percent"),
        ]
        
        memory_points = [
            MetricDataPoint(now, 500_000_000, "Bytes")  # 500MB
        ]
        
        conn_points = [
            MetricDataPoint(now, 450, "Count")  # 90% of max
        ]
        
        iops = IOPSMetrics(
            read_iops=MetricSeries("ReadIOPS", [], "Count/Second"),
            write_iops=MetricSeries("WriteIOPS", [], "Count/Second")
        )
        
        storage = StorageMetrics(
            free_storage=MetricSeries("FreeStorage", [
                MetricDataPoint(now, 10_000_000_000, "Bytes")
            ], "Bytes"),
            used_storage=MetricSeries("UsedStorage", [
                MetricDataPoint(now, 90_000_000_000, "Bytes")
            ], "Bytes"),
            total_storage=100_000_000_000
        )
        
        metrics = CloudWatchMetrics(
            instance_info=instance_info,
            cpu_utilization=MetricSeries("CPUUtilization", cpu_points, "Percent"),
            freeable_memory=MetricSeries("FreeableMemory", memory_points, "Bytes"),
            database_connections=MetricSeries("DatabaseConnections", conn_points, "Count"),
            iops=iops,
            storage=storage,
            collection_time=now
        )
        
        # Analyze metrics
        thresholds = MetricThresholds()
        analyzer = DiagnosticAnalyzer(thresholds)
        analysis = analyzer.analyze_metrics(metrics)
        
        # Verify analysis results
        assert analysis.overall_severity == Severity.CRITICAL
        assert len(analysis.violations) > 0
        assert any(v.metric_name == "CPUUtilization" for v in analysis.violations)
    
    def test_report_generation(self):
        """Test report generation from diagnostic data."""
        # Create minimal diagnostic data
        instance_info = RDSInstanceInfo(
            instance_id="test-db",
            resource_id="db-TEST123",
            engine="postgres",
            engine_version="14.7",
            instance_class="db.t3.medium",
            status="available",
            storage_type="gp2",
            allocated_storage=100,
            max_connections=500,
            availability_zone="ap-southeast-1a"
        )
        
        now = datetime.now()
        metrics = CloudWatchMetrics(
            instance_info=instance_info,
            cpu_utilization=MetricSeries("CPUUtilization", [], "Percent"),
            freeable_memory=MetricSeries("FreeableMemory", [], "Bytes"),
            database_connections=MetricSeries("DatabaseConnections", [], "Count"),
            iops=IOPSMetrics(
                read_iops=MetricSeries("ReadIOPS", [], "Count/Second"),
                write_iops=MetricSeries("WriteIOPS", [], "Count/Second")
            ),
            storage=StorageMetrics(
                free_storage=MetricSeries("FreeStorage", [], "Bytes"),
                used_storage=MetricSeries("UsedStorage", [], "Bytes"),
                total_storage=100_000_000_000
            ),
            collection_time=now
        )
        
        analysis = MetricAnalysis(
            violations=[],
            trends=[],
            overall_severity=Severity.NORMAL,
            summary="All metrics normal"
        )
        
        diagnostic_data = DiagnosticData(
            instance_info=instance_info,
            cloudwatch_metrics=metrics,
            performance_insights_queries=None,
            wait_events=None,
            top_databases=None,
            top_users=None,
            analysis=analysis,
            recommendations=["Continue monitoring"],
            collection_timestamp=now
        )
        
        # Generate technical report
        generator = ReportGenerator()
        tech_report = generator.generate_report(
            diagnostic_data,
            ReportType.TECHNICAL,
            OutputFormat.TEXT
        )
        
        assert tech_report.content is not None
        assert len(tech_report.content) > 0
        assert "TECHNICAL" in tech_report.content
        assert "test-db" in tech_report.content
        
        # Generate management report
        mgmt_report = generator.generate_report(
            diagnostic_data,
            ReportType.MANAGEMENT,
            OutputFormat.TEXT
        )
        
        assert mgmt_report.content is not None
        assert len(mgmt_report.content) > 0
        assert "EXECUTIVE SUMMARY" in mgmt_report.content
        
        # Generate JSON report
        json_report = generator.generate_report(
            diagnostic_data,
            ReportType.TECHNICAL,
            OutputFormat.JSON
        )
        
        assert json_report.content is not None
        assert json_report.content.startswith("{")
        assert "test-db" in json_report.content
    
    def test_time_range_parsing(self):
        """Test TimeRange parsing works correctly."""
        # Test various duration formats
        time_range_1h = TimeRange.from_duration("1h")
        assert (time_range_1h.end - time_range_1h.start).total_seconds() >= 3600
        
        time_range_24h = TimeRange.from_duration("24h")
        assert (time_range_24h.end - time_range_24h.start).total_seconds() >= 86400
        
        time_range_7d = TimeRange.from_duration("7d")
        assert (time_range_7d.end - time_range_7d.start).total_seconds() >= 604800
