"""Unit tests for Performance Insights configuration."""

import pytest
import tempfile
from pathlib import Path

from core.config import Configuration, PerformanceInsightsConfig


class TestPerformanceInsightsConfig:
    """Test suite for Performance Insights configuration."""
    
    def test_default_values(self):
        """Test default Performance Insights configuration values."""
        pi_config = PerformanceInsightsConfig()
        
        assert pi_config.enabled is True
        assert pi_config.max_queries == 25
        assert pi_config.collect_enhanced_metrics is True
        assert pi_config.fallback_on_error is True
        assert pi_config.collect_cpu_metrics is True
        assert pi_config.collect_lock_metrics is True
        assert pi_config.collect_io_metrics is True
        assert pi_config.collect_row_metrics is True
    
    def test_validate_valid_config(self):
        """Test validation of valid Performance Insights configuration."""
        pi_config = PerformanceInsightsConfig(
            enabled=True,
            max_queries=50,
            collect_enhanced_metrics=True
        )
        
        errors = pi_config.validate()
        assert len(errors) == 0
    
    def test_validate_max_queries_too_low(self):
        """Test validation fails when max_queries is less than 1."""
        pi_config = PerformanceInsightsConfig(max_queries=0)
        
        errors = pi_config.validate()
        assert len(errors) == 1
        assert "max_queries must be at least 1" in errors[0]
    
    def test_validate_max_queries_too_high(self):
        """Test validation fails when max_queries exceeds 100."""
        pi_config = PerformanceInsightsConfig(max_queries=150)
        
        errors = pi_config.validate()
        assert len(errors) == 1
        assert "max_queries cannot exceed 100" in errors[0]
    
    def test_validate_max_queries_boundary_values(self):
        """Test validation passes for boundary values of max_queries."""
        # Test minimum boundary
        pi_config_min = PerformanceInsightsConfig(max_queries=1)
        assert len(pi_config_min.validate()) == 0
        
        # Test maximum boundary
        pi_config_max = PerformanceInsightsConfig(max_queries=100)
        assert len(pi_config_max.validate()) == 0
    
    def test_configuration_includes_pi_config(self):
        """Test that Configuration includes Performance Insights config."""
        config = Configuration()
        
        assert hasattr(config, 'performance_insights')
        assert isinstance(config.performance_insights, PerformanceInsightsConfig)
        assert config.performance_insights.enabled is True
    
    def test_load_from_file_with_pi_config(self):
        """Test loading Performance Insights configuration from YAML file."""
        yaml_content = """
aws_profile: test-profile
default_region: us-east-1

performance_insights:
  enabled: false
  max_queries: 10
  collect_enhanced_metrics: false
  fallback_on_error: false
  collect_cpu_metrics: false
  collect_lock_metrics: true
  collect_io_metrics: true
  collect_row_metrics: false
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = Configuration.load_from_file(temp_path)
            
            assert config.performance_insights.enabled is False
            assert config.performance_insights.max_queries == 10
            assert config.performance_insights.collect_enhanced_metrics is False
            assert config.performance_insights.fallback_on_error is False
            assert config.performance_insights.collect_cpu_metrics is False
            assert config.performance_insights.collect_lock_metrics is True
            assert config.performance_insights.collect_io_metrics is True
            assert config.performance_insights.collect_row_metrics is False
        finally:
            Path(temp_path).unlink()
    
    def test_load_from_file_with_partial_pi_config(self):
        """Test loading with partial Performance Insights configuration uses defaults."""
        yaml_content = """
aws_profile: test-profile

performance_insights:
  max_queries: 15
  collect_cpu_metrics: false
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = Configuration.load_from_file(temp_path)
            
            # Specified values
            assert config.performance_insights.max_queries == 15
            assert config.performance_insights.collect_cpu_metrics is False
            
            # Default values for unspecified fields
            assert config.performance_insights.enabled is True
            assert config.performance_insights.collect_enhanced_metrics is True
            assert config.performance_insights.fallback_on_error is True
            assert config.performance_insights.collect_lock_metrics is True
            assert config.performance_insights.collect_io_metrics is True
            assert config.performance_insights.collect_row_metrics is True
        finally:
            Path(temp_path).unlink()
    
    def test_load_from_file_without_pi_config(self):
        """Test loading without Performance Insights configuration uses defaults."""
        yaml_content = """
aws_profile: test-profile
default_region: us-east-1
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = Configuration.load_from_file(temp_path)
            
            # Should use all default values
            assert config.performance_insights.enabled is True
            assert config.performance_insights.max_queries == 25
            assert config.performance_insights.collect_enhanced_metrics is True
            assert config.performance_insights.fallback_on_error is True
        finally:
            Path(temp_path).unlink()
    
    def test_load_from_file_with_invalid_pi_config(self):
        """Test loading with invalid Performance Insights configuration uses defaults."""
        yaml_content = """
aws_profile: test-profile

performance_insights:
  max_queries: 200  # Invalid: exceeds 100
  collect_enhanced_metrics: true
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = Configuration.load_from_file(temp_path)
            
            # Should fall back to default values due to validation error
            assert config.performance_insights.max_queries == 25  # Default
            assert config.performance_insights.enabled is True
        finally:
            Path(temp_path).unlink()
    
    def test_merge_with_cli_args_preserves_pi_config(self):
        """Test that merging with CLI args preserves Performance Insights config."""
        config = Configuration()
        config.performance_insights.max_queries = 50
        config.performance_insights.enabled = False
        
        cli_args = {
            'profile': 'new-profile',
            'region': 'us-west-2'
        }
        
        merged = config.merge_with_cli_args(cli_args)
        
        # CLI args should be applied
        assert merged.aws_profile == 'new-profile'
        assert merged.default_region == 'us-west-2'
        
        # Performance Insights config should be preserved
        assert merged.performance_insights.max_queries == 50
        assert merged.performance_insights.enabled is False
