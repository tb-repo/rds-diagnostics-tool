"""Unit tests for configuration management."""

import pytest
import tempfile
import os
from pathlib import Path

from core.config import Configuration, MetricThresholds
from core.models import OutputFormat


class TestMetricThresholds:
    """Tests for MetricThresholds."""
    
    def test_default_values(self):
        """Test default threshold values."""
        thresholds = MetricThresholds()
        assert thresholds.cpu_warning == 70.0
        assert thresholds.cpu_critical == 90.0
        assert thresholds.memory_warning == 80.0
        assert thresholds.memory_critical == 95.0
    
    def test_validate_valid_thresholds(self):
        """Test validation passes for valid thresholds."""
        thresholds = MetricThresholds()
        errors = thresholds.validate()
        assert len(errors) == 0
    
    def test_validate_negative_values(self):
        """Test validation catches negative values."""
        thresholds = MetricThresholds(cpu_warning=-10.0)
        errors = thresholds.validate()
        assert len(errors) > 0
        assert any("negative" in err.lower() for err in errors)
    
    def test_validate_warning_greater_than_critical(self):
        """Test validation catches warning >= critical."""
        thresholds = MetricThresholds(cpu_warning=95.0, cpu_critical=90.0)
        errors = thresholds.validate()
        assert len(errors) > 0
        assert any("cpu_warning" in err and "cpu_critical" in err for err in errors)
    
    def test_validate_percentage_over_100(self):
        """Test validation catches percentages over 100."""
        thresholds = MetricThresholds(cpu_critical=150.0)
        errors = thresholds.validate()
        assert len(errors) > 0
        assert any("100" in err for err in errors)


class TestConfiguration:
    """Tests for Configuration."""
    
    def test_load_defaults(self):
        """Test loading default configuration."""
        config = Configuration.load_defaults()
        assert config.default_region == "ap-southeast-1"
        assert config.default_time_range == "1h"
        assert config.output_format == OutputFormat.TEXT
        assert config.metric_thresholds.cpu_warning == 70.0
    
    def test_load_from_file_not_found(self):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            Configuration.load_from_file("/nonexistent/config.yaml")
    
    def test_load_from_file_valid(self):
        """Test loading from valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
default_region: us-east-1
default_time_range: 24h
output_format: json
thresholds:
  cpu:
    warning: 60.0
    critical: 85.0
  memory:
    warning: 75.0
    critical: 90.0
""")
            f.flush()
            temp_path = f.name
        
        try:
            config = Configuration.load_from_file(temp_path)
            assert config.default_region == "us-east-1"
            assert config.default_time_range == "24h"
            assert config.output_format == OutputFormat.JSON
            assert config.metric_thresholds.cpu_warning == 60.0
            assert config.metric_thresholds.cpu_critical == 85.0
        finally:
            os.unlink(temp_path)
    
    def test_load_from_file_empty(self):
        """Test loading from empty file uses defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            f.flush()
            temp_path = f.name
        
        try:
            config = Configuration.load_from_file(temp_path)
            assert config.default_region == "ap-southeast-1"
            assert config.metric_thresholds.cpu_warning == 70.0
        finally:
            os.unlink(temp_path)
    
    def test_merge_with_cli_args(self):
        """Test merging configuration with CLI arguments."""
        config = Configuration.load_defaults()
        
        cli_args = {
            'profile': 'test-profile',
            'region': 'us-west-2',
            'time_range': '12h',
            'format': 'json',
            'cpu_warning': 65.0
        }
        
        merged = config.merge_with_cli_args(cli_args)
        
        assert merged.aws_profile == 'test-profile'
        assert merged.default_region == 'us-west-2'
        assert merged.default_time_range == '12h'
        assert merged.output_format == OutputFormat.JSON
        assert merged.metric_thresholds.cpu_warning == 65.0
    
    def test_merge_with_cli_args_precedence(self):
        """Test CLI args take precedence over config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
default_region: ap-southeast-1
thresholds:
  cpu:
    warning: 70.0
""")
            f.flush()
            temp_path = f.name
        
        try:
            config = Configuration.load_from_file(temp_path)
            cli_args = {
                'region': 'eu-west-1',
                'cpu_warning': 80.0
            }
            merged = config.merge_with_cli_args(cli_args)
            
            assert merged.default_region == 'eu-west-1'
            assert merged.metric_thresholds.cpu_warning == 80.0
        finally:
            os.unlink(temp_path)
    
    def test_merge_with_empty_cli_args(self):
        """Test merging with empty CLI args preserves config."""
        config = Configuration(
            aws_profile='original-profile',
            default_region='ap-southeast-1'
        )
        
        merged = config.merge_with_cli_args({})
        
        assert merged.aws_profile == 'original-profile'
        assert merged.default_region == 'ap-southeast-1'
