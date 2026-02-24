"""Unit tests for engine metrics mapping in Performance Insights collector."""

import pytest
from unittest.mock import Mock
from collectors.performance_insights import (
    PerformanceInsightsCollector,
    ENGINE_METRICS,
    METRIC_FIELD_MAPPING
)


class TestEngineMetricsMapping:
    """Test suite for engine metrics configuration and mapping."""
    
    @pytest.fixture
    def collector(self):
        """Create a PerformanceInsightsCollector instance for testing."""
        pi_client = Mock()
        rds_client = Mock()
        return PerformanceInsightsCollector(pi_client, rds_client)
    
    def test_all_engines_have_mappings(self):
        """Test that all supported engines have metric mappings."""
        expected_engines = [
            'mysql', 'mariadb', 'postgres',
            'aurora-mysql', 'aurora-postgresql',
            'oracle-ee', 'oracle-se2',
            'sqlserver-ee', 'sqlserver-se'
        ]
        
        for engine in expected_engines:
            assert engine in ENGINE_METRICS, f"Engine {engine} missing from ENGINE_METRICS"
            
            # Verify each engine has all required categories
            metrics = ENGINE_METRICS[engine]
            assert 'execution' in metrics, f"Engine {engine} missing 'execution' category"
            assert 'resource' in metrics, f"Engine {engine} missing 'resource' category"
            assert 'rows' in metrics, f"Engine {engine} missing 'rows' category"
            assert 'io' in metrics, f"Engine {engine} missing 'io' category"
            
            # Verify each category has at least one metric
            for category, metric_list in metrics.items():
                assert len(metric_list) > 0, \
                    f"Engine {engine} has empty {category} category"
    
    def test_metric_name_format(self):
        """Test that all PI metric names follow the correct format."""
        for engine, categories in ENGINE_METRICS.items():
            for category, metrics in categories.items():
                for metric in metrics:
                    # All PI metrics should start with 'db.sql.stats.'
                    assert metric.startswith('db.sql.stats.'), \
                        f"Invalid metric format for {engine}/{category}: {metric}"
    
    def test_normalize_engine_name_mysql(self, collector):
        """Test engine name normalization for MySQL variants."""
        test_cases = [
            ('mysql', 'mysql'),
            ('MySQL', 'mysql'),
            ('MYSQL', 'mysql'),
            ('mysql-8.0', 'mysql')
        ]
        
        for input_engine, expected in test_cases:
            result = collector._normalize_engine_name(input_engine)
            assert result == expected, \
                f"Failed to normalize '{input_engine}' to '{expected}', got '{result}'"
    
    def test_normalize_engine_name_postgres(self, collector):
        """Test engine name normalization for PostgreSQL variants."""
        test_cases = [
            ('postgres', 'postgres'),
            ('postgresql', 'postgres'),
            ('PostgreSQL', 'postgres'),
            ('postgres-14', 'postgres')
        ]
        
        for input_engine, expected in test_cases:
            result = collector._normalize_engine_name(input_engine)
            assert result == expected, \
                f"Failed to normalize '{input_engine}' to '{expected}', got '{result}'"
    
    def test_normalize_engine_name_aurora(self, collector):
        """Test engine name normalization for Aurora variants."""
        test_cases = [
            ('aurora', 'aurora-mysql'),  # Default to MySQL
            ('aurora-mysql', 'aurora-mysql'),
            ('Aurora-MySQL', 'aurora-mysql'),
            ('aurora-postgresql', 'aurora-postgresql'),
            ('aurora-postgres', 'aurora-postgresql'),
            ('Aurora-PostgreSQL', 'aurora-postgresql')
        ]
        
        for input_engine, expected in test_cases:
            result = collector._normalize_engine_name(input_engine)
            assert result == expected, \
                f"Failed to normalize '{input_engine}' to '{expected}', got '{result}'"
    
    def test_normalize_engine_name_oracle(self, collector):
        """Test engine name normalization for Oracle variants."""
        test_cases = [
            ('oracle-ee', 'oracle-ee'),
            ('Oracle-EE', 'oracle-ee'),
            ('oracle-se2', 'oracle-se2'),
            ('oracle-se', 'oracle-se2'),
            ('Oracle-SE2', 'oracle-se2')
        ]
        
        for input_engine, expected in test_cases:
            result = collector._normalize_engine_name(input_engine)
            assert result == expected, \
                f"Failed to normalize '{input_engine}' to '{expected}', got '{result}'"
    
    def test_normalize_engine_name_sqlserver(self, collector):
        """Test engine name normalization for SQL Server variants."""
        test_cases = [
            ('sqlserver-ee', 'sqlserver-ee'),
            ('SQLServer-EE', 'sqlserver-ee'),
            ('sqlserver-se', 'sqlserver-se'),
            ('sqlserver', 'sqlserver-se'),  # Default to SE
            ('SQLServer', 'sqlserver-se')
        ]
        
        for input_engine, expected in test_cases:
            result = collector._normalize_engine_name(input_engine)
            assert result == expected, \
                f"Failed to normalize '{input_engine}' to '{expected}', got '{result}'"
    
    def test_normalize_engine_name_unknown(self, collector):
        """Test engine name normalization for unknown engines."""
        unknown_engines = ['unknown-db', 'custom-engine', 'test-db']
        
        for engine in unknown_engines:
            result = collector._normalize_engine_name(engine)
            # Should return lowercase version of input
            assert result == engine.lower(), \
                f"Unknown engine '{engine}' should return lowercase, got '{result}'"
    
    def test_get_engine_metrics_config_mysql(self, collector):
        """Test getting metrics config for MySQL."""
        config = collector._get_engine_metrics_config('mysql')
        
        assert 'execution' in config
        assert 'resource' in config
        assert 'rows' in config
        assert 'io' in config
        
        # MySQL should have lock_time
        assert 'db.sql.stats.lock_time_ms' in config['resource']
        
        # MySQL should have rows_examined
        assert 'db.sql.stats.rows_examined' in config['rows']
    
    def test_get_engine_metrics_config_postgres(self, collector):
        """Test getting metrics config for PostgreSQL."""
        config = collector._get_engine_metrics_config('postgres')
        
        assert 'execution' in config
        assert 'resource' in config
        assert 'rows' in config
        assert 'io' in config
        
        # PostgreSQL should NOT have lock_time
        assert 'db.sql.stats.lock_time_ms' not in config['resource']
        
        # PostgreSQL should NOT have rows_examined
        assert 'db.sql.stats.rows_examined' not in config['rows']
        
        # PostgreSQL uses 'rows' instead
        assert 'db.sql.stats.rows' in config['rows']
    
    def test_get_engine_metrics_config_aurora_mysql(self, collector):
        """Test getting metrics config for Aurora MySQL."""
        config = collector._get_engine_metrics_config('aurora-mysql')
        
        # Aurora MySQL should have same metrics as MySQL
        mysql_config = collector._get_engine_metrics_config('mysql')
        assert config == mysql_config
    
    def test_get_engine_metrics_config_aurora_postgresql(self, collector):
        """Test getting metrics config for Aurora PostgreSQL."""
        config = collector._get_engine_metrics_config('aurora-postgresql')
        
        # Aurora PostgreSQL should have same metrics as PostgreSQL
        postgres_config = collector._get_engine_metrics_config('postgres')
        assert config == postgres_config
    
    def test_get_engine_metrics_config_unknown_engine(self, collector, caplog):
        """Test getting metrics config for unknown engine returns fallback."""
        config = collector._get_engine_metrics_config('unknown-engine')
        
        # Should return MySQL metrics as fallback
        mysql_config = ENGINE_METRICS['mysql']
        assert config == mysql_config
        
        # Should log warning
        assert 'Unknown engine type' in caplog.text
        assert 'unknown-engine' in caplog.text
    
    def test_map_metric_name_execution_metrics(self, collector):
        """Test mapping execution-related PI metrics to field names."""
        test_cases = [
            ('db.sql.stats.executions_per_sec', 'executions_per_second'),
            ('db.sql.stats.calls_per_sec', 'executions_per_second'),
            ('db.sql.stats.total_time_ms', 'total_execution_time'),
            ('db.sql.stats.elapsed_time_per_sec_ms', 'total_execution_time'),
            ('db.sql.stats.total_elapsed_time_ms', 'total_execution_time')
        ]
        
        for pi_metric, expected_field in test_cases:
            result = collector._map_metric_name(pi_metric, 'mysql')
            assert result == expected_field, \
                f"Failed to map '{pi_metric}' to '{expected_field}', got '{result}'"
    
    def test_map_metric_name_resource_metrics(self, collector):
        """Test mapping resource-related PI metrics to field names."""
        test_cases = [
            ('db.sql.stats.cpu_time_ms', 'cpu_time'),
            ('db.sql.stats.cpu_time_per_sec_ms', 'cpu_time'),
            ('db.sql.stats.total_worker_time_ms', 'cpu_time'),
            ('db.sql.stats.lock_time_ms', 'lock_time')
        ]
        
        for pi_metric, expected_field in test_cases:
            result = collector._map_metric_name(pi_metric, 'mysql')
            assert result == expected_field, \
                f"Failed to map '{pi_metric}' to '{expected_field}', got '{result}'"
    
    def test_map_metric_name_row_metrics(self, collector):
        """Test mapping row-related PI metrics to field names."""
        test_cases = [
            ('db.sql.stats.rows_examined', 'rows_examined'),
            ('db.sql.stats.rows_sent', 'rows_returned'),
            ('db.sql.stats.rows', 'rows_returned'),
            ('db.sql.stats.rows_processed_per_sec', 'rows_returned'),
            ('db.sql.stats.total_rows', 'rows_returned')
        ]
        
        for pi_metric, expected_field in test_cases:
            result = collector._map_metric_name(pi_metric, 'mysql')
            assert result == expected_field, \
                f"Failed to map '{pi_metric}' to '{expected_field}', got '{result}'"
    
    def test_map_metric_name_io_metrics(self, collector):
        """Test mapping I/O-related PI metrics to field names."""
        test_cases = [
            ('db.sql.stats.innodb_io_r_bytes', 'read_io_bytes'),
            ('db.sql.stats.shared_blks_read', 'read_io_bytes'),
            ('db.sql.stats.physical_read_bytes_per_sec', 'read_io_bytes'),
            ('db.sql.stats.total_physical_reads', 'read_io_bytes'),
            ('db.sql.stats.innodb_io_w_bytes', 'write_io_bytes'),
            ('db.sql.stats.shared_blks_written', 'write_io_bytes'),
            ('db.sql.stats.physical_write_bytes_per_sec', 'write_io_bytes'),
            ('db.sql.stats.total_logical_writes', 'write_io_bytes')
        ]
        
        for pi_metric, expected_field in test_cases:
            result = collector._map_metric_name(pi_metric, 'mysql')
            assert result == expected_field, \
                f"Failed to map '{pi_metric}' to '{expected_field}', got '{result}'"
    
    def test_map_metric_name_unknown_metric(self, collector, caplog):
        """Test mapping unknown PI metric returns None."""
        import logging
        caplog.set_level(logging.DEBUG)
        
        result = collector._map_metric_name('db.sql.stats.unknown_metric', 'mysql')
        
        assert result is None
        
        # Should log debug message
        assert 'No mapping found' in caplog.text
        assert 'db.sql.stats.unknown_metric' in caplog.text
    
    def test_all_engine_metrics_have_mappings(self, collector):
        """
        Test that all metrics defined in ENGINE_METRICS have corresponding
        field mappings in METRIC_FIELD_MAPPING.
        """
        unmapped_metrics = []
        
        for engine, categories in ENGINE_METRICS.items():
            for category, metrics in categories.items():
                for metric in metrics:
                    if metric not in METRIC_FIELD_MAPPING:
                        unmapped_metrics.append(f"{engine}/{category}/{metric}")
        
        assert len(unmapped_metrics) == 0, \
            f"Found unmapped metrics: {', '.join(unmapped_metrics)}"
    
    def test_metric_field_mapping_completeness(self):
        """Test that METRIC_FIELD_MAPPING covers all expected field names."""
        expected_fields = {
            'executions_per_second',
            'total_execution_time',
            'cpu_time',
            'lock_time',
            'rows_examined',
            'rows_returned',
            'read_io_bytes',
            'write_io_bytes'
        }
        
        mapped_fields = set(METRIC_FIELD_MAPPING.values())
        
        # All expected fields should be in the mapping
        for field in expected_fields:
            assert field in mapped_fields, \
                f"Expected field '{field}' not found in METRIC_FIELD_MAPPING"
    
    def test_engine_specific_metric_availability(self, collector):
        """
        Property 2: Engine-Specific Metric Collection
        
        For any RDS engine type, collector SHALL request only metrics
        supported by that engine according to ENGINE_METRICS mapping.
        """
        # MySQL has lock_time
        mysql_config = collector._get_engine_metrics_config('mysql')
        mysql_metrics = [m for metrics in mysql_config.values() for m in metrics]
        assert 'db.sql.stats.lock_time_ms' in mysql_metrics
        
        # PostgreSQL does NOT have lock_time
        postgres_config = collector._get_engine_metrics_config('postgres')
        postgres_metrics = [m for metrics in postgres_config.values() for m in metrics]
        assert 'db.sql.stats.lock_time_ms' not in postgres_metrics
        
        # MySQL has rows_examined
        assert 'db.sql.stats.rows_examined' in mysql_metrics
        
        # PostgreSQL does NOT have rows_examined
        assert 'db.sql.stats.rows_examined' not in postgres_metrics
