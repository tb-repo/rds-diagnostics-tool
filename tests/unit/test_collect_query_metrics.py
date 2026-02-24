"""Unit tests for _collect_query_metrics method."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from collectors.performance_insights import PerformanceInsightsCollector
from core.models import TimeRange
from aws.clients import AWSClientError


class TestCollectQueryMetrics:
    """Test suite for _collect_query_metrics method."""
    
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
    
    def test_collect_query_metrics_success_mysql(self, collector, time_range):
        """Test successful metric collection for MySQL."""
        # Mock response from get_resource_metrics
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': [
                {
                    'Key': {'Metric': 'db.sql.stats.executions_per_sec'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 0.5},
                        {'Timestamp': datetime.utcnow(), 'Value': 0.6}
                    ]
                },
                {
                    'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 100.0},
                        {'Timestamp': datetime.utcnow(), 'Value': 120.0}
                    ]
                },
                {
                    'Key': {'Metric': 'db.sql.stats.lock_time_ms'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 10.0},
                        {'Timestamp': datetime.utcnow(), 'Value': 15.0}
                    ]
                }
            ]
        })
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        # Verify metrics were collected and averaged
        assert 'executions_per_second' in metrics
        assert metrics['executions_per_second'] == 0.55  # (0.5 + 0.6) / 2
        
        assert 'cpu_time' in metrics
        assert metrics['cpu_time'] == 110.0  # (100 + 120) / 2
        
        assert 'lock_time' in metrics
        assert metrics['lock_time'] == 12.5  # (10 + 15) / 2
    
    def test_collect_query_metrics_success_postgres(self, collector, time_range):
        """Test successful metric collection for PostgreSQL."""
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': [
                {
                    'Key': {'Metric': 'db.sql.stats.calls_per_sec'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 0.8}
                    ]
                },
                {
                    'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 150.0}
                    ]
                },
                {
                    'Key': {'Metric': 'db.sql.stats.rows'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 50}
                    ]
                }
            ]
        })
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-xyz789',
            engine='postgres',
            time_range=time_range
        )
        
        # PostgreSQL uses different metric names
        assert 'executions_per_second' in metrics
        assert metrics['executions_per_second'] == 0.8
        
        assert 'cpu_time' in metrics
        assert metrics['cpu_time'] == 150.0
        
        assert 'rows_returned' in metrics
        assert metrics['rows_returned'] == 50.0
        
        # PostgreSQL doesn't have lock_time
        assert 'lock_time' not in metrics
    
    def test_collect_query_metrics_empty_response(self, collector, time_range):
        """Test handling of empty response."""
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': []
        })
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        assert metrics == {}
    
    def test_collect_query_metrics_no_data_points(self, collector, time_range):
        """Test handling of metrics with no data points."""
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': [
                {
                    'Key': {'Metric': 'db.sql.stats.executions_per_sec'},
                    'DataPoints': []
                },
                {
                    'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                    'DataPoints': []
                }
            ]
        })
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        assert metrics == {}
    
    def test_collect_query_metrics_partial_data(self, collector, time_range):
        """Test handling of partial metric data."""
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': [
                {
                    'Key': {'Metric': 'db.sql.stats.executions_per_sec'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 0.5}
                    ]
                },
                {
                    'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                    'DataPoints': []  # No data for this metric
                },
                {
                    'Key': {'Metric': 'db.sql.stats.lock_time_ms'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 10.0}
                    ]
                }
            ]
        })
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        # Should have metrics with data
        assert 'executions_per_second' in metrics
        assert 'lock_time' in metrics
        
        # Should not have metric without data
        assert 'cpu_time' not in metrics
    
    def test_collect_query_metrics_invalid_values_filtered(self, collector, time_range):
        """Test that invalid metric values are filtered out."""
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': [
                {
                    'Key': {'Metric': 'db.sql.stats.executions_per_sec'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': -1.0}  # Invalid: negative
                    ]
                },
                {
                    'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': float('inf')}  # Invalid: infinity
                    ]
                },
                {
                    'Key': {'Metric': 'db.sql.stats.lock_time_ms'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 10.0}  # Valid
                    ]
                }
            ]
        })
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        # Invalid metrics should be None
        assert metrics.get('executions_per_second') is None
        assert metrics.get('cpu_time') is None
        
        # Valid metric should be present
        assert metrics['lock_time'] == 10.0
    
    def test_collect_query_metrics_api_error(self, collector, time_range, caplog):
        """Test handling of API errors."""
        collector.pi_client.get_resource_metrics = Mock(
            side_effect=AWSClientError("API rate limit exceeded")
        )
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        # Should return empty dict on error
        assert metrics == {}
        
        # Should log warning
        assert 'Failed to collect enhanced metrics' in caplog.text
        assert 'sql-abc123' in caplog.text
    
    def test_collect_query_metrics_unexpected_error(self, collector, time_range, caplog):
        """Test handling of unexpected errors."""
        collector.pi_client.get_resource_metrics = Mock(
            side_effect=Exception("Unexpected error")
        )
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        # Should return empty dict on error
        assert metrics == {}
        
        # Should log warning
        assert 'Unexpected error collecting metrics' in caplog.text
    
    def test_collect_query_metrics_builds_correct_query_structure(self, collector, time_range):
        """Test that metric queries are built correctly."""
        collector.pi_client.get_resource_metrics = Mock(return_value={'MetricList': []})
        
        collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        # Verify the call was made with correct structure
        call_args = collector.pi_client.get_resource_metrics.call_args
        
        assert call_args[1]['resource_id'] == 'db-TEST123'
        assert call_args[1]['start_time'] == time_range.start
        assert call_args[1]['end_time'] == time_range.end
        
        metric_queries = call_args[1]['metric_queries']
        assert len(metric_queries) > 0
        
        # Verify query structure
        for query in metric_queries:
            assert 'Metric' in query
            assert 'GroupBy' in query
            assert query['GroupBy']['Group'] == 'db.sql'
            assert 'Filter' in query
            assert query['Filter']['db.sql.id'] == 'sql-abc123'
    
    def test_collect_query_metrics_property_4_api_data_preservation(self, collector, time_range):
        """
        Property 4: API Data Preservation
        
        For any metric value returned by PI API, stored value SHALL be
        exactly equal to API-provided value without modification.
        """
        # Mock API response with specific values
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': [
                {
                    'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 123.456789}
                    ]
                }
            ]
        })
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        # Value should be preserved exactly (no rounding, no modification)
        assert metrics['cpu_time'] == 123.456789
    
    def test_collect_query_metrics_averages_time_series(self, collector, time_range):
        """Test that time-series data is averaged correctly."""
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': [
                {
                    'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 100.0},
                        {'Timestamp': datetime.utcnow(), 'Value': 200.0},
                        {'Timestamp': datetime.utcnow(), 'Value': 300.0}
                    ]
                }
            ]
        })
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        # Should average the three values
        assert metrics['cpu_time'] == 200.0  # (100 + 200 + 300) / 3
    
    def test_collect_query_metrics_handles_missing_metric_key(self, collector, time_range):
        """Test handling of malformed response with missing metric key."""
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': [
                {
                    'Key': {},  # Missing 'Metric' key
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 100.0}
                    ]
                },
                {
                    'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 150.0}
                    ]
                }
            ]
        })
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        # Should skip malformed entry and process valid one
        assert 'cpu_time' in metrics
        assert metrics['cpu_time'] == 150.0
    
    def test_collect_query_metrics_handles_data_points_without_value(self, collector, time_range):
        """Test handling of data points missing Value field."""
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': [
                {
                    'Key': {'Metric': 'db.sql.stats.cpu_time_ms'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow()},  # Missing 'Value'
                        {'Timestamp': datetime.utcnow(), 'Value': 100.0},
                        {'Timestamp': datetime.utcnow(), 'Value': 200.0}
                    ]
                }
            ]
        })
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='mysql',
            time_range=time_range
        )
        
        # Should average only the valid values
        assert metrics['cpu_time'] == 150.0  # (100 + 200) / 2
    
    def test_collect_query_metrics_unknown_engine_uses_fallback(self, collector, time_range):
        """Test that unknown engines use fallback metrics."""
        collector.pi_client.get_resource_metrics = Mock(return_value={
            'MetricList': [
                {
                    'Key': {'Metric': 'db.sql.stats.executions_per_sec'},
                    'DataPoints': [
                        {'Timestamp': datetime.utcnow(), 'Value': 0.5}
                    ]
                }
            ]
        })
        
        metrics = collector._collect_query_metrics(
            resource_id='db-TEST123',
            sql_id='sql-abc123',
            engine='unknown-engine',  # Unknown engine
            time_range=time_range
        )
        
        # Should still collect metrics using fallback (MySQL) configuration
        assert 'executions_per_second' in metrics
