"""Main CLI entry point for RDS Diagnostics Tool."""

import logging
import re
from pathlib import Path

import click

from core.config import Configuration
from core.models import ReportType, OutputFormat, TimeRange
from core.app import RDSDiagnosticsApp
from aws.clients import AWSClientError

# Version
__version__ = "0.1.0"

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USER_CANCELLED = 2


# Configure logging
def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


# Validation helpers
def validate_instance_id(instance_id: str) -> tuple[bool, str]:
    """
    Validate RDS instance ID format.
    
    RDS instance IDs must:
    - Be 1-63 characters long
    - Contain only alphanumeric characters and hyphens
    - Start with a letter
    - Not end with a hyphen
    - Not contain two consecutive hyphens
    
    Args:
        instance_id: Instance identifier to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not instance_id:
        return False, "Instance ID cannot be empty"
    
    if len(instance_id) > 63:
        return False, f"Instance ID too long ({len(instance_id)} chars, max 63)"
    
    if not instance_id[0].isalpha():
        return False, "Instance ID must start with a letter"
    
    if instance_id.endswith('-'):
        return False, "Instance ID cannot end with a hyphen"
    
    if '--' in instance_id:
        return False, "Instance ID cannot contain consecutive hyphens"
    
    pattern = r'^[a-zA-Z][a-zA-Z0-9-]{0,62}$'
    if not re.match(pattern, instance_id):
        return False, "Instance ID contains invalid characters (only alphanumeric and hyphens allowed)"
    
    return True, ""


# Error handling helpers
def handle_aws_error(e: AWSClientError, config: Configuration, instance: str, ctx):
    """
    Centralized AWS error handling with helpful suggestions.
    
    Args:
        e: AWS client error
        config: Application configuration
        instance: Instance ID being accessed
        ctx: Click context
    """
    click.echo(f"\nERROR: {e}", err=True)
    
    error_str = str(e).lower()
    if "not found" in error_str or "does not exist" in error_str:
        click.echo(
            f"\nSuggestion: Verify the instance ID '{instance}' is correct.",
            err=True
        )
        click.echo(
            f"Use 'rds-diag list' to see available instances.",
            err=True
        )
    elif "credentials" in error_str or "authentication" in error_str:
        click.echo(
            "\nSuggestion: Check your AWS credentials and profile configuration.",
            err=True
        )
        if config.aws_profile:
            click.echo(
                f"Try running: aws sso login --profile {config.aws_profile}",
                err=True
            )
    elif "permission" in error_str or "authorized" in error_str:
        click.echo(
            "\nSuggestion: Ensure your AWS profile has the required permissions:",
            err=True
        )
        click.echo("  - rds:DescribeDBInstances", err=True)
        click.echo("  - cloudwatch:GetMetricStatistics", err=True)
        click.echo("  - pi:GetResourceMetrics (for Performance Insights)", err=True)
    
    ctx.exit(EXIT_ERROR)


@click.group()
@click.option(
    '--profile', '-p',
    help='AWS CLI profile name',
    default=None
)
@click.option(
    '--region', '-r',
    help='AWS region (default: ap-southeast-1)',
    default=None
)
@click.option(
    '--config', '-c',
    help='Path to configuration file',
    type=click.Path(exists=True),
    default=None
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output with detailed progress information'
)
@click.pass_context
def cli(ctx, profile, region, config, verbose):
    """
    RDS Diagnostics and Reporting Tool
    
    A command-line utility for diagnosing and reporting on AWS RDS instance
    performance across multiple accounts and environments.
    
    Examples:
    
      # List all RDS instances
      rds-diag --profile lt-prd list
      
      # Run diagnostics on an instance
      rds-diag --profile lt-prd diagnose --instance my-db-instance
      
      # Generate a technical report
      rds-diag --profile lt-prd report --instance my-db --time-range 24h --report-type technical
      
      # Generate a management report in JSON format
      rds-diag --profile lt-prd report --instance my-db --report-type management --format json -o report.json
    """
    # Setup logging
    setup_logging(verbose)
    
    # Load configuration
    if config:
        try:
            base_config = Configuration.load_from_file(config)
        except Exception as e:
            click.echo(f"ERROR: Failed to load configuration file: {e}", err=True)
            ctx.exit(EXIT_ERROR)
    else:
        base_config = Configuration.load_defaults()
    
    # Merge with CLI arguments
    cli_args = {
        'profile': profile,
        'region': region,
    }
    merged_config = base_config.merge_with_cli_args(cli_args)
    
    # Store config in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['config'] = merged_config
    ctx.obj['verbose'] = verbose


if __name__ == '__main__':
    cli()


@cli.command()
def version():
    """Display version information."""
    click.echo(f"RDS Diagnostics Tool v{__version__}")
    click.echo("A command-line utility for AWS RDS performance diagnostics and reporting")


@cli.command()
@click.pass_context
def list(ctx):
    """
    List all RDS instances in the configured region.
    
    Displays instance ID, engine type, status, and instance class for each
    RDS instance found in the specified region.
    
    Examples:
    
      # List instances using default profile and region
      rds-diag list
      
      # List instances in a specific account and region
      rds-diag --profile lt-prd --region us-east-1 list
    """
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    if verbose:
        click.echo(f"Listing RDS instances in region: {config.default_region}")
        if config.aws_profile:
            click.echo(f"Using AWS profile: {config.aws_profile}")
    
    try:
        # Initialize application
        app = RDSDiagnosticsApp(config)
        
        if verbose:
            click.echo("Connecting to AWS...")
        
        # List instances
        instances = app.list_instances()
        
        if not instances:
            click.echo("No RDS instances found in this region.")
            return
        
        # Display instances
        click.echo(f"\nFound {len(instances)} RDS instance(s):\n")
        click.echo(f"{'Instance ID':<30} {'Engine':<15} {'Status':<12} {'Instance Class':<20}")
        click.echo("-" * 80)
        
        for instance in instances:
            click.echo(
                f"{instance.instance_id:<30} "
                f"{instance.engine:<15} "
                f"{instance.status:<12} "
                f"{instance.instance_class:<20}"
            )
        
    except AWSClientError as e:
        click.echo(f"\nERROR: {e}", err=True)
        if "credentials" in str(e).lower() or "authentication" in str(e).lower():
            click.echo(
                "\nSuggestion: Check your AWS credentials and profile configuration.",
                err=True
            )
            if config.aws_profile:
                click.echo(
                    f"Try running: aws sso login --profile {config.aws_profile}",
                    err=True
                )
        ctx.exit(EXIT_ERROR)
    except Exception as e:
        click.echo(f"\nERROR: Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        ctx.exit(EXIT_ERROR)


@cli.command()
@click.option(
    '--instance', '-i',
    required=True,
    help='RDS instance identifier'
)
@click.option(
    '--time-range', '-t',
    default=None,
    help='Time range for metrics (e.g., "1h", "24h", "7d"). Mutually exclusive with --start-time/--end-time'
)
@click.option(
    '--start-time',
    default=None,
    help='Start time (e.g., "2026-03-02T10:00:00", "2026-03-02 10:00", "2026-03-02"). Requires --end-time'
)
@click.option(
    '--end-time',
    default=None,
    help='End time (e.g., "2026-03-02T14:00:00", "2026-03-02 14:00", "2026-03-02"). Requires --start-time'
)
@click.pass_context
def diagnose(ctx, instance, time_range, start_time, end_time):
    """
    Run diagnostics on a specific RDS instance.
    
    Collects CloudWatch metrics and Performance Insights data (if enabled),
    analyzes the data, and displays a diagnostic summary.
    
    Examples:
    
      # Run diagnostics with default 1-hour time range
      rds-diag diagnose --instance my-db-instance
      
      # Run diagnostics for the last 24 hours
      rds-diag --profile lt-prd diagnose --instance my-db --time-range 24h
      
      # Run diagnostics for the last 7 days with verbose output
      rds-diag --verbose diagnose -i my-db -t 7d
      
      # Run diagnostics for specific time range
      rds-diag diagnose --instance my-db --start-time "2026-03-02 09:00" --end-time "2026-03-02 17:00"
      
      # Run diagnostics for specific date (full day)
      rds-diag diagnose --instance my-db --start-time "2026-03-01" --end-time "2026-03-02"
    """
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    # Validate instance ID format
    is_valid, error_msg = validate_instance_id(instance)
    if not is_valid:
        click.echo(f"\nERROR: Invalid instance ID format: {error_msg}", err=True)
        click.echo(
            "\nInstance IDs must start with a letter, contain only alphanumeric "
            "characters and hyphens, and be 1-63 characters long.",
            err=True
        )
        ctx.exit(EXIT_ERROR)
    
    # Validate time range options
    if (start_time or end_time) and time_range:
        click.echo(
            "\nERROR: Cannot use both --time-range and --start-time/--end-time options together.",
            err=True
        )
        click.echo("Use either --time-range OR --start-time with --end-time.", err=True)
        ctx.exit(EXIT_ERROR)
    
    if (start_time and not end_time) or (end_time and not start_time):
        click.echo(
            "\nERROR: Both --start-time and --end-time must be specified together.",
            err=True
        )
        ctx.exit(EXIT_ERROR)
    
    # Default to 1h if no time options specified
    if not time_range and not start_time and not end_time:
        time_range = '1h'
    
    if verbose:
        click.echo(f"Running diagnostics for instance: {instance}")
        if time_range:
            click.echo(f"Time range: {time_range}")
        else:
            click.echo(f"Start time: {start_time}")
            click.echo(f"End time: {end_time}")
        click.echo(f"Region: {config.default_region}")
        if config.aws_profile:
            click.echo(f"AWS profile: {config.aws_profile}")
    
    try:
        # Parse time range
        try:
            if time_range:
                time_range_obj = TimeRange.from_duration(time_range)
            else:
                time_range_obj = TimeRange.from_timestamps(start_time, end_time)
        except ValueError as e:
            click.echo(f"\nERROR: {e}", err=True)
            if time_range:
                click.echo(
                    "\nSupported formats: <number><m|h|d> (e.g., '15m', '1h', '24h', '7d')",
                    err=True
                )
            else:
                click.echo(
                    "\nSupported formats: '2026-03-02T10:00:00', '2026-03-02 10:00', or '2026-03-02'",
                    err=True
                )
            ctx.exit(EXIT_ERROR)
        
        # Initialize application
        if verbose:
            click.echo("\nInitializing AWS clients...")
        
        app = RDSDiagnosticsApp(config)
        
        # Run diagnostics
        if verbose:
            click.echo("Collecting diagnostic data...")
        
        diagnostic_data = app.run_diagnostics(instance, time_range_obj)
        
        # Display summary
        click.echo(f"\n{'='*80}")
        click.echo(f"Diagnostic Summary for {instance}")
        click.echo(f"{'='*80}\n")
        
        # Instance information
        info = diagnostic_data.instance_info
        click.echo(f"Instance Details:")
        click.echo(f"  Engine: {info.engine} {info.engine_version}")
        click.echo(f"  Instance Class: {info.instance_class}")
        click.echo(f"  Status: {info.status}")
        
        # Display storage appropriately for Aurora vs standard RDS
        if 'aurora' in info.engine.lower():
            click.echo(f"  Storage: {info.storage_type} (Auto-scaling cluster storage)")
        else:
            click.echo(f"  Storage: {info.storage_type} ({info.allocated_storage} GB)")
        
        click.echo(f"  Availability Zone: {info.availability_zone}")
        
        # Overall severity
        analysis = diagnostic_data.analysis
        click.echo(f"\nOverall Status: {analysis.overall_severity.value.upper()}")
        
        # Violations
        if analysis.violations:
            click.echo(f"\nThreshold Violations ({len(analysis.violations)}):")
            for violation in analysis.violations:
                severity_marker = "⚠️ " if violation.severity.value == "warning" else "🔴"
                click.echo(
                    f"  {severity_marker} {violation.metric_name}: "
                    f"{violation.current_value:.2f} (threshold: {violation.threshold_value:.2f})"
                )
        else:
            click.echo("\n✓ No threshold violations detected")
        
        # Recommendations
        if diagnostic_data.recommendations:
            click.echo(f"\nRecommendations ({len(diagnostic_data.recommendations)}):")
            for i, rec in enumerate(diagnostic_data.recommendations, 1):
                click.echo(f"  {i}. {rec}")
        
        # Performance Insights status
        if diagnostic_data.performance_insights_queries:
            click.echo(
                f"\n✓ Performance Insights enabled "
                f"({len(diagnostic_data.performance_insights_queries)} queries analyzed)"
            )
        else:
            click.echo("\nℹ️  Performance Insights not enabled or no query data available")
        
        click.echo(f"\n{'='*80}")
        click.echo(
            f"\nFor detailed report, use: "
            f"rds-diag report --instance {instance} --time-range {time_range}"
        )
        
    except AWSClientError as e:
        handle_aws_error(e, config, instance, ctx)
    except Exception as e:
        click.echo(f"\nERROR: Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        ctx.exit(EXIT_ERROR)



@cli.command()
@click.option(
    '--instance', '-i',
    required=True,
    help='RDS instance identifier'
)
@click.option(
    '--time-range', '-t',
    default=None,
    help='Time range for metrics (e.g., "1h", "24h", "7d"). Mutually exclusive with --start-time/--end-time'
)
@click.option(
    '--start-time',
    default=None,
    help='Start time (e.g., "2026-03-02T10:00:00", "2026-03-02 10:00", "2026-03-02"). Requires --end-time'
)
@click.option(
    '--end-time',
    default=None,
    help='End time (e.g., "2026-03-02T14:00:00", "2026-03-02 14:00", "2026-03-02"). Requires --start-time'
)
@click.option(
    '--report-type',
    type=click.Choice(['technical', 'management'], case_sensitive=False),
    default='technical',
    help='Type of report to generate. Default: technical'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['text', 'json'], case_sensitive=False),
    default='text',
    help='Output format. Default: text'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    default=None,
    help='Output file path (default: display to stdout)'
)
@click.option(
    '--force',
    is_flag=True,
    help='Overwrite output file without confirmation'
)
@click.pass_context
def report(ctx, instance, time_range, start_time, end_time, report_type, format, output, force):
    """
    Generate a formatted report for an RDS instance.
    
    Supports both technical reports (detailed metrics and queries) and
    management reports (executive summary with recommendations).
    
    Examples:
    
      # Generate technical report to stdout
      rds-diag report --instance my-db-instance
      
      # Generate management report in JSON format
      rds-diag report -i my-db --report-type management --format json
      
      # Save technical report to file
      rds-diag report -i my-db -t 24h -o report.txt
      
      # Generate management report for 7 days and save as JSON
      rds-diag report -i my-db -t 7d --report-type management -f json -o report.json
      
      # Generate report for specific time range
      rds-diag report -i my-db --start-time "2026-03-02 09:00" --end-time "2026-03-02 17:00" -o report.txt
      
      # Generate report for specific date (full day)
      rds-diag report -i my-db --start-time "2026-03-01" --end-time "2026-03-02" -o daily-report.txt
    """
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    # Validate instance ID format
    is_valid, error_msg = validate_instance_id(instance)
    if not is_valid:
        click.echo(f"\nERROR: Invalid instance ID format: {error_msg}", err=True)
        click.echo(
            "\nInstance IDs must start with a letter, contain only alphanumeric "
            "characters and hyphens, and be 1-63 characters long.",
            err=True
        )
        ctx.exit(EXIT_ERROR)
    
    # Validate time range options
    if (start_time or end_time) and time_range:
        click.echo(
            "\nERROR: Cannot use both --time-range and --start-time/--end-time options together.",
            err=True
        )
        click.echo("Use either --time-range OR --start-time with --end-time.", err=True)
        ctx.exit(EXIT_ERROR)
    
    if (start_time and not end_time) or (end_time and not start_time):
        click.echo(
            "\nERROR: Both --start-time and --end-time must be specified together.",
            err=True
        )
        ctx.exit(EXIT_ERROR)
    
    # Default to 1h if no time options specified
    if not time_range and not start_time and not end_time:
        time_range = '1h'
    
    if verbose:
        click.echo(f"Generating {report_type} report for instance: {instance}")
        if time_range:
            click.echo(f"Time range: {time_range}")
        else:
            click.echo(f"Start time: {start_time}")
            click.echo(f"End time: {end_time}")
        click.echo(f"Output format: {format}")
        if output:
            click.echo(f"Output file: {output}")
    
    try:
        # Parse time range
        try:
            if time_range:
                time_range_obj = TimeRange.from_duration(time_range)
            else:
                time_range_obj = TimeRange.from_timestamps(start_time, end_time)
        except ValueError as e:
            click.echo(f"\nERROR: {e}", err=True)
            if time_range:
                click.echo(
                    "\nSupported formats: <number><m|h|d> (e.g., '15m', '1h', '24h', '7d')",
                    err=True
                )
            else:
                click.echo(
                    "\nSupported formats: '2026-03-02T10:00:00', '2026-03-02 10:00', or '2026-03-02'",
                    err=True
                )
            ctx.exit(EXIT_ERROR)
        
        # Parse report type and format
        report_type_enum = ReportType.TECHNICAL if report_type.lower() == 'technical' else ReportType.MANAGEMENT
        format_enum = OutputFormat.TEXT if format.lower() == 'text' else OutputFormat.JSON
        
        # Check if output file exists and prompt for confirmation
        if output and not force:
            output_path = Path(output)
            if output_path.exists():
                if not click.confirm(
                    f"\nFile '{output}' already exists. Overwrite?",
                    default=False
                ):
                    click.echo("Operation cancelled.")
                    ctx.exit(EXIT_USER_CANCELLED)
        
        # Initialize application
        if verbose:
            click.echo("\nInitializing AWS clients...")
        
        app = RDSDiagnosticsApp(config)
        
        # Run diagnostics and generate report
        if verbose:
            click.echo("Collecting diagnostic data...")
        
        generated_report = app.run_full_diagnostic_with_report(
            instance_id=instance,
            report_type=report_type_enum,
            time_range=time_range_obj,
            output_format=format_enum
        )
        
        if verbose:
            click.echo("Report generated successfully")
        
        # Output report
        if output:
            # Create parent directories if needed
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file with secure permissions and UTF-8 encoding
            try:
                # Create file with owner-only permissions (0o600)
                output_path.touch(mode=0o600, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(generated_report.content)
                click.echo(f"\n✓ Report saved to: {output}")
            except IOError as e:
                click.echo(f"\nERROR: Failed to write output file: {e}", err=True)
                click.echo(
                    "\nSuggestion: Check file permissions and disk space.",
                    err=True
                )
                ctx.exit(EXIT_ERROR)
        else:
            # Display to stdout
            click.echo(generated_report.content)
        
    except AWSClientError as e:
        handle_aws_error(e, config, instance, ctx)
    except Exception as e:
        click.echo(f"\nERROR: Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        ctx.exit(EXIT_ERROR)



@cli.command()
@click.pass_context
def check_permissions(ctx):
    """
    Check IAM permissions for RDS diagnostics operations.
    
    Validates that the configured AWS profile has the required permissions
    to run diagnostics and generate reports.
    
    Examples:
    
      # Check permissions for default profile
      rds-diag check-permissions
      
      # Check permissions for specific profile
      rds-diag --profile lt-prd check-permissions
    """
    from aws.permissions import PermissionValidator
    import json
    
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    click.echo("Checking IAM permissions...\n")
    
    if verbose:
        click.echo(f"Profile: {config.aws_profile or 'default'}")
        click.echo(f"Region: {config.default_region}\n")
    
    try:
        validator = PermissionValidator(
            profile=config.aws_profile,
            region=config.default_region
        )
        
        results = validator.validate_all_permissions()
        
        # Display results
        click.echo("Permission Check Results:")
        click.echo("=" * 80)
        
        for check in results['checks']:
            service = check['service']
            required = "REQUIRED" if check['required'] else "OPTIONAL"
            status = "✓ PASS" if check['has_permission'] else "✗ FAIL"
            
            click.echo(f"\n{service} ({required}): {status}")
            
            if not check['has_permission'] and check['missing']:
                click.echo("  Missing permissions:")
                for perm in check['missing']:
                    click.echo(f"    - {perm}")
        
        click.echo("\n" + "=" * 80)
        
        # Summary
        if results['has_required_permissions']:
            click.echo("\n✓ All required permissions are present")
            click.echo("  You can run diagnostics and generate reports")
            
            if results['missing_optional']:
                click.echo("\n⚠️  Some optional permissions are missing:")
                for perm in results['missing_optional']:
                    click.echo(f"    - {perm}")
                click.echo("\n  Performance Insights data will not be available")
        else:
            click.echo("\n✗ Missing required permissions")
            click.echo("  The following permissions are required:")
            for perm in results['missing_required']:
                click.echo(f"    - {perm}")
            
            click.echo("\n  To fix this, attach the following IAM policy to your user/role:")
            click.echo("\n" + json.dumps(validator.get_required_permissions_policy(), indent=2))
            
            ctx.exit(EXIT_ERROR)
        
        if verbose:
            click.echo("\nDetailed Results:")
            click.echo(json.dumps(results, indent=2))
    
    except Exception as e:
        click.echo(f"\n✗ ERROR: Failed to check permissions: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        ctx.exit(EXIT_ERROR)
