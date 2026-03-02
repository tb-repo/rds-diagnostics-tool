"""Configuration management for RDS Diagnostics Tool."""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import logging

from core.models import TimeRange, OutputFormat

logger = logging.getLogger(__name__)


@dataclass
class MetricThresholds:
    """Threshold values for metric alerts."""
    cpu_warning: float = 70.0
    cpu_critical: float = 90.0
    memory_warning: float = 80.0
    memory_critical: float = 95.0
    connections_warning: int = 80  # percentage of max
    connections_critical: int = 95
    iops_warning: float = 80.0  # percentage of provisioned
    iops_critical: float = 95.0
    storage_warning: float = 80.0  # percentage used
    storage_critical: float = 90.0
    
    def validate(self) -> list[str]:
        """
        Validate threshold values and return list of error messages.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check for negative values
        for field_name, value in asdict(self).items():
            if value < 0:
                errors.append(f"{field_name} cannot be negative: {value}")
        
        # Check warning < critical
        if self.cpu_warning >= self.cpu_critical:
            errors.append(
                f"cpu_warning ({self.cpu_warning}) must be less than "
                f"cpu_critical ({self.cpu_critical})"
            )
        
        if self.memory_warning >= self.memory_critical:
            errors.append(
                f"memory_warning ({self.memory_warning}) must be less than "
                f"memory_critical ({self.memory_critical})"
            )
        
        if self.connections_warning >= self.connections_critical:
            errors.append(
                f"connections_warning ({self.connections_warning}) must be less than "
                f"connections_critical ({self.connections_critical})"
            )
        
        if self.iops_warning >= self.iops_critical:
            errors.append(
                f"iops_warning ({self.iops_warning}) must be less than "
                f"iops_critical ({self.iops_critical})"
            )
        
        if self.storage_warning >= self.storage_critical:
            errors.append(
                f"storage_warning ({self.storage_warning}) must be less than "
                f"storage_critical ({self.storage_critical})"
            )
        
        # Check percentage values are in valid range (0-100)
        percentage_fields = [
            ("cpu_warning", self.cpu_warning),
            ("cpu_critical", self.cpu_critical),
            ("memory_warning", self.memory_warning),
            ("memory_critical", self.memory_critical),
            ("connections_warning", self.connections_warning),
            ("connections_critical", self.connections_critical),
            ("iops_warning", self.iops_warning),
            ("iops_critical", self.iops_critical),
            ("storage_warning", self.storage_warning),
            ("storage_critical", self.storage_critical),
        ]
        
        for field_name, value in percentage_fields:
            if value > 100:
                errors.append(f"{field_name} cannot exceed 100%: {value}")
        
        return errors


@dataclass
class PerformanceInsightsConfig:
    """Configuration for Performance Insights data collection."""
    enabled: bool = True
    max_queries: int = 25
    collect_enhanced_metrics: bool = True
    fallback_on_error: bool = True
    collect_cpu_metrics: bool = True
    collect_lock_metrics: bool = True
    collect_io_metrics: bool = True
    collect_row_metrics: bool = True
    
    def validate(self) -> list[str]:
        """
        Validate Performance Insights configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if self.max_queries < 1:
            errors.append(f"max_queries must be at least 1: {self.max_queries}")
        
        if self.max_queries > 100:
            errors.append(f"max_queries cannot exceed 100: {self.max_queries}")
        
        return errors


