"""Report formatters for technical and management audiences."""

import json
import logging
from datetime import datetime
from typing import Optional, List

from core.models import (
    DiagnosticData, Severity, Trend, SQLQuery, Violation,
    MetricAnalysis
)

logger = logging.getLogger(__name__)


class TechnicalReportFormatter:
    """Formats diagnostic data for technical audiences."""
    
    @staticmethod
    def format(diagnostic_data: DiagnosticData) -> str:
        """
        Format diagnostic data as a detailed technical report.
        
        Args:
            diagnostic_data: Complete diagnostic data
            
        Returns:
            Formatted text report
        """
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("RDS DIAGNOSTICS REPORT - TECHNICAL")
        lines.append("=" * 80)
        lines.append(f"Generated: {diagnostic_data.collection_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")
        
        # Instance Information
        lines.append("INSTANCE INFORMATION")
        lines.append("-" * 80)
        inst = diagnostic_data.instance_info
        lines.append(f"Instance ID:       {inst.instance_id}")
        lines.append(f"Resource ID:       {inst.resource_id}")
        lines.append(f"Engine:            {inst.engine} {inst.engine_version}")
        lines.append(f"Instance Class:    {inst.instance_class}")
        lines.append(f"Status:            {inst.status}")
        lines.append(f"Storage Type:      {inst.storage_type}")
        
        # Handle Aurora vs standard RDS storage display
        if 'aurora' in inst.engine.lower():
            lines.append(f"Allocated Storage: Auto-scaling (cluster-level)")
            if inst.max_connections > 0:
                lines.append(f"Max Connections:   {inst.max_connections}")
            else:
                lines.append(f"Max Connections:   Dynamic (formula-based)")
        else:
            lines.append(f"Allocated Storage: {inst.allocated_storage} GB")
            if inst.max_connections > 0:
                lines.append(f"Max Connections:   {inst.max_connections}")
            else:
                lines.append(f"Max Connections:   Not available")
        
        lines.append(f"Availability Zone: {inst.availability_zone}")
        lines.append("")
        
        # Analysis Summary
        lines.append("ANALYSIS SUMMARY")
        lines.append("-" * 80)
        analysis = diagnostic_data.analysis
        lines.append(f"Overall Severity: {analysis.overall_severity.value.upper()}")
        lines.append(f"Summary: {analysis.summary}")
        lines.append("")
        
        # Threshold Violations
        if analysis.violations:
            lines.append("THRESHOLD VIOLATIONS")
            lines.append("-" * 80)
            for violation in analysis.violations:
                severity_marker = "🔴" if violation.severity == Severity.CRITICAL else "⚠️"
                lines.append(f"{severity_marker} {violation.severity.value.upper()}: {violation.message}")
                lines.append(f"   Metric: {violation.metric_name}")
                lines.append(f"   Current: {violation.current_value:.2f}")
                lines.append(f"   Threshold: {violation.threshold_value:.2f}")
                lines.append(f"   Time: {violation.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append("")
        else:
            lines.append("THRESHOLD VIOLATIONS")
            lines.append("-" * 80)
            lines.append("✓ No threshold violations detected")
            lines.append("")
        
        # CloudWatch Metrics
        lines.append("CLOUDWATCH METRICS")
        lines.append("-" * 80)
        metrics = diagnostic_data.cloudwatch_metrics
        
        # CPU
        cpu = metrics.cpu_utilization
        lines.append(f"CPU Utilization:")
        if cpu.data_points:
            lines.append(f"  Average: {cpu.get_average():.2f}%")
            lines.append(f"  Maximum: {cpu.get_max():.2f}%")
            lines.append(f"  Minimum: {cpu.get_min():.2f}%")
            latest = cpu.get_latest()
            if latest:
                lines.append(f"  Latest:  {latest.value:.2f}% at {latest.timestamp.strftime('%H:%M:%S')}")
        else:
            lines.append("  No data available")
        lines.append("")
        
        # Memory
        memory = metrics.freeable_memory
        lines.append(f"Freeable Memory:")
        if memory.data_points:
            lines.append(f"  Average: {memory.get_average() / (1024**3):.2f} GB")
            lines.append(f"  Maximum: {memory.get_max() / (1024**3):.2f} GB")
            lines.append(f"  Minimum: {memory.get_min() / (1024**3):.2f} GB")
            latest = memory.get_latest()
            if latest:
                lines.append(f"  Latest:  {latest.value / (1024**3):.2f} GB at {latest.timestamp.strftime('%H:%M:%S')}")
        else:
            lines.append("  No data available")
        lines.append("")
        
        # Connections
        conn = metrics.database_connections
        lines.append(f"Database Connections:")
        if conn.data_points:
            lines.append(f"  Average: {conn.get_average():.0f}")
            lines.append(f"  Maximum: {conn.get_max():.0f}")
            lines.append(f"  Minimum: {conn.get_min():.0f}")
            latest = conn.get_latest()
            if latest:
                pct = (latest.value / inst.max_connections) * 100 if inst.max_connections > 0 else 0
                lines.append(f"  Latest:  {latest.value:.0f} ({pct:.1f}% of max) at {latest.timestamp.strftime('%H:%M:%S')}")
        else:
            lines.append("  No data available")
        lines.append("")
        
        # IOPS
        iops = metrics.iops
        lines.append(f"IOPS:")
        if iops.read_iops.data_points:
            lines.append(f"  Read IOPS Average:  {iops.read_iops.get_average():.2f}")
            lines.append(f"  Write IOPS Average: {iops.write_iops.get_average():.2f}")
            total = iops.get_total_iops_series()
            if total.data_points:
                lines.append(f"  Total IOPS Average: {total.get_average():.2f}")
        else:
            lines.append("  No data available")
        lines.append("")
        
        # Storage
        storage = metrics.storage
        lines.append(f"Storage:")
        
        # Handle Aurora vs standard RDS storage
        if 'aurora' in inst.engine.lower():
            lines.append(f"  Type: Auto-scaling cluster storage")
            if storage.free_storage.data_points:
                latest_free = storage.free_storage.get_latest()
                latest_used = storage.used_storage.get_latest()
                if latest_free and latest_used:
                    total_gb = (latest_free.value + latest_used.value) / (1024**3)
                    used_gb = latest_used.value / (1024**3)
                    free_gb = latest_free.value / (1024**3)
                    usage_pct = (used_gb / total_gb * 100) if total_gb > 0 else 0
                    lines.append(f"  Current Total: {total_gb:.2f} GB")
                    lines.append(f"  Used: {used_gb:.2f} GB ({usage_pct:.1f}%)")
                    lines.append(f"  Free: {free_gb:.2f} GB")
            else:
                lines.append(f"  No storage metrics available")
        else:
            usage_pct = storage.get_usage_percentage()
            lines.append(f"  Total Allocated: {storage.total_storage / (1024**3):.2f} GB")
            lines.append(f"  Usage: {usage_pct:.1f}%")
            if storage.free_storage.data_points:
                latest_free = storage.free_storage.get_latest()
                if latest_free:
                    lines.append(f"  Free: {latest_free.value / (1024**3):.2f} GB")
        lines.append("")
        
        # Trends
        if analysis.trends:
            lines.append("METRIC TRENDS")
            lines.append("-" * 80)
            for trend in analysis.trends:
                trend_icon = "📈" if trend.trend == Trend.DEGRADING else "📉" if trend.trend == Trend.IMPROVING else "➡️"
                lines.append(f"{trend_icon} {trend.description}")
            lines.append("")
        
        # Performance Insights
        if diagnostic_data.performance_insights_queries:
            lines.append("TOP SQL QUERIES (Performance Insights)")
            lines.append("-" * 80)
            lines.append("Note: Values represent database load (Average Active Sessions)")
            lines.append("")
            for i, query in enumerate(diagnostic_data.performance_insights_queries[:10], 1):
                lines.append(f"{i}. Query ID: {query.query_id}")
                lines.append(f"   Total Load: {query.total_execution_time:.2f} AAS")
                lines.append(f"   Average Load: {query.average_execution_time:.4f} AAS")
                lines.append(f"   Time Samples: {query.execution_count}")
                if query.wait_events:
                    lines.append(f"   Wait Events: {', '.join(query.wait_events)}")
                # Truncate long queries
                query_text = query.query_text[:200] + "..." if len(query.query_text) > 200 else query.query_text
                lines.append(f"   SQL: {query_text}")
                lines.append("")
        else:
            lines.append("TOP SQL QUERIES (Performance Insights)")
            lines.append("-" * 80)
            lines.append("Performance Insights data not available")
            lines.append("")
        
        # Wait Events
        if diagnostic_data.wait_events:
            lines.append("WAIT EVENTS")
            lines.append("-" * 80)
            for event in diagnostic_data.wait_events[:10]:
                lines.append(f"• {event.event_name}")
                lines.append(f"  Total Wait Time: {event.total_wait_time:.2f}s")
                lines.append(f"  Wait Count: {event.wait_count}")
                lines.append("")
        
        # Top Databases
        if diagnostic_data.top_databases:
            lines.append("TOP DATABASES BY LOAD")
            lines.append("-" * 80)
            for i, db in enumerate(diagnostic_data.top_databases[:10], 1):
                lines.append(f"{i}. {db.database_name}")
                lines.append(f"   Total Load: {db.total_load:.2f} AAS")
                lines.append(f"   Load %: {db.load_percentage:.1f}%")
                lines.append("")
        
        # Top Users
        if diagnostic_data.top_users:
            lines.append("TOP USERS BY LOAD")
            lines.append("-" * 80)
            for i, user in enumerate(diagnostic_data.top_users[:10], 1):
                lines.append(f"{i}. {user.user_name}")
                lines.append(f"   Total Load: {user.total_load:.2f} AAS")
                lines.append(f"   Load %: {user.load_percentage:.1f}%")
                lines.append("")
        
        # Recommendations
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 80)
        for i, rec in enumerate(diagnostic_data.recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")
        
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_json(diagnostic_data: DiagnosticData) -> str:
        """
        Format diagnostic data as JSON.
        
        Args:
            diagnostic_data: Complete diagnostic data
            
        Returns:
            JSON string
        """
        data = {
            "generated_at": diagnostic_data.collection_timestamp.isoformat(),
            "instance": {
                "instance_id": diagnostic_data.instance_info.instance_id,
                "resource_id": diagnostic_data.instance_info.resource_id,
                "engine": diagnostic_data.instance_info.engine,
                "engine_version": diagnostic_data.instance_info.engine_version,
                "instance_class": diagnostic_data.instance_info.instance_class,
                "status": diagnostic_data.instance_info.status,
                "storage_type": diagnostic_data.instance_info.storage_type,
                "allocated_storage_gb": diagnostic_data.instance_info.allocated_storage,
                "max_connections": diagnostic_data.instance_info.max_connections,
                "availability_zone": diagnostic_data.instance_info.availability_zone
            },
            "analysis": {
                "overall_severity": diagnostic_data.analysis.overall_severity.value,
                "summary": diagnostic_data.analysis.summary,
                "violations": [
                    {
                        "metric_name": v.metric_name,
                        "severity": v.severity.value,
                        "current_value": v.current_value,
                        "threshold_value": v.threshold_value,
                        "timestamp": v.timestamp.isoformat(),
                        "message": v.message
                    }
                    for v in diagnostic_data.analysis.violations
                ],
                "trends": [
                    {
                        "metric_name": t.metric_name,
                        "trend": t.trend.value,
                        "change_percentage": t.change_percentage,
                        "description": t.description
                    }
                    for t in diagnostic_data.analysis.trends
                ]
            },
            "metrics": {
                "cpu_utilization": {
                    "average": diagnostic_data.cloudwatch_metrics.cpu_utilization.get_average(),
                    "max": diagnostic_data.cloudwatch_metrics.cpu_utilization.get_max(),
                    "min": diagnostic_data.cloudwatch_metrics.cpu_utilization.get_min(),
                    "unit": "Percent"
                },
                "freeable_memory_gb": {
                    "average": diagnostic_data.cloudwatch_metrics.freeable_memory.get_average() / (1024**3),
                    "max": diagnostic_data.cloudwatch_metrics.freeable_memory.get_max() / (1024**3),
                    "min": diagnostic_data.cloudwatch_metrics.freeable_memory.get_min() / (1024**3),
                    "unit": "GB"
                },
                "database_connections": {
                    "average": diagnostic_data.cloudwatch_metrics.database_connections.get_average(),
                    "max": diagnostic_data.cloudwatch_metrics.database_connections.get_max(),
                    "min": diagnostic_data.cloudwatch_metrics.database_connections.get_min(),
                    "unit": "Count"
                },
                "storage_usage_percent": diagnostic_data.cloudwatch_metrics.storage.get_usage_percentage()
            },
            "performance_insights": {
                "available": diagnostic_data.performance_insights_queries is not None,
                "note": "Load values represent Average Active Sessions (AAS), not execution time",
                "top_queries": [
                    {
                        "query_id": q.query_id,
                        "total_load_aas": q.total_execution_time,
                        "average_load_aas": q.average_execution_time,
                        "time_samples": q.execution_count,
                        "query_text": q.query_text,
                        "wait_events": q.wait_events
                    }
                    for q in (diagnostic_data.performance_insights_queries or [])
                ],
                "top_databases": [
                    {
                        "database_name": db.database_name,
                        "total_load_aas": db.total_load,
                        "load_percentage": db.load_percentage
                    }
                    for db in (diagnostic_data.top_databases or [])
                ],
                "top_users": [
                    {
                        "user_name": u.user_name,
                        "total_load_aas": u.total_load,
                        "load_percentage": u.load_percentage
                    }
                    for u in (diagnostic_data.top_users or [])
                ]
            },
            "recommendations": diagnostic_data.recommendations
        }
        
        return json.dumps(data, indent=2)


class ManagementReportFormatter:
    """Formats diagnostic data for management audiences."""
    
    @staticmethod
    def format(diagnostic_data: DiagnosticData) -> str:
        """
        Format diagnostic data as a concise management report.
        
        Args:
            diagnostic_data: Complete diagnostic data
            
        Returns:
            Formatted text report
        """
        lines = []
        
        # Header
        lines.append("=" * 70)
        lines.append("RDS DIAGNOSTICS REPORT - EXECUTIVE SUMMARY")
        lines.append("=" * 70)
        lines.append(f"Report Date: {diagnostic_data.collection_timestamp.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Instance: {diagnostic_data.instance_info.instance_id}")
        lines.append("")
        
        # Executive Summary
        summary = ManagementReportFormatter.create_executive_summary(
            diagnostic_data.analysis
        )
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 70)
        lines.append(summary)
        lines.append("")
        
        # Severity Assessment
        lines.append("SEVERITY ASSESSMENT")
        lines.append("-" * 70)
        severity = diagnostic_data.analysis.overall_severity
        if severity == Severity.CRITICAL:
            lines.append("Status: 🔴 CRITICAL - Immediate Action Required")
        elif severity == Severity.WARNING:
            lines.append("Status: ⚠️  WARNING - Attention Needed")
        else:
            lines.append("Status: ✓ NORMAL - No Issues Detected")
        lines.append("")
        
        # Key Findings
        if diagnostic_data.analysis.violations:
            findings = ManagementReportFormatter.format_key_findings(
                diagnostic_data.analysis.violations
            )
            lines.append("KEY FINDINGS")
            lines.append("-" * 70)
            lines.append(findings)
            lines.append("")
        
        # Performance Metrics (as percentages/trends)
        lines.append("PERFORMANCE METRICS")
        lines.append("-" * 70)
        metrics = diagnostic_data.cloudwatch_metrics
        
        cpu_avg = metrics.cpu_utilization.get_average()
        lines.append(f"CPU Utilization:     {cpu_avg:.1f}%")
        
        conn_latest = metrics.database_connections.get_latest()
        if conn_latest:
            conn_pct = (conn_latest.value / diagnostic_data.instance_info.max_connections) * 100
            lines.append(f"Connection Usage:    {conn_pct:.1f}%")
        
        storage_pct = metrics.storage.get_usage_percentage()
        lines.append(f"Storage Usage:       {storage_pct:.1f}%")
        
        # Add trend indicators
        for trend in diagnostic_data.analysis.trends:
            if abs(trend.change_percentage) > 10:  # Only show significant trends
                trend_icon = "↑" if trend.trend == Trend.DEGRADING else "↓" if trend.trend == Trend.IMPROVING else "→"
                lines.append(f"  {trend.metric_name}: {trend_icon} {abs(trend.change_percentage):.0f}%")
        lines.append("")
        
        # Recommendations
        rec_text = ManagementReportFormatter.format_recommendations(
            diagnostic_data.recommendations
        )
        lines.append("RECOMMENDED ACTIONS")
        lines.append("-" * 70)
        lines.append(rec_text)
        lines.append("")
        
        lines.append("=" * 70)
        lines.append("For detailed technical analysis, request a technical report.")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    @staticmethod
    def create_executive_summary(analysis: MetricAnalysis) -> str:
        """
        Create executive summary from analysis.
        
        Args:
            analysis: Metric analysis results
            
        Returns:
            Executive summary text
        """
        if analysis.overall_severity == Severity.CRITICAL:
            summary = (
                f"The RDS instance is experiencing critical performance issues. "
                f"{len(analysis.violations)} metrics have exceeded critical thresholds "
                f"and require immediate attention to prevent service degradation."
            )
        elif analysis.overall_severity == Severity.WARNING:
            summary = (
                f"The RDS instance shows warning signs that should be monitored. "
                f"{len(analysis.violations)} metrics are approaching threshold limits. "
                f"Proactive action is recommended to prevent future issues."
            )
        else:
            summary = (
                "The RDS instance is operating within normal parameters. "
                "All monitored metrics are within acceptable thresholds. "
                "Continue regular monitoring."
            )
        
        # Add trend information
        degrading = [t for t in analysis.trends if t.trend == Trend.DEGRADING]
        if degrading:
            summary += f" Note: {len(degrading)} metrics show increasing trends that warrant attention."
        
        return summary
    
    @staticmethod
    def format_key_findings(violations: List[Violation]) -> str:
        """
        Format key findings from violations.
        
        Args:
            violations: List of violations
            
        Returns:
            Formatted findings text
        """
        lines = []
        
        critical = [v for v in violations if v.severity == Severity.CRITICAL]
        warnings = [v for v in violations if v.severity == Severity.WARNING]
        
        if critical:
            lines.append(f"Critical Issues ({len(critical)}):")
            for v in critical:
                lines.append(f"  • {v.message}")
        
        if warnings:
            if critical:
                lines.append("")
            lines.append(f"Warnings ({len(warnings)}):")
            for v in warnings:
                lines.append(f"  • {v.message}")
        
        return "\n".join(lines) if lines else "No issues detected."
    
    @staticmethod
    def format_recommendations(recommendations: List[str]) -> str:
        """
        Format recommendations for management.
        
        Args:
            recommendations: List of recommendation strings
            
        Returns:
            Formatted recommendations text
        """
        if not recommendations:
            return "No specific actions required at this time."
        
        # Prioritize critical recommendations
        critical_recs = [r for r in recommendations if "CRITICAL" in r]
        other_recs = [r for r in recommendations if "CRITICAL" not in r]
        
        lines = []
        
        if critical_recs:
            lines.append("Immediate Actions:")
            for i, rec in enumerate(critical_recs, 1):
                lines.append(f"  {i}. {rec}")
        
        if other_recs:
            if critical_recs:
                lines.append("")
            lines.append("Additional Recommendations:")
            for i, rec in enumerate(other_recs, 1):
                lines.append(f"  {i}. {rec}")
        
        return "\n".join(lines)
