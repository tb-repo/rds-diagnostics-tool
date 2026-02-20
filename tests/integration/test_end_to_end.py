"""End-to-end integration tests for RDS Diagnostics Tool."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from click.testing import CliRunner

from cli.main import cli
from core.models import (
    RDSInstanceInfo, MetricDataPoint, MetricSeries, IOPSMetrics,
    StorageMetrics, CloudWatchMetrics, Severity, ReportType, OutputFormat
)


@pytest.fixture
def mock_rds_instance():
    """Create a mock RDS instance."""
    return RDSInstanceInfo(
        instance_id="test-db-instance",
        resource_id="db-ABCDEFGHIJKLMNOP",
        engine="postgres",
        engine_version="14.7",
        instance_class="db.t3.medium",
        status="available",
        storage_type="gp2",
        allocated_storage=100,
        max_connections=100,
        availability_zone="ap-southeast-1a"
    )


@pytest.fixture
def mock_metrics(mock_rds_instance):
    """Create mock CloudWatch metrics."""
    now = datetime.utcnow()
    
    cpu_data = [
        MetricDataPoint(timestamp=now - timedelta(minutes=i*5), value=50.0 + i, unit="Percent")
        for i in range(12)
    ]
    
    memory_data = [
        MetricDataPoint(timestamp=now - timedelta(minutes=i*5), value=1000000000.0, unit="Bytes")
        for i in range(12)
    ]
    
    connections_data = [
        MetricDataPoint(timestamp=now - timedelta(minutes=i*5), value=10.0, unit="Count")
        for i in range(12)
    ]
    
    read_iops_data = [
        MetricDataPoint(timestamp=now - timedelta(minutes=i*5), value=100.0, unit="Count/Second")
        for i in range(12)
    ]
    
    write_iops_data = [
        MetricDataPoint(timestamp=now - timedelta(minutes=i*5), value=50.0, unit="Count/Second")
        for i in range(12)
    ]
    
    free_storage_data = [
        MetricDataPoint(timestamp=now - timedelta(minutes=i*5), value=50000000000.0, unit="Bytes")
        for i in range(12)
    ]
    
    used_storage_data = [
        MetricDataPoint(timestamp=now - timedelta(minutes=i*5), value=50000000000.0, unit="Bytes")
        for i in range(12)
    ]
    
    return CloudWatchMetrics(
        instance_info=mock_rds_instance,
        cpu_utilization=MetricSeries("CPUUtilization", cpu_data, "Percent"),
        freeable_memory=MetricSeries("FreeableMemory", memory_data, "Bytes"),
        database_connections=MetricSeries("DatabaseConnections", connections_data, "Count"),
        iops=IOPSMetrics(
            read_iops=MetricSeries("ReadIOPS", read_iops_data, "Count/Second"),
            write_iops=MetricSeries("WriteIOPS", write_iops_data, "Count/Second")
        ),
        storage=StorageMetrics(
            free_storage=MetricSeries("FreeStorageSpace", free_storage_data, "Bytes"),
            used_storage=MetricSeries("UsedStorageSpace", used_storage_data, "Bytes"),
            total_storage=100000000000
        ),
        collection_time=now
    )


class TestListCommand:
    """Test the 'list' command end-to-end."""
    
    @patch('cli.main.RDSDiagnosticsApp')
    def test_list_command_success(self, mock_app_class, mock_rds_instance):
        """Test successful list command execution."""
        # Setup mock
        mock_app = Mock()
        mock_app.list_instances.return_value = [mock_rds_instance]
        mock_app_class.return_value = mock_app
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, ['list'])
        
        # Assertions
        assert result.exit_code == 0
        assert "test-db-instance" in result.output
        assert "postgres" in result.output
        assert "available" in result.output
        assert "db.t3.medium" in result.output
    
    @patch('cli.main.RDSDiagnosticsApp')
    def test_list_command_no_instances(self, mock_app_class):
        """Test list command with no instances found."""
        # Setup mock
        mock_app = Mock()
        mock_app.list_instances.return_value = []
        mock_app_class.return_value = mock_app
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, ['list'])
        
        # Assertions
        assert result.exit_code == 0
        assert "No RDS instances found" in result.output
    
    @patch('cli.main.RDSDiagnosticsApp')
    def test_list_command_with_profile(self, mock_app_class, mock_rds_instance):
        """Test list command with AWS profile specified."""
        # Setup mock
        mock_app = Mock()
        mock_app.list_instances.return_value = [mock_rds_instance]
        mock_app_class.return_value = mock_app
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, ['--profile', 'test-profile', 'list'])
        
        # Assertions
        assert result.exit_code == 0
        assert "test-db-instance" in result.output


class TestDiagnoseCommand:
    """Test the 'diagnose' command end-to-end."""
    
    @patch('cli.main.RDSDiagnosticsApp')
    def test_diagnose_command_success(self, mock_app_class, mock_rds_instance, mock_metrics):
        """Test successful diagnose command execution."""
        from core.models import DiagnosticData, MetricAnalysis
        
        # Setup mock
        mock_app = Mock()
        
        diagnostic_data = DiagnosticData(
            instance_info=mock_rds_instance,
            cloudwatch_metrics=mock_metrics,
            performance_insights_queries=None,
            wait_events=None,
            analysis=MetricAnalysis(
                violations=[],
                trends=[],
                overall_severity=Severity.NORMAL,
                summary="All metrics within normal range"
            ),
            recommendations=[],
            collection_timestamp=datetime.utcnow()
        )
        
        mock_app.run_diagnostics.return_value = diagnostic_data
        mock_app_class.return_value = mock_app
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, ['diagnose', '--instance', 'test-db-instance'])
        
        # Assertions
        assert result.exit_code == 0
        assert "Diagnostic Summary" in result.output
        assert "test-db-instance" in result.output
        assert "postgres" in result.output
        assert "NORMAL" in result.output
    
    @patch('cli.main.RDSDiagnosticsApp')
    def test_diagnose_command_invalid_instance_id(self, mock_app_class):
        """Test diagnose command with invalid instance ID format."""
        # Run command with invalid instance ID
        runner = CliRunner()
        result = runner.invoke(cli, ['diagnose', '--instance', '123-invalid'])
        
        # Assertions
        assert result.exit_code == 1
        assert "Invalid instance ID format" in result.output
    
    @patch('cli.main.RDSDiagnosticsApp')
    def test_diagnose_command_with_time_range(self, mock_app_class, mock_rds_instance, mock_metrics):
        """Test diagnose command with custom time range."""
        from core.models import DiagnosticData, MetricAnalysis
        
        # Setup mock
        mock_app = Mock()
        
        diagnostic_data = DiagnosticData(
            instance_info=mock_rds_instance,
            cloudwatch_metrics=mock_metrics,
            performance_insights_queries=None,
            wait_events=None,
            analysis=MetricAnalysis(
                violations=[],
                trends=[],
                overall_severity=Severity.NORMAL,
                summary="All metrics within normal range"
            ),
            recommendations=[],
            collection_timestamp=datetime.utcnow()
        )
        
        mock_app.run_diagnostics.return_value = diagnostic_data
        mock_app_class.return_value = mock_app
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, ['diagnose', '--instance', 'test-db', '--time-range', '24h'])
        
        # Assertions
        assert result.exit_code == 0
        assert "Diagnostic Summary" in result.output


class TestReportCommand:
    """Test the 'report' command end-to-end."""
    
    @patch('cli.main.RDSDiagnosticsApp')
    def test_report_command_technical_text(self, mock_app_class):
        """Test report command generating technical report in text format."""
        from core.models import Report
        
        # Setup mock
        mock_app = Mock()
        mock_report = Report(
            report_type=ReportType.TECHNICAL,
            content="Technical Report Content\n\nInstance: test-db\nCPU: 50%",
            format=OutputFormat.TEXT,
            generated_at=datetime.utcnow()
        )
        mock_app.run_full_diagnostic_with_report.return_value = mock_report
        mock_app_class.return_value = mock_app
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, ['report', '--instance', 'test-db'])
        
        # Assertions
        assert result.exit_code == 0
        assert "Technical Report Content" in result.output
    
    @patch('cli.main.RDSDiagnosticsApp')
    def test_report_command_management_json(self, mock_app_class):
        """Test report command generating management report in JSON format."""
        from core.models import Report
        import json
        
        # Setup mock
        mock_app = Mock()
        report_content = json.dumps({
            "report_type": "management",
            "summary": "System healthy",
            "severity": "normal"
        })
        mock_report = Report(
            report_type=ReportType.MANAGEMENT,
            content=report_content,
            format=OutputFormat.JSON,
            generated_at=datetime.utcnow()
        )
        mock_app.run_full_diagnostic_with_report.return_value = mock_report
        mock_app_class.return_value = mock_app
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, [
            'report',
            '--instance', 'test-db',
            '--report-type', 'management',
            '--format', 'json'
        ])
        
        # Assertions
        assert result.exit_code == 0
        assert "management" in result.output
    
    @patch('cli.main.RDSDiagnosticsApp')
    def test_report_command_file_output(self, mock_app_class, tmp_path):
        """Test report command with file output."""
        from core.models import Report
        
        # Setup mock
        mock_app = Mock()
        mock_report = Report(
            report_type=ReportType.TECHNICAL,
            content="Technical Report Content",
            format=OutputFormat.TEXT,
            generated_at=datetime.utcnow()
        )
        mock_app.run_full_diagnostic_with_report.return_value = mock_report
        mock_app_class.return_value = mock_app
        
        # Create output file path
        output_file = tmp_path / "report.txt"
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, [
            'report',
            '--instance', 'test-db',
            '--output', str(output_file)
        ])
        
        # Assertions
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Report saved to" in result.output
        
        # Verify file content
        content = output_file.read_text()
        assert "Technical Report Content" in content


class TestVersionCommand:
    """Test the 'version' command."""
    
    def test_version_command(self):
        """Test version command displays version information."""
        runner = CliRunner()
        result = runner.invoke(cli, ['version'])
        
        assert result.exit_code == 0
        assert "RDS Diagnostics Tool" in result.output
        assert "0.1.0" in result.output


class TestVerboseMode:
    """Test verbose mode across commands."""
    
    @patch('cli.main.RDSDiagnosticsApp')
    def test_list_verbose(self, mock_app_class, mock_rds_instance):
        """Test list command with verbose flag."""
        mock_app = Mock()
        mock_app.list_instances.return_value = [mock_rds_instance]
        mock_app_class.return_value = mock_app
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--verbose', 'list'])
        
        assert result.exit_code == 0
        assert "Listing RDS instances" in result.output or "Connecting to AWS" in result.output


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('cli.main.RDSDiagnosticsApp')
    def test_authentication_error(self, mock_app_class):
        """Test handling of authentication errors."""
        from aws.clients import AWSClientError
        
        mock_app_class.side_effect = AWSClientError("Invalid credentials")
        
        runner = CliRunner()
        result = runner.invoke(cli, ['list'])
        
        assert result.exit_code == 1
        assert "ERROR" in result.output
    
    def test_invalid_time_range_format(self):
        """Test handling of invalid time range format."""
        runner = CliRunner()
        result = runner.invoke(cli, ['diagnose', '--instance', 'test-db', '--time-range', 'invalid'])
        
        assert result.exit_code == 1
        assert "ERROR" in result.output