@dataclass
class Configuration:
    """Application configuration."""
    aws_profile: Optional[str] = None
    default_region: str = "ap-southeast-1"
    default_time_range: str = "1h"
    metric_thresholds: MetricThresholds = field(default_factory=MetricThresholds)
    performance_insights: PerformanceInsightsConfig = field(default_factory=PerformanceInsightsConfig)
    output_format: OutputFormat = OutputFormat.TEXT
    
    @staticmethod
    def load_from_file(path: str) -> "Configuration":
        """
        Load configuration from a YAML file.
        
        Args:
            path: Path to configuration file
            
        Returns:
            Configuration object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is malformed
        """
        config_path = Path(path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse configuration file: {e}")
        
        if data is None:
            data = {}
        
        # Parse thresholds
        thresholds_data = data.get('thresholds', {})
        thresholds = MetricThresholds()
        
        if 'cpu' in thresholds_data:
            thresholds.cpu_warning = thresholds_data['cpu'].get('warning', 70.0)
            thresholds.cpu_critical = thresholds_data['cpu'].get('critical', 90.0)
        
        if 'memory' in thresholds_data:
            thresholds.memory_warning = thresholds_data['memory'].get('warning', 80.0)
            thresholds.memory_critical = thresholds_data['memory'].get('critical', 95.0)
        
        if 'connections' in thresholds_data:
            thresholds.connections_warning = thresholds_data['connections'].get('warning', 80)
            thresholds.connections_critical = thresholds_data['connections'].get('critical', 95)
        
        if 'iops' in thresholds_data:
            thresholds.iops_warning = thresholds_data['iops'].get('warning', 80.0)
            thresholds.iops_critical = thresholds_data['iops'].get('critical', 95.0)
        
        if 'storage' in thresholds_data:
            thresholds.storage_warning = thresholds_data['storage'].get('warning', 80.0)
            thresholds.storage_critical = thresholds_data['storage'].get('critical', 90.0)
        
        # Validate thresholds
        validation_errors = thresholds.validate()
        if validation_errors:
            for error in validation_errors:
                logger.error(f"Configuration validation error: {error}")
            logger.warning("Using default values for invalid threshold settings")
            thresholds = MetricThresholds()
        
        # Parse Performance Insights configuration
        pi_data = data.get('performance_insights', {})
        pi_config = PerformanceInsightsConfig(
            enabled=pi_data.get('enabled', True),
            max_queries=pi_data.get('max_queries', 25),
            collect_enhanced_metrics=pi_data.get('collect_enhanced_metrics', True),
            fallback_on_error=pi_data.get('fallback_on_error', True),
            collect_cpu_metrics=pi_data.get('collect_cpu_metrics', True),
            collect_lock_metrics=pi_data.get('collect_lock_metrics', True),
            collect_io_metrics=pi_data.get('collect_io_metrics', True),
            collect_row_metrics=pi_data.get('collect_row_metrics', True)
        )
        
        # Validate Performance Insights configuration
        pi_validation_errors = pi_config.validate()
        if pi_validation_errors:
            for error in pi_validation_errors:
                logger.error(f"Performance Insights configuration validation error: {error}")
            logger.warning("Using default values for invalid Performance Insights settings")
            pi_config = PerformanceInsightsConfig()
        
        # Parse output format
        output_format_str = data.get('output_format', 'text').lower()
        try:
            output_format = OutputFormat(output_format_str)
        except ValueError:
            logger.warning(
                f"Invalid output format '{output_format_str}', using default 'text'"
            )
            output_format = OutputFormat.TEXT
        
        return Configuration(
            aws_profile=data.get('aws_profile'),
            default_region=data.get('default_region', 'ap-southeast-1'),
            default_time_range=data.get('default_time_range', '1h'),
            metric_thresholds=thresholds,
            performance_insights=pi_config,
            output_format=output_format
        )
    
    @staticmethod
    def load_defaults() -> "Configuration":
        """
        Load default configuration.
        
        Returns:
            Configuration object with default values
        """
        return Configuration()
    
    def merge_with_cli_args(self, cli_args: Dict[str, Any]) -> "Configuration":
        """
        Merge configuration with command-line arguments.
        Command-line arguments take precedence over config file values.
        
        Args:
            cli_args: Dictionary of command-line arguments
            
        Returns:
            New Configuration object with merged values
        """
        # Create a copy of current config
        merged = Configuration(
            aws_profile=self.aws_profile,
            default_region=self.default_region,
            default_time_range=self.default_time_range,
            metric_thresholds=MetricThresholds(
                cpu_warning=self.metric_thresholds.cpu_warning,
                cpu_critical=self.metric_thresholds.cpu_critical,
                memory_warning=self.metric_thresholds.memory_warning,
                memory_critical=self.metric_thresholds.memory_critical,
                connections_warning=self.metric_thresholds.connections_warning,
                connections_critical=self.metric_thresholds.connections_critical,
                iops_warning=self.metric_thresholds.iops_warning,
                iops_critical=self.metric_thresholds.iops_critical,
                storage_warning=self.metric_thresholds.storage_warning,
                storage_critical=self.metric_thresholds.storage_critical,
            ),
            performance_insights=PerformanceInsightsConfig(
                enabled=self.performance_insights.enabled,
                max_queries=self.performance_insights.max_queries,
                collect_enhanced_metrics=self.performance_insights.collect_enhanced_metrics,
                fallback_on_error=self.performance_insights.fallback_on_error,
                collect_cpu_metrics=self.performance_insights.collect_cpu_metrics,
                collect_lock_metrics=self.performance_insights.collect_lock_metrics,
                collect_io_metrics=self.performance_insights.collect_io_metrics,
                collect_row_metrics=self.performance_insights.collect_row_metrics,
            ),
            output_format=self.output_format
        )
        
        # Override with CLI args if provided
        if cli_args.get('profile') is not None:
            merged.aws_profile = cli_args['profile']
        
        if cli_args.get('region') is not None:
            merged.default_region = cli_args['region']
        
        if cli_args.get('time_range') is not None:
            merged.default_time_range = cli_args['time_range']
        
        if cli_args.get('format') is not None:
            try:
                merged.output_format = OutputFormat(cli_args['format'])
            except ValueError:
                logger.warning(
                    f"Invalid output format '{cli_args['format']}', "
                    f"keeping current value"
                )
        
        # Override threshold values if provided
        if cli_args.get('cpu_warning') is not None:
            merged.metric_thresholds.cpu_warning = cli_args['cpu_warning']
        
        if cli_args.get('cpu_critical') is not None:
            merged.metric_thresholds.cpu_critical = cli_args['cpu_critical']
        
        if cli_args.get('memory_warning') is not None:
            merged.metric_thresholds.memory_warning = cli_args['memory_warning']
        
        if cli_args.get('memory_critical') is not None:
            merged.metric_thresholds.memory_critical = cli_args['memory_critical']
        
        return merged
