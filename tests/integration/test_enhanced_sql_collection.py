"""Integration tests for enhanced SQL query collection."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from collectors.performance_insights import PerformanceInsightsCollector
from core.models import TimeRange, SQLQuery
from aws.clients import AWSClientError


class TestEnhancedSQLCollection:
    """Integration tests for collect_top_sql_queries with enhanced metrics."""
    
    @pytest.fixture
    def collector(self):
        """Create a PerformanceInsightsCollector instance for testing."""
        pi_client = Mock()
        rds_client = Mock()
        return PerformanceInsightsCollector(pi_client, rds_client)
    
    @pytest.fixture
    def time_range(self):
        """Create a sample time range."""
        end = datetime.utcnow()
        start = end - timedelta(hours=1)
        return TimeRange(start=start, end=end)
    
    def test_collect_top_sql_queries_with_enhanced_metrics_mysql(self, collector, time_range):
        """Test end-to-end collection with enhanced metrics for MySQL."""
        # Mock Performance Insights enabled
        collector.rds_client.describe_instance = Mock(return_value={
            'PerformanceInsightsEnabled': True,
            'Engine': 'mysql'
        })
        collector.rds_client.get_instance_resource_id = Mock(return_value='db-TEST123')
        
        # Mock describe_dimension_keys response (Phase 1: identify queries)
        collector.pi_client.describe_dimension_keys = Mock(return_value=[
            {
                'Dimensions': {
                    'db.sql.id': 'sql-abc123',
                    'db.sql.statement': 'SELECT * FROM users WHERE id = ?'
                },
                'Total': 1000.0,
                'Partitions': [
                    {'Value': 100.0},
                    {'Value': 200.0},
                    {'Value': 300.0}
                ]
            },
            {
                'Dimensions': {
                    'db.sql.id': 'sql-xyz789',
                    'db.sql.statement': 'UPDATE orders SET status = ? WHERE id = ?'
                },
                'Total': 500.0,
                'Partitions': [
                    {'Value': 250.0},
                    {'Value': 250.0}
                ]
            }
        ])
        
        # Mock get_resource_metrics response (Phase 2: enhanced metrics)
        def mock_get_resource_metrics(resource_id, metric_queries, start_time, end_time):
            # Extract SQL ID from filter
            sql_id = metric_queries[0]['Filter']['db.sql.id']
            
            if sql_id == 'sql-abc123':
                return {
                    'MetricList': [
                        {
                            'Key': {'Metric': 'db.sql.stats.executions_per_sec'},
                            'DataPoints': [{'Value': 0.5}]
                        },
                        {
                            'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                            'DataPoints': [{'Value': 800.0}]
                        },
                        {
                            'Key': {'Metric': 'db.sql.stats.lock_time_ms'},
                            'DataPoints': [{'Value': 50.0}]
                        },
                        {
                            'Key': {'Metric': 'db.sql.stats.rows_examined'},
                            'DataPoints': [{'Value': 10000}]
                        },
                        {
                            'Key': {'Metric': 'db.sql.stats.rows_sent'},
                            'DataPoints': [{'Value': 100}]
                        }
                    ]
                }
            elif sql_id == 'sql-xyz789':
                return {
                    'MetricList': [
                        {
                            'Key': {'Metric': 'db.sql.stats.executions_per_sec'},
                            'DataPoints': [{'Value': 0.3}]
                        },
                        {
                            'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                            'DataPoints': [{'Value': 400.0}]
                        }
                    ]
                }
            return {'MetricList': []}
        
        collector.pi_client.get_resource_metrics = Mock(side_effect=mock_get_resource_metrics)
        
        # Execute collection
        queries = collector.collect_top_sql_queries(
            instance_id='test-instance',
            time_range=time_range,
            limit=10
        )
        
        # Verify results
        assert len(queries) == 2
        
        # Verify first query has enhanced metrics
        query1 = queries[0]
        assert query1.query_id == 'sql-abc123'
        assert query1.query_text == 'SELECT * FROM users WHERE id = ?'
        assert query1.engine_type == 'mysql'
        assert query1.executions_per_second == 0.5
        assert query1.cpu_time == 800.0
        assert query1.lock_time == 50.0
        assert query1.rows_examined == 10000
        assert query1.rows_returned == 100
        
        # Verify second query has partial enhanced metrics
        query2 = queries[1]
        assert query2.query_id == 'sql-xyz789'
        assert query2.engine_type == 'mysql'
        assert query2.executions_per_second == 0.3
        assert query2.cpu_time == 400.0
        assert query2.lock_time is None  # Not available in response
        assert query2.rows_examined is None
    
    def test_collect_top_sql_queries_with_enhanced_metrics_postgres(self, collector, time_range):
        """Test end-to-end collection with enhanced metrics for PostgreSQL."""
        # Mock Performance Insights enabled
        collector.rds_client.describe_instance = Mock(return_value={
            'PerformanceInsightsEnabled': True,
            'Engine': 'postgres'
        })
        collector.rds_client.get_instance_resource_id = Mock(return_value='db-TEST456')
        
        # Mock describe_dimension_keys response
        collector.pi_client.describe_dimension_keys = Mock(return_value=[
            {
                'Dimensions': {
                    'db.sql.id': 'sql-pg123',
                    'db.sql.statement': 'SELECT * FROM products WHERE category = $1'
                },
                'Total': 750.0,
                'Partitions': [{'Value': 750.0}]
            }
        ])
        
        # Mock get_resource_metrics response with PostgreSQL metrics
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': [
                {
                    'Key': {'Metric': 'db.sql.stats.calls_per_sec'},
                    'DataPoints': [{'Value': 0.8}]
                },
                {
                    'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                    'DataPoints': [{'Value': 600.0}]
                },
                {
                    'Key': {'Metric': 'db.sql.stats.rows'},
                    'DataPoints': [{'Value': 50}]
                },
                {
                    'Key': {'Metric': 'db.sql.stats.shared_blks_read'},
                    'DataPoints': [{'Value': 1024}]
                }
            ]
        })
        
        # Execute collection
        queries = collector.collect_top_sql_queries(
            instance_id='test-postgres-instance',
            time_range=time_range,
            limit=10
        )
        
        # Verify results
        assert len(queries) == 1
        
        query = queries[0]
        assert query.query_id == 'sql-pg123'
        assert query.engine_type == 'postgres'
        assert query.executions_per_second == 0.8  # PostgreSQL uses calls_per_sec
        assert query.cpu_time == 600.0
        assert query.rows_returned == 50.0  # PostgreSQL uses 'rows' metric
        assert query.read_io_bytes == 1024.0
        assert query.lock_time is None  # PostgreSQL doesn't have lock_time
    
    def test_collect_top_sql_queries_fallback_on_enhanced_error(self, collector, time_range, caplog):
        """Test fallback to basic collection when enhanced collection fails."""
        # Mock Performance Insights enabled
        collector.rds_client.describe_instance = Mock(return_value={
            'PerformanceInsightsEnabled': True,
            'Engine': 'mysql'
        })
        collector.rds_client.get_instance_resource_id = Mock(return_value='db-TEST123')
        
        # Mock describe_dimension_keys response
        collector.pi_client.describe_dimension_keys = Mock(return_value=[
            {
                'Dimensions': {
                    'db.sql.id': 'sql-abc123',
                    'db.sql.statement': 'SELECT * FROM users'
                },
                'Total': 1000.0,
                'Partitions': [{'Value': 1000.0}]
            }
        ])
        
        # Mock get_resource_metrics to fail
        collector.pi_client.get_resource_metrics = Mock(
            side_effect=AWSClientError("Rate limit exceeded")
        )
        
        # Execute collection
        queries = collector.collect_top_sql_queries(
            instance_id='test-instance',
            time_range=time_range,
            limit=10
        )
        
        # Verify fallback behavior
        assert len(queries) == 1
        
        query = queries[0]
        assert query.query_id == 'sql-abc123'
        assert query.query_text == 'SELECT * FROM users'
        assert query.engine_type == 'mysql'
        
        # Enhanced metrics should be None (fallback to basic)
        assert query.executions_per_second is None
        assert query.cpu_time is None
        assert query.lock_time is None
        
        # Basic metrics should still be present
        assert query.total_execution_time == 1000.0
        
        # Should log warning about enhanced collection failure
        assert 'Enhanced metric collection failed' in caplog.text or 'Failed to collect enhanced metrics' in caplog.text
    
    def test_collect_top_sql_queries_deduplication(self, collector, time_range):
        """Test that duplicate SQL IDs are deduplicated."""
        # Mock Performance Insights enabled
        collector.rds_client.describe_instance = Mock(return_value={
            'PerformanceInsightsEnabled': True,
            'Engine': 'mysql'
        })
        collector.rds_client.get_instance_resource_id = Mock(return_value='db-TEST123')
        
        # Mock describe_dimension_keys with duplicate SQL IDs
        collector.pi_client.describe_dimension_keys = Mock(return_value=[
            {
                'Dimensions': {
                    'db.sql.id': 'sql-abc123',
                    'db.sql.statement': 'SELECT * FROM users'
                },
                'Total': 1000.0,
                'Partitions': [{'Value': 1000.0}]
            },
            {
                'Dimensions': {
                    'db.sql.id': 'sql-abc123',  # Duplicate
                    'db.sql.statement': 'SELECT * FROM users'
                },
                'Total': 500.0,
                'Partitions': [{'Value': 500.0}]
            },
            {
                'Dimensions': {
                    'db.sql.id': 'sql-xyz789',
                    'db.sql.statement': 'SELECT * FROM orders'
                },
                'Total': 750.0,
                'Partitions': [{'Value': 750.0}]
            }
        ])
        
        # Mock get_resource_metrics
        collector.pi_client.get_resource_metrics = Mock(return_value={'MetricList': []})
        
        # Execute collection
        queries = collector.collect_top_sql_queries(
            instance_id='test-instance',
            time_range=time_range,
            limit=10
        )
        
        # Should only have 2 unique queries
        assert len(queries) == 2
        
        query_ids = [q.query_id for q in queries]
        assert 'sql-abc123' in query_ids
        assert 'sql-xyz789' in query_ids
        assert query_ids.count('sql-abc123') == 1  # No duplicates
    
    def test_collect_top_sql_queries_respects_limit(self, collector, time_range):
        """Test that collection respects the limit parameter."""
        # Mock Performance Insights enabled
        collector.rds_client.describe_instance = Mock(return_value={
            'PerformanceInsightsEnabled': True,
            'Engine': 'mysql'
        })
        collector.rds_client.get_instance_resource_id = Mock(return_value='db-TEST123')
        
        # Mock describe_dimension_keys with many queries
        dimension_keys = []
        for i in range(20):
            dimension_keys.append({
                'Dimensions': {
                    'db.sql.id': f'sql-{i:03d}',
                    'db.sql.statement': f'SELECT * FROM table{i}'
                },
                'Total': 1000.0 - (i * 10),
                'Partitions': [{'Value': 1000.0 - (i * 10)}]
            })
        
        collector.pi_client.describe_dimension_keys = Mock(return_value=dimension_keys)
        collector.pi_client.get_resource_metrics = Mock(return_value={'MetricList': []})
        
        # Execute collection with limit=5
        queries = collector.collect_top_sql_queries(
            instance_id='test-instance',
            time_range=time_range,
            limit=5
        )
        
        # Should only return 5 queries
        assert len(queries) == 5
    
    def test_collect_top_sql_queries_pi_not_enabled(self, collector, time_range, caplog):
        """Test handling when Performance Insights is not enabled."""
        # Mock Performance Insights disabled
        collector.rds_client.describe_instance = Mock(return_value={
            'PerformanceInsightsEnabled': False,
            'Engine': 'mysql'
        })
        
        # Execute collection
        queries = collector.collect_top_sql_queries(
            instance_id='test-instance',
            time_range=time_range,
            limit=10
        )
        
        # Should return empty list
        assert queries == []
        
        # Should log warning
        assert 'Performance Insights not enabled' in caplog.text
    
    def test_collect_top_sql_queries_api_error_in_phase1(self, collector, time_range, caplog):
        """Test handling of API error in Phase 1 (describe_dimension_keys)."""
        # Mock Performance Insights enabled
        collector.rds_client.describe_instance = Mock(return_value={
            'PerformanceInsightsEnabled': True,
            'Engine': 'mysql'
        })
        collector.rds_client.get_instance_resource_id = Mock(return_value='db-TEST123')
        
        # Mock describe_dimension_keys to fail
        collector.pi_client.describe_dimension_keys = Mock(
            side_effect=AWSClientError("Access denied")
        )
        
        # Execute collection
        queries = collector.collect_top_sql_queries(
            instance_id='test-instance',
            time_range=time_range,
            limit=10
        )
        
        # Should return empty list
        assert queries == []
        
        # Should log error
        assert 'Failed to collect top SQL queries' in caplog.text
    
    def test_collect_top_sql_queries_property_2_engine_specific_metrics(self, collector, time_range):
        """
        Property 2: Engine-Specific Metric Collection
        
        For any RDS engine type, collector SHALL request only metrics
        supported by that engine according to engine metrics mapping.
        """
        # Test with MySQL
        collector.rds_client.describe_instance = Mock(return_value={
            'PerformanceInsightsEnabled': True,
            'Engine': 'mysql'
        })
        collector.rds_client.get_instance_resource_id = Mock(return_value='db-TEST123')
        
        collector.pi_client.describe_dimension_keys = Mock(return_value=[
            {
                'Dimensions': {
                    'db.sql.id': 'sql-abc123',
                    'db.sql.statement': 'SELECT 1'
                },
                'Total': 100.0,
                'Partitions': [{'Value': 100.0}]
            }
        ])
        
        collector.pi_client.get_resource_metrics = Mock(return_value={'MetricList': []})
        
        # Execute collection
        collector.collect_top_sql_queries(
            instance_id='test-instance',
            time_range=time_range,
            limit=10
        )
        
        # Verify get_resource_metrics was called
        assert collector.pi_client.get_resource_metrics.called
        
        # Get the metric_queries parameter
        call_args = collector.pi_client.get_resource_metrics.call_args
        metric_queries = call_args[1]['metric_queries']
        
        # Extract requested metric names
        requested_metrics = [q['Metric'] for q in metric_queries]
        
        # Verify MySQL-specific metrics are requested
        assert 'db.sql.stats.executions_per_sec' in requested_metrics
        assert 'db.sql.stats.cpu_time_ms' in requested_metrics
        assert 'db.sql.stats.lock_time_ms' in requested_metrics  # MySQL has lock_time
        assert 'db.sql.stats.rows_examined' in requested_metrics  # MySQL has rows_examined
        
        # Verify PostgreSQL-specific metrics are NOT requested
        assert 'db.sql.stats.calls_per_sec' not in requested_metrics  # PostgreSQL metric
        assert 'db.sql.stats.shared_blks_read' not in requested_metrics  # PostgreSQL metric
    
    def test_collect_top_sql_queries_maintains_backward_compatibility(self, collector, time_range):
        """Test that method maintains backward compatibility with existing signature."""
        # Mock Performance Insights enabled
        collector.rds_client.describe_instance = Mock(return_value={
            'PerformanceInsightsEnabled': True,
            'Engine': 'mysql'
        })
        collector.rds_client.get_instance_resource_id = Mock(return_value='db-TEST123')
        
        collector.pi_client.describe_dimension_keys = Mock(return_value=[
            {
                'Dimensions': {
                    'db.sql.id': 'sql-abc123',
                    'db.sql.statement': 'SELECT 1'
                },
                'Total': 100.0,
                'Partitions': [{'Value': 100.0}]
            }
        ])
        
        collector.pi_client.get_resource_metrics = Mock(return_value={'MetricList': []})
        
        # Call with original signature (no new parameters)
        queries = collector.collect_top_sql_queries(
            instance_id='test-instance',
            time_range=time_range,
            limit=10
        )
        
        # Should return List[SQLQuery] as before
        assert isinstance(queries, list)
        assert len(queries) == 1
        assert isinstance(queries[0], SQLQuery)
        
        # Should have all original fields
        assert hasattr(queries[0], 'query_id')
        assert hasattr(queries[0], 'query_text')
        assert hasattr(queries[0], 'total_execution_time')
        assert hasattr(queries[0], 'average_execution_time')
        assert hasattr(queries[0], 'execution_count')
        
        # Should also have new optional fields
        assert hasattr(queries[0], 'engine_type')
        assert hasattr(queries[0], 'executions_per_second')
        assert hasattr(queries[0], 'cpu_time')
