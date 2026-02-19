"""Report generator orchestrator."""

import logging
from datetime import datetime

from core.models import DiagnosticData, Report, ReportType, OutputFormat
from reporting.formatters import TechnicalReportFormatter, ManagementReportFormatter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates reports from diagnostic data."""
    
    def generate_report(
        self,
        diagnostic_data: DiagnosticData,
        report_type: ReportType,
        output_format: OutputFormat = OutputFormat.TEXT
    ) -> Report:
        """
        Generate a report from diagnostic data.
        
        Args:
            diagnostic_data: Complete diagnostic data
            report_type: Type of report (technical or management)
            output_format: Output format (text or JSON)
            
        Returns:
            Report object with formatted content
        """
        logger.info(
            f"Generating {report_type.value} report in {output_format.value} format"
        )
        
        # Route to appropriate formatter
        if report_type == ReportType.TECHNICAL:
            if output_format == OutputFormat.JSON:
                content = TechnicalReportFormatter.format_json(diagnostic_data)
            else:
                content = TechnicalReportFormatter.format(diagnostic_data)
        else:  # MANAGEMENT
            if output_format == OutputFormat.JSON:
                # Management reports use same JSON structure as technical
                content = TechnicalReportFormatter.format_json(diagnostic_data)
            else:
                content = ManagementReportFormatter.format(diagnostic_data)
        
        return Report(
            report_type=report_type,
            content=content,
            format=output_format,
            generated_at=datetime.now()
        )
