"""Unit tests for metric value validation."""

import pytest
import math
from unittest.mock import Mock
from collectors.performance_insights import PerformanceInsightsCollector


class TestMetricValidation:
    """Test suite for metric value validation."""
    
    @pytest.fixture
    def collector(self):
        """Create a PerformanceInsightsCollector instance for testing."""
        pi_client = Mock()
        rds_client = Mock()
        return PerformanceInsightsCollector(pi_client, rds_client)
    
    def test_validate_valid_positive_value(self, collector):
        """Test validation of valid positive values."""
        test_cases = [
            (0.0, 0.0),
            (1.0, 1.0),
            (100.5, 100.5),
            (1000000.0, 1000000.0),
            (0.001, 0.001)
        ]
        
        for input_value, expected in test_cases:
            result = collector._validate_metric_value('test_metric', input_value)
            assert result == expected, \
                f"Failed to validate {input_value}, expected {expected}, got {result}"
    
    def test_validate_zero_value(self, collector):
        """Test validation of zero value (should be valid)."""
        result = collector._validate_metric_value('test_metric', 0)
        assert result == 0.0
        
        result = collector._validate_metric_value('test_metric', 0.0)
        assert result == 0.0
    
    def test_validate_none_value(self, collector):
        """Test validation of None value (should return None)."""
        result = collector._validate_metric_value('test_metric', None)
        assert result is None
    
    def test_validate_negative_value(self, collector, caplog):
        """Test validation of negative values (should return None)."""
        test_cases = [-1.0, -100.5, -0.001]
        
        for value in test_cases:
            result = collector._validate_metric_value('test_metric', value)
            assert result is None, \
                f"Negative value {value} should return None, got {result}"
            
            # Should log warning
            assert 'Invalid metric value' in caplog.text
            assert 'negative' in caplog.text.lower()
            caplog.clear()
    
    def test_validate_infinity_value(self, collector, caplog):
        """Test validation of infinity values (should return None)."""
        test_cases = [float('inf'), float('-inf')]
        
        for value in test_cases:
            result = collector._validate_metric_value('test_metric', value)
            assert result is None, \
                f"Infinity value {value} should return None, got {result}"
            
            # Should log warning
            assert 'Invalid metric value' in caplog.text
            assert 'infinity' in caplog.text.lower()
            caplog.clear()
    
    def test_validate_nan_value(self, collector, caplog):
        """Test validation of NaN values (should return None)."""
        result = collector._validate_metric_value('test_metric', float('nan'))
        assert result is None
        
        # Should log warning
        assert 'Invalid metric value' in caplog.text
        assert 'nan' in caplog.text.lower()
    
    def test_validate_string_numeric_value(self, collector):
        """Test validation of string numeric values (should convert to float)."""
        test_cases = [
            ('100', 100.0),
            ('100.5', 100.5),
            ('0', 0.0),
            ('0.001', 0.001)
        ]
        
        for input_value, expected in test_cases:
            result = collector._validate_metric_value('test_metric', input_value)
            assert result == expected, \
                f"Failed to convert '{input_value}' to {expected}, got {result}"
    
    def test_validate_integer_value(self, collector):
        """Test validation of integer values (should convert to float)."""
        test_cases = [
            (0, 0.0),
            (1, 1.0),
            (100, 100.0),
            (1000000, 1000000.0)
        ]
        
        for input_value, expected in test_cases:
            result = collector._validate_metric_value('test_metric', input_value)
            assert result == expected, \
                f"Failed to convert {input_value} to {expected}, got {result}"
    
    def test_validate_non_numeric_string(self, collector, caplog):
        """Test validation of non-numeric strings (should return None)."""
        test_cases = ['abc', 'not a number', '', 'N/A']
        
        for value in test_cases:
            result = collector._validate_metric_value('test_metric', value)
            assert result is None, \
                f"Non-numeric string '{value}' should return None, got {result}"
            
            # Should log warning
            assert 'Invalid metric value' in caplog.text
            assert 'not numeric' in caplog.text.lower()
            caplog.clear()
    
    def test_validate_invalid_types(self, collector, caplog):
        """Test validation of invalid types (should return None)."""
        test_cases = [[], {}, object(), lambda: None]
        
        for value in test_cases:
            result = collector._validate_metric_value('test_metric', value)
            assert result is None, \
                f"Invalid type {type(value)} should return None, got {result}"
            
            # Should log warning
            assert 'Invalid metric value' in caplog.text
            caplog.clear()
    
    def test_validate_metric_value_property_7(self, collector):
        """
        Property 7: Metric Value Validation
        
        For any metric value (time, count, or rate), validation SHALL verify
        that value is non-negative, not infinity, and not NaN.
        """
        # Valid values should pass
        assert collector._validate_metric_value('cpu_time', 100.0) == 100.0
        assert collector._validate_metric_value('execution_count', 50) == 50.0
        assert collector._validate_metric_value('executions_per_sec', 0.5) == 0.5
        
        # Negative values should return None
        assert collector._validate_metric_value('cpu_time', -100.0) is None
        
        # Infinity should return None
        assert collector._validate_metric_value('cpu_time', float('inf')) is None
        assert collector._validate_metric_value('cpu_time', float('-inf')) is None
        
        # NaN should return None
        assert collector._validate_metric_value('cpu_time', float('nan')) is None
    
    def test_validate_preserves_precision(self, collector):
        """Test that validation preserves floating point precision."""
        test_cases = [
            0.123456789,
            123.456789,
            0.000001,
            999999.999999
        ]
        
        for value in test_cases:
            result = collector._validate_metric_value('test_metric', value)
            assert result == value, \
                f"Precision not preserved: {value} != {result}"
    
    def test_validate_large_values(self, collector):
        """Test validation of very large values."""
        large_values = [
            1e6,   # 1 million
            1e9,   # 1 billion
            1e12,  # 1 trillion
        ]
        
        for value in large_values:
            result = collector._validate_metric_value('test_metric', value)
            assert result == value, \
                f"Large value {value} not validated correctly, got {result}"
    
    def test_validate_small_values(self, collector):
        """Test validation of very small positive values."""
        small_values = [
            1e-6,   # 0.000001
            1e-9,   # 0.000000001
            1e-12,  # 0.000000000001
        ]
        
        for value in small_values:
            result = collector._validate_metric_value('test_metric', value)
            assert result == value, \
                f"Small value {value} not validated correctly, got {result}"
    
    def test_validate_different_metric_names(self, collector):
        """Test validation works with different metric names."""
        metric_names = [
            'cpu_time',
            'lock_time',
            'executions_per_second',
            'rows_examined',
            'read_io_bytes'
        ]
        
        for metric_name in metric_names:
            result = collector._validate_metric_value(metric_name, 100.0)
            assert result == 100.0, \
                f"Validation failed for metric '{metric_name}'"
    
    def test_validate_logs_metric_name_in_warnings(self, collector, caplog):
        """Test that warnings include the metric name for debugging."""
        collector._validate_metric_value('cpu_time_ms', -100)
        assert 'cpu_time_ms' in caplog.text
        
        caplog.clear()
        
        collector._validate_metric_value('lock_time_ms', float('inf'))
        assert 'lock_time_ms' in caplog.text
        
        caplog.clear()
        
        collector._validate_metric_value('rows_examined', 'invalid')
        assert 'rows_examined' in caplog.text
