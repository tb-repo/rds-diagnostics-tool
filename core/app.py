"""Application core orchestration."""

import logging
from typing import List, Optional

from core.config import Configuration
from core.models import (
    RDSInstanceInfo, DiagnosticData, Report, TimeRange,
    ReportType, OutputFormat
)
from aws.clients import AWSClientFactory, AWSClientError
from collectors.instance_info import InstanceInfoCollector
from collectors.metrics import MetricsCollector
from collectors.performance_insights import PerformanceInsightsCollector
from analysis.analyzer import DiagnosticAnalyzer
from reporting.generator import ReportGenerator

logger = logging.getLogger(__name__)


class RDSDiagnosticsApp:
    """Main application orchestrator for RDS diagnostics."""
    
    def __init__(self, config: Configuration):
        """
        Initialize RDS Diagnostics application.
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Initialize AWS clients
        try:
            self.aws_factory = AWSClientFactory(
                profile=config.aws_profile,
                region=config.default_region
            )
            self.rds_client = self.aws_factory.create_rds_client()
            self.cloudwatch_client = self.aws_factory.create_cloudwatch_client()
            self.pi_client = self.aws_factory.create_performance_insights_client()
        except AWSClientError as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise
        
        # Initialize collectors
        self.instance_collector = InstanceInfoCollector(self.rds_client)
        self.metrics_collector = MetricsCollector(
            self.cloudwatch_client,
            self.rds_client
        )
        self.pi_collector = PerformanceInsightsCollector(
            self.pi_client,
            self.rds_client
        )
        
        # Initialize analyzer and report generator
        self.analyzer = DiagnosticAnalyzer(config.metric_thresholds)
        self.report_generator = ReportGenerator()
    
    def list_instances(self) -> List[RDSInstanceInfo]:
        """
        List all RDS instances in the configured region.
        
        Returns:
            List of RDSInstanceInfo objects
            
        Raises:
            AWSClientError: If instances cannot be listed
        """
        logger.info(f"Listing RDS instances in region {self.config.default_region}")
        
        try:
            instances = self.instance_collector.list_all_instances()
            logger.info(f"Found {len(instances)} RDS instances")
            return instances
        except AWSClientError as e:
            logger.error(f"Failed to list instances: {e}")
            raise
    
    def run_diagnostics(
        self,
        instance_id: str,
        time_range: Optional[TimeRange] = None
    ) -> DiagnosticData:
        """
        Run complete diagnostics on an RDS instance.
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for metrics (uses default if None)
            
        Returns:
            DiagnosticData object with complete analysis
            
        Raises:
            AWSClientError: If diagnostics cannot be completed
        """
        logger.info(f"Running diagnostics for instance: {instance_id}")
        
        # Use default time range if not provided
        if time_range is None:
            time_range = TimeRange.from_duration(self.config.default_time_range)
            logger.info(f"Using default time range: {self.config.default_time_range}")
        
        try:
            # Collect instance information
            logger.info("Collecting instance information...")
            instance_info = self.instance_collector.get_instance_details(instance_id)
            
            # Collect CloudWatch metrics
            logger.info("Collecting CloudWatch metrics...")
            cloudwatch_metrics = self.metrics_collector.collect_all_metrics(
                instance_id,
                time_range,
                instance_info
            )
            
            # Collect Performance Insights data (if enabled)
            logger.info("Checking Performance Insights availability...")
            pi_queries = None
            wait_events = None
            
            if self.pi_collector.is_performance_insights_enabled(instance_id):
                logger.info("Collecting Performance Insights data...")
                try:
                    pi_queries = self.pi_collector.collect_top_sql_queries(
                        instance_id,
                        time_range
                    )
                    wait_events = self.pi_collector.collect_wait_events(
                        instance_id,
                        time_range
                    )
                except AWSClientError as e:
                    logger.warning(f"Failed to collect Performance Insights data: {e}")
                    # Continue without PI data
            else:
                logger.info("Performance Insights not enabled for this instance")
            
            # Analyze metrics
            logger.info("Analyzing metrics...")
            analysis = self.analyzer.analyze_metrics(cloudwatch_metrics)
            
            # Generate recommendations
            logger.info("Generating recommendations...")
            recommendations = self.analyzer.generate_recommendations(
                analysis,
                pi_queries or []
            )
            
            # Create diagnostic data
            diagnostic_data = DiagnosticData(
                instance_info=instance_info,
                cloudwatch_metrics=cloudwatch_metrics,
                performance_insights_queries=pi_queries,
                wait_events=wait_events,
                analysis=analysis,
                recommendations=recommendations,
                collection_timestamp=cloudwatch_metrics.collection_time
            )
            
            logger.info("Diagnostics completed successfully")
            return diagnostic_data
            
        except AWSClientError as e:
            logger.error(f"Failed to run diagnostics: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during diagnostics: {e}", exc_info=True)
            raise AWSClientError(f"Diagnostics failed: {str(e)}")
    
    def generate_report(
        self,
        diagnostic_data: DiagnosticData,
        report_type: ReportType,
        output_format: Optional[OutputFormat] = None
    ) -> Report:
        """
        Generate a formatted report from diagnostic data.
        
        Args:
            diagnostic_data: Complete diagnostic data
            report_type: Type of report (technical or management)
            output_format: Output format (uses config default if None)
            
        Returns:
            Report object with formatted content
        """
        if output_format is None:
            output_format = self.config.output_format
        
        logger.info(
            f"Generating {report_type.value} report in {output_format.value} format"
        )
        
        try:
            report = self.report_generator.generate_report(
                diagnostic_data,
                report_type,
                output_format
            )
            logger.info("Report generated successfully")
            return report
        except Exception as e:
            logger.error(f"Failed to generate report: {e}", exc_info=True)
            raise
    
    def run_full_diagnostic_with_report(
        self,
        instance_id: str,
        report_type: ReportType = ReportType.TECHNICAL,
        time_range: Optional[TimeRange] = None,
        output_format: Optional[OutputFormat] = None
    ) -> Report:
        """
        Run diagnostics and generate report in one operation.
        
        Args:
            instance_id: RDS instance identifier
            report_type: Type of report to generate
            time_range: Time range for metrics
            output_format: Output format
            
        Returns:
            Generated report
            
        Raises:
            AWSClientError: If operation fails
        """
        logger.info(f"Running full diagnostic with report for {instance_id}")
        
        # Run diagnostics
        diagnostic_data = self.run_diagnostics(instance_id, time_range)
        
        # Generate report
        report = self.generate_report(diagnostic_data, report_type, output_format)
        
        return report
