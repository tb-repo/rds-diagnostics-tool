"""Unit tests for SQLQuery JSON serialization with enhanced fields."""

import json
import pytest
from datetime import datetime
from core.models import (
    SQLQuery, DiagnosticData, RDSInstanceInfo, CloudWatchMetrics,
    MetricAnalysis, MetricSeries, MetricDataPoint, IOPSMetrics,
    StorageMetrics, Severity
)
from reporting.formatters import TechnicalReportFormatter


class TestSQLQueryJSONSerialization:
    """Test suite for SQLQuery JSON serialization."""
    
    def test_json_serialization_with_basic_fields(self):
        """Test JSON serialization with only basic SQLQuery fields."""
        query = SQLQuery(
            query_id="sql-123",
            query_text="SELECT * FROM users",
            total_execution_time=100.0,
            average_execution_time=10.0,
            execution_count=10
        )
        
        # Create minimal diagnostic data for JSON formatting
        diagnostic_data = self._create_diagnostic_data([query])
        
        # Generate JSON
        json_output = TechnicalReportFormatter.format_json(diagnostic_data)
        
        # Parse JSON to verify it's valid
        data = json.loads(json_output)
        
        # Verify query data is present
        assert "performance_insights" in data
        assert "top_queries" in data["performance_insights"]
        assert len(data["performance_insights"]["top_queries"]) == 1
        
        query_data = data["performance_insights"]["top_queries"][0]
        assert query_data["query_id"] == "sql-123"
        assert query_data["query_text"] == "SELECT * FROM users"
        assert query_data["total_load_aas"] == 100.0
        
        # Verify enhanced fields are present with null values
        assert query_data["engine_type"] is None
        assert query_data["executions_per_second"] is None
        assert query_data["cpu_time"] is None
        assert query_data["lock_time"] is None
        assert query_data["rows_examined"] is None
        assert query_data["rows_returned"] is None
        assert query_data["read_io_bytes"] is None
        assert query_data["write_io_bytes"] is None
    
    def test_json_serialization_with_all_fields(self):
        """Test JSON serialization with all SQLQuery fields populated."""
        query = SQLQuery(
            query_id="sql-456",
            query_text="SELECT id, name FROM products",
            total_execution_time=250.5,
            average_execution_time=25.05,
            execution_count=10,
            rows_affected=100,
            wait_events=["lock/table", "io/file"],
            engine_type="mysql",
            executions_per_second=0.5,
            cpu_time=200.0,
            lock_time=30.0,
            rows_examined=1000,
            rows_returned=100,
            read_io_bytes=1024000,
            write_io_bytes=512000
        )
        
        diagnostic_data = self._create_diagnostic_data([query])
        json_output = TechnicalReportFormatter.format_json(diagnostic_data)
        data = json.loads(json_output)
        
        query_data = data["performance_insights"]["top_queries"][0]
        
        # Verify all fields are present
        assert query_data["query_id"] == "sql-456"
        assert query_data["engine_type"] == "mysql"
        assert query_data["executions_per_second"] == 0.5
        assert query_data["cpu_time"] == 200.0
        assert query_data["lock_time"] == 30.0
        assert query_data["rows_examined"] == 1000
        assert query_data["rows_returned"] == 100
        assert query_data["read_io_bytes"] == 1024000
        assert query_data["write_io_bytes"] == 512000
        assert query_data["rows_affected"] == 100
        assert query_data["wait_events"] == ["lock/table", "io/file"]
    
    def test_json_serialization_with_partial_fields(self):
        """Test JSON serialization with some enhanced fields populated."""
        query = SQLQuery(
            query_id="sql-789",
            query_text="SELECT * FROM orders",
            total_execution_time=150.0,
            average_execution_time=15.0,
            execution_count=10,
            engine_type="postgres",
            cpu_time=120.0,
            rows_returned=50,
            # lock_time, rows_examined not available for postgres
        )
        
        diagnostic_data = self._create_diagnostic_data([query])
        json_output = TechnicalReportFormatter.format_json(diagnostic_data)
        data = json.loads(json_output)
        
        query_data = data["performance_insights"]["top_queries"][0]
        
        # Verify populated fields
        assert query_data["engine_type"] == "postgres"
        assert query_data["cpu_time"] == 120.0
        assert query_data["rows_returned"] == 50
        
        # Verify unpopulated fields are null
        assert query_data["lock_time"] is None
        assert query_data["rows_examined"] is None
    
    def test_json_field_naming_convention(self):
        """
        Property 14: JSON Field Naming Convention
        
        For any field in JSON output, field name SHALL follow snake_case.
        """
        query = SQLQuery(
            query_id="test",
            query_text="SELECT 1",
            total_execution_time=10.0,
            average_execution_time=1.0,
            execution_count=1,
            executions_per_second=0.1,
            cpu_time=5.0,
            lock_time=2.0,
            rows_examined=100,
            rows_returned=10,
            read_io_bytes=1024,
            write_io_bytes=512
        )
        
        diagnostic_data = self._create_diagnostic_data([query])
        json_output = TechnicalReportFormatter.format_json(diagnostic_data)
        data = json.loads(json_output)
        
        query_data = data["performance_insights"]["top_queries"][0]
        
        # Verify all field names are snake_case
        expected_fields = [
            "query_id", "query_text", "total_load_aas", "average_load_aas",
            "time_samples", "wait_events", "rows_affected",
            "engine_type", "executions_per_second", "cpu_time", "lock_time",
            "rows_examined", "rows_returned", "read_io_bytes", "write_io_bytes"
        ]
        
        for field in expected_fields:
            assert field in query_data, f"Field {field} not found in JSON"
            # Verify snake_case (no camelCase)
            assert field == field.lower(), f"Field {field} is not lowercase"
            assert " " not in field, f"Field {field} contains spaces"
    
    def test_json_validity(self):
        """
        Property 15: JSON Validity
        
        For any generated JSON report, output SHALL be valid JSON.
        """
        queries = [
            SQLQuery(
                query_id=f"sql-{i}",
                query_text=f"SELECT * FROM table{i}",
                total_execution_time=float(i * 100),
                average_execution_time=float(i * 10),
                execution_count=10,
                engine_type="mysql" if i % 2 == 0 else "postgres",
                cpu_time=float(i * 50) if i % 2 == 0 else None
            )
            for i in range(5)
        ]
        
        diagnostic_data = self._create_diagnostic_data(queries)
        json_output = TechnicalReportFormatter.format_json(diagnostic_data)
        
        # Should not raise exception
        data = json.loads(json_output)
        
        # Verify structure
        assert isinstance(data, dict)
        assert "performance_insights" in data
        assert "top_queries" in data["performance_insights"]
        assert len(data["performance_insights"]["top_queries"]) == 5
    
    def test_json_round_trip_preservation(self):
        """
        Property 16: JSON Round-Trip Preservation
        
        For any JSON report, parsing then serializing SHALL produce equivalent data.
        """
        query = SQLQuery(
            query_id="sql-roundtrip",
            query_text="SELECT * FROM test",
            total_execution_time=123.45,
            average_execution_time=12.345,
            execution_count=10,
            engine_type="mysql",
            executions_per_second=0.5,
            cpu_time=100.0,
            lock_time=20.0,
            rows_examined=1000,
            rows_returned=100,
            read_io_bytes=2048,
            write_io_bytes=1024
        )
        
        diagnostic_data = self._create_diagnostic_data([query])
        
        # First serialization
        json_output1 = TechnicalReportFormatter.format_json(diagnostic_data)
        data1 = json.loads(json_output1)
        
        # Second serialization (from parsed data)
        json_output2 = json.dumps(data1, indent=2)
        data2 = json.loads(json_output2)
        
        # Verify equivalence
        assert data1 == data2
        
        # Verify query data is preserved
        query1 = data1["performance_insights"]["top_queries"][0]
        query2 = data2["performance_insights"]["top_queries"][0]
        
        assert query1["query_id"] == query2["query_id"]
        assert query1["engine_type"] == query2["engine_type"]
        assert query1["cpu_time"] == query2["cpu_time"]
        assert query1["rows_examined"] == query2["rows_examined"]
    
    def test_json_with_multiple_queries(self):
        """Test JSON serialization with multiple queries."""
        queries = [
            SQLQuery(
                query_id="sql-1",
                query_text="SELECT * FROM users",
                total_execution_time=100.0,
                average_execution_time=10.0,
                execution_count=10,
                engine_type="mysql",
                cpu_time=80.0
            ),
            SQLQuery(
                query_id="sql-2",
                query_text="SELECT * FROM orders",
                total_execution_time=200.0,
                average_execution_time=20.0,
                execution_count=10,
                engine_type="postgres"
                # No cpu_time for postgres in this test
            )
        ]
        
        diagnostic_data = self._create_diagnostic_data(queries)
        json_output = TechnicalReportFormatter.format_json(diagnostic_data)
        data = json.loads(json_output)
        
        top_queries = data["performance_insights"]["top_queries"]
        assert len(top_queries) == 2
        
        # First query has cpu_time
        assert top_queries[0]["cpu_time"] == 80.0
        
        # Second query has null cpu_time
        assert top_queries[1]["cpu_time"] is None
    
    def _create_diagnostic_data(self, queries):
        """Helper to create minimal DiagnosticData for testing."""
        now = datetime.utcnow()
        
        instance_info = RDSInstanceInfo(
            instance_id="test-instance",
            resource_id="db-TEST123",
            engine="mysql",
            engine_version="8.0.35",
            instance_class="db.t3.medium",
            status="available",
            storage_type="gp3",
            allocated_storage=100,
            max_connections=150,
            availability_zone="us-east-1a"
        )
        
        # Create minimal metric data
        metric_point = MetricDataPoint(timestamp=now, value=50.0, unit="Percent")
        metric_series = MetricSeries(
            metric_name="test",
            data_points=[metric_point],
            unit="Percent"
        )
        
        cloudwatch_metrics = CloudWatchMetrics(
            instance_info=instance_info,
            cpu_utilization=metric_series,
            freeable_memory=metric_series,
            database_connections=metric_series,
            iops=IOPSMetrics(read_iops=metric_series, write_iops=metric_series),
            storage=StorageMetrics(
                free_storage=metric_series,
                used_storage=metric_series,
                total_storage=100 * 1024**3
            ),
            collection_time=now
        )
        
        analysis = MetricAnalysis(
            violations=[],
            trends=[],
            overall_severity=Severity.NORMAL,
            summary="Test summary"
        )
        
        return DiagnosticData(
            instance_info=instance_info,
            cloudwatch_metrics=cloudwatch_metrics,
            performance_insights_queries=queries,
            wait_events=None,
            top_databases=None,
            top_users=None,
            analysis=analysis,
            recommendations=[],
            collection_timestamp=now
        )
