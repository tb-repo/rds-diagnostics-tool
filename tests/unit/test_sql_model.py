"""Unit tests for extended SQLQuery model."""

import pytest
from core.models import SQLQuery


class TestSQLQueryModel:
    """Test suite for SQLQuery dataclass with enhanced fields."""
    
    def test_create_with_required_fields_only(self):
        """Test creating SQLQuery with only required fields (backward compatibility)."""
        query = SQLQuery(
            query_id="sql-123",
            query_text="SELECT * FROM users",
            total_execution_time=100.0,
            average_execution_time=10.0,
            execution_count=10
        )
        
        assert query.query_id == "sql-123"
        assert query.query_text == "SELECT * FROM users"
        assert query.total_execution_time == 100.0
        assert query.average_execution_time == 10.0
        assert query.execution_count == 10
        
        # Verify optional fields default to None or empty list
        assert query.rows_affected is None
        assert query.wait_events == []
        assert query.engine_type is None
        assert query.executions_per_second is None
        assert query.cpu_time is None
        assert query.lock_time is None
        assert query.rows_examined is None
        assert query.rows_returned is None
        assert query.read_io_bytes is None
        assert query.write_io_bytes is None
    
    def test_create_with_all_fields(self):
        """Test creating SQLQuery with all fields including enhanced metrics."""
        query = SQLQuery(
            query_id="sql-456",
            query_text="SELECT id, name FROM products WHERE category = 'electronics'",
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
        
        # Verify all fields are set correctly
        assert query.query_id == "sql-456"
        assert query.query_text == "SELECT id, name FROM products WHERE category = 'electronics'"
        assert query.total_execution_time == 250.5
        assert query.average_execution_time == 25.05
        assert query.execution_count == 10
        assert query.rows_affected == 100
        assert query.wait_events == ["lock/table", "io/file"]
        assert query.engine_type == "mysql"
        assert query.executions_per_second == 0.5
        assert query.cpu_time == 200.0
        assert query.lock_time == 30.0
        assert query.rows_examined == 1000
        assert query.rows_returned == 100
        assert query.read_io_bytes == 1024000
        assert query.write_io_bytes == 512000
    
    def test_create_with_partial_enhanced_fields(self):
        """Test creating SQLQuery with some enhanced fields (engine-specific availability)."""
        # Simulate PostgreSQL which doesn't have lock_time or rows_examined
        query = SQLQuery(
            query_id="sql-789",
            query_text="SELECT * FROM orders",
            total_execution_time=150.0,
            average_execution_time=15.0,
            execution_count=10,
            engine_type="postgres",
            executions_per_second=0.8,
            cpu_time=120.0,
            # lock_time not available for postgres
            # rows_examined not available for postgres
            rows_returned=50,
            read_io_bytes=2048000,
            write_io_bytes=1024000
        )
        
        assert query.engine_type == "postgres"
        assert query.cpu_time == 120.0
        assert query.lock_time is None  # Not available for postgres
        assert query.rows_examined is None  # Not available for postgres
        assert query.rows_returned == 50
    
    def test_long_sql_text(self):
        """Test SQLQuery can store long SQL text (up to 10,000 characters)."""
        long_sql = "SELECT " + ", ".join([f"col{i}" for i in range(1000)]) + " FROM large_table"
        
        query = SQLQuery(
            query_id="sql-long",
            query_text=long_sql,
            total_execution_time=500.0,
            average_execution_time=50.0,
            execution_count=10
        )
        
        assert query.query_text == long_sql
        assert len(query.query_text) > 5000  # Verify it's actually long
    
    def test_sql_text_round_trip_preservation(self):
        """
        Property 1: SQL Text Round-Trip Preservation
        
        For any SQL query text, storing and retrieving SHALL preserve exact original text.
        """
        original_texts = [
            "SELECT * FROM users",
            "SELECT\n  id,\n  name\nFROM\n  products\nWHERE\n  status = 'active'",
            "SELECT * FROM orders WHERE created_at > '2024-01-01' AND status IN ('pending', 'processing')",
            "-- Comment\nSELECT /* inline comment */ id FROM table",
            "SELECT 'special chars: !@#$%^&*()' AS test"
        ]
        
        for original_text in original_texts:
            query = SQLQuery(
                query_id="test-id",
                query_text=original_text,
                total_execution_time=100.0,
                average_execution_time=10.0,
                execution_count=10
            )
            
            retrieved_text = query.query_text
            assert retrieved_text == original_text, \
                f"Round-trip failed: expected '{original_text}', got '{retrieved_text}'"
    
    def test_enhanced_fields_are_optional(self):
        """Test that all enhanced fields can be None without errors."""
        query = SQLQuery(
            query_id="sql-optional",
            query_text="SELECT 1",
            total_execution_time=10.0,
            average_execution_time=1.0,
            execution_count=10,
            engine_type=None,
            executions_per_second=None,
            cpu_time=None,
            lock_time=None,
            rows_examined=None,
            rows_returned=None,
            read_io_bytes=None,
            write_io_bytes=None
        )
        
        # Should not raise any errors
        assert query.query_id == "sql-optional"
        assert query.engine_type is None
        assert query.cpu_time is None
    
    def test_backward_compatibility_with_existing_code(self):
        """Test that existing code patterns still work with extended model."""
        # Simulate existing code that only uses basic fields
        queries = [
            SQLQuery(
                query_id=f"sql-{i}",
                query_text=f"SELECT * FROM table{i}",
                total_execution_time=float(i * 100),
                average_execution_time=float(i * 10),
                execution_count=10
            )
            for i in range(5)
        ]
        
        # Existing code operations should still work
        total_time = sum(q.total_execution_time for q in queries)
        assert total_time == 1000.0  # 0 + 100 + 200 + 300 + 400
        
        # Filtering by execution time
        slow_queries = [q for q in queries if q.total_execution_time > 200]
        assert len(slow_queries) == 2  # queries 3 and 4
        
        # Accessing optional fields should not raise errors
        for query in queries:
            assert query.engine_type is None
            assert query.cpu_time is None
