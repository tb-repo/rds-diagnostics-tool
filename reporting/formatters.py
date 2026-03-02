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
                severity_marker = "[!]" if violation.severity == Severity.CRITICAL else "[*]"
                lines.append(f"{severity_marker} {violation.severity.value.upper()}: {violation.message}")
                lines.append(f"   Metric: {violation.metric_name}")
                lines.append(f"   Current: {violation.current_value:.2f}")
                lines.append(f"   Threshold: {violation.threshold_value:.2f}")
                lines.append(f"   Time: {violation.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append("")
        else:
            lines.append("THRESHOLD VIOLATIONS")
            lines.append("-" * 80)
            lines.append("[OK] No threshold violations detected")
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
                trend_icon = "[^]" if trend.trend == Trend.DEGRADING else "[v]" if trend.trend == Trend.IMPROVING else "[-]"
                lines.append(f"{trend_icon} {trend.description}")
            lines.append("")
        
        # Performance Insights - Enhanced SQL Metrics
        if diagnostic_data.performance_insights_queries:
            lines.append("TOP SQL QUERIES (Performance Insights)")
            lines.append("-" * 80)
            lines.append("Note: Queries sorted by total execution time (highest impact first)")
            lines.append("")
            
            # Sort queries by total execution time (descending)
            sorted_queries = sorted(
                diagnostic_data.performance_insights_queries[:10],
                key=lambda q: q.total_execution_time,
                reverse=True
            )
            
            for i, query in enumerate(sorted_queries, 1):
                lines.append(f"{'=' * 80}")
                lines.append(f"Query #{i}: {query.query_id}")
                lines.append(f"{'=' * 80}")
                
                # SQL Text (with proper formatting for long queries)
                lines.append("SQL Text:")
                if len(query.query_text) > 500:
                    # Show first 500 chars with continuation indicator
                    lines.append(f"  {query.query_text[:500]}")
                    lines.append(f"  ... (truncated, {len(query.query_text)} total characters)")
                else:
                    # Show full query, handle multi-line
                    for line in query.query_text.split('\n'):
                        lines.append(f"  {line}")
                lines.append("")
                
                # Engine Type
                if query.engine_type:
                    lines.append(f"Engine: {query.engine_type}")
                    lines.append("")
                
                # Execution Metrics
                lines.append("Execution Metrics:")
                lines.append(f"  Total Load:             {query.total_execution_time:.2f} AAS (Average Active Sessions)")
                lines.append(f"  Average Load:           {query.average_execution_time:.2f} AAS per time bucket")
                lines.append(f"  Time Buckets:           {query.execution_count} (5-minute intervals)")
                
                if query.executions_per_second is not None:
                    lines.append(f"  Executions/sec:         {query.executions_per_second:.2f} calls/sec")
                lines.append("")
                
                # Check if any per-query execution metrics are available
                has_resource_metrics = query.cpu_time is not None or query.lock_time is not None
                has_row_metrics = (query.rows_examined is not None or 
                                  query.rows_returned is not None or 
                                  query.rows_per_second is not None)
                has_io_metrics = (query.read_io_bytes is not None or 
                                 query.write_io_bytes is not None or 
                                 query.read_io_time is not None or 
                                 query.write_io_time is not None)
                
                # Only show sections if at least one metric is available
                if has_resource_metrics:
                    lines.append("Resource Metrics:")
                    if query.cpu_time is not None:
                        cpu_pct = (query.cpu_time / query.total_execution_time * 100) if query.total_execution_time > 0 else 0
                        lines.append(f"  CPU Time:               {query.cpu_time:.2f} ms ({cpu_pct:.1f}% of total)")
                    
                    if query.lock_time is not None:
                        lock_pct = (query.lock_time / query.total_execution_time * 100) if query.total_execution_time > 0 else 0
                        lines.append(f"  Lock Time:              {query.lock_time:.2f} ms ({lock_pct:.1f}% of total)")
                    lines.append("")
                
                if has_row_metrics:
                    lines.append("Row Metrics:")
                    if query.rows_examined is not None:
                        lines.append(f"  Rows Examined:          {query.rows_examined:,}")
                    
                    if query.rows_returned is not None:
                        lines.append(f"  Rows Returned:          {query.rows_returned:,}")
                    
                    # Calculate and display efficiency ratio
                    if query.rows_examined is not None and query.rows_returned is not None and query.rows_examined > 0:
                        efficiency = (query.rows_returned / query.rows_examined) * 100
                        lines.append(f"  Efficiency Ratio:       {efficiency:.2f}%")
                        if efficiency < 1.0:
                            lines.append(f"                          [!] Low efficiency - consider adding indexes")
                        elif efficiency < 10.0:
                            lines.append(f"                          [!] Poor selectivity - review query optimization")
                    
                    # Rows per second (Aurora PostgreSQL 17+)
                    if query.rows_per_second is not None:
                        lines.append(f"  Rows/sec:               {query.rows_per_second:.2f}")
                    
                    lines.append("")
                
                if has_io_metrics:
                    lines.append("I/O Metrics:")
                    if query.read_io_bytes is not None:
                        read_mb = query.read_io_bytes / (1024 * 1024)
                        lines.append(f"  Read I/O:               {read_mb:.2f} MB")
                    
                    if query.write_io_bytes is not None:
                        write_mb = query.write_io_bytes / (1024 * 1024)
                        lines.append(f"  Write I/O:              {write_mb:.2f} MB")
                    
                    # I/O Time Metrics (Aurora PostgreSQL 17+)
                    if query.read_io_time is not None:
                        read_time_sec = query.read_io_time / 1000  # Convert ms to seconds
                        lines.append(f"  Read I/O Time:          {query.read_io_time:.2f} ms ({read_time_sec:.2f} sec)")
                        if query.read_io_time > 10000:  # More than 10 seconds
                            lines.append(f"                          [!] CRITICAL: Extremely high read latency!")
                        elif query.read_io_time > 1000:  # More than 1 second
                            lines.append(f"                          [*] WARNING: High read latency")
                    
                    if query.write_io_time is not None:
                        write_time_sec = query.write_io_time / 1000  # Convert ms to seconds
                        lines.append(f"  Write I/O Time:         {query.write_io_time:.2f} ms ({write_time_sec:.2f} sec)")
                        if query.write_io_time > 10000:  # More than 10 seconds
                            lines.append(f"                          [!] CRITICAL: Extremely high write latency!")
                        elif query.write_io_time > 1000:  # More than 1 second
                            lines.append(f"                          [*] WARNING: High write latency")
                    
                    lines.append("")
                
                # Add explanatory note if no per-query execution metrics are available
                if not (has_resource_metrics or has_row_metrics or has_io_metrics):
                    lines.append("Note: Per-query execution metrics (CPU time, lock time, rows, I/O time)")
                    lines.append("      are not available from Performance Insights API for Aurora PostgreSQL.")
                    lines.append("      See 'OS-LEVEL PERFORMANCE METRICS' section below for system-wide")
                    lines.append("      CPU, memory, and disk I/O performance data.")
                    lines.append("")
                
                # Wait Events (if available)
                if query.wait_events:
                    lines.append(f"Wait Events: {', '.join(query.wait_events)}")
                    lines.append("")
                
                # Rows Affected (if available)
                if query.rows_affected is not None:
                    lines.append(f"Rows Affected: {query.rows_affected:,}")
                    lines.append("")
        else:
            lines.append("TOP SQL QUERIES (Performance Insights)")
            lines.append("-" * 80)
            lines.append("Performance Insights data not available")
            lines.append("To enable enhanced SQL metrics, ensure Performance Insights is enabled")
            lines.append("on your RDS instance.")
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
        
        # OS-Level Metrics from Performance Insights
        if diagnostic_data.os_metrics:
            lines.append("OS-LEVEL PERFORMANCE METRICS (Performance Insights)")
            lines.append("-" * 80)
            os_m = diagnostic_data.os_metrics
            
            # CPU Metrics
            lines.append("CPU:")
            if os_m.cpu_total is not None:
                lines.append(f"  Total Utilization:  {os_m.cpu_total:.1f}%")
            if os_m.cpu_user is not None:
                lines.append(f"  User Space:         {os_m.cpu_user:.1f}%")
            if os_m.cpu_system is not None:
                lines.append(f"  System/Kernel:      {os_m.cpu_system:.1f}%")
            if os_m.cpu_wait is not None:
                wait_indicator = "  [*] HIGH" if os_m.cpu_wait > 10 else ""
                lines.append(f"  I/O Wait:           {os_m.cpu_wait:.1f}%{wait_indicator}")
                if os_m.cpu_wait > 10:
                    lines.append(f"     -> Database is waiting for disk I/O")
            lines.append("")
            
            # Memory Metrics
            lines.append("Memory:")
            if os_m.memory_free_gb is not None:
                lines.append(f"  Free:               {os_m.memory_free_gb:.2f} GB")
            if os_m.memory_active_gb is not None:
                lines.append(f"  Active:             {os_m.memory_active_gb:.2f} GB")
            if os_m.memory_cached_gb is not None:
                lines.append(f"  Cached:             {os_m.memory_cached_gb:.2f} GB")
            lines.append("")
            
            # Disk I/O Metrics - THE KEY SECTION
            lines.append("Disk I/O:")
            if os_m.read_iops is not None:
                lines.append(f"  Read IOPS:          {os_m.read_iops:.1f}")
            if os_m.write_iops is not None:
                lines.append(f"  Write IOPS:         {os_m.write_iops:.1f}")
            
            # Latency - with warnings
            if os_m.read_latency_ms is not None:
                latency_indicator = "  [*] HIGH" if os_m.read_latency_ms > 10 else ""
                lines.append(f"  Read Latency:       {os_m.read_latency_ms:.2f} ms{latency_indicator}")
                if os_m.read_latency_ms > 10:
                    lines.append(f"     -> Slow disk reads detected")
            
            if os_m.write_latency_ms is not None:
                latency_indicator = "  [*] HIGH" if os_m.write_latency_ms > 10 else ""
                lines.append(f"  Write Latency:      {os_m.write_latency_ms:.2f} ms{latency_indicator}")
                if os_m.write_latency_ms > 10:
                    lines.append(f"     -> Slow disk writes detected")
            
            # Throughput
            if os_m.read_throughput_kbps is not None:
                lines.append(f"  Read Throughput:    {os_m.read_throughput_kbps:.1f} KB/s ({os_m.read_throughput_kbps/1024:.2f} MB/s)")
            if os_m.write_throughput_kbps is not None:
                lines.append(f"  Write Throughput:   {os_m.write_throughput_kbps:.1f} KB/s ({os_m.write_throughput_kbps/1024:.2f} MB/s)")
            
            # Queue depth - important indicator
            if os_m.disk_queue_depth is not None:
                queue_indicator = "  [*] I/O BOTTLENECK" if os_m.disk_queue_depth > 2 else ""
                lines.append(f"  Queue Depth:        {os_m.disk_queue_depth:.2f}{queue_indicator}")
                if os_m.disk_queue_depth > 2:
                    lines.append(f"     -> Queries are waiting for disk access")
            
            if os_m.disk_utilization_pct is not None:
                lines.append(f"  Disk Utilization:   {os_m.disk_utilization_pct:.1f}%")
            lines.append("")
            
            # Temp Usage (PostgreSQL specific)
            if os_m.temp_blocks_read is not None or os_m.temp_blocks_written is not None:
                lines.append("Temp Usage:")
                if os_m.temp_blocks_read is not None:
                    temp_indicator = "  [*] HIGH" if os_m.temp_blocks_read > 1000 else ""
                    lines.append(f"  Temp Blocks Read:   {os_m.temp_blocks_read:.0f}{temp_indicator}")
                if os_m.temp_blocks_written is not None:
                    temp_indicator = "  [*] HIGH" if os_m.temp_blocks_written > 1000 else ""
                    lines.append(f"  Temp Blocks Written: {os_m.temp_blocks_written:.0f}{temp_indicator}")
                    if os_m.temp_blocks_written > 1000:
                        lines.append(f"     -> Queries spilling to disk - consider increasing work_mem")
                lines.append("")
            
            # Swap Usage
            if os_m.swap_free_gb is not None or os_m.swap_out_rate is not None:
                lines.append("Swap:")
                if os_m.swap_free_gb is not None:
                    lines.append(f"  Free Swap:          {os_m.swap_free_gb:.2f} GB")
                if os_m.swap_in_rate is not None:
                    lines.append(f"  Swap In Rate:       {os_m.swap_in_rate:.2f} MB/s")
                if os_m.swap_out_rate is not None:
                    swap_indicator = "  [!] CRITICAL" if os_m.swap_out_rate > 0 else ""
                    lines.append(f"  Swap Out Rate:      {os_m.swap_out_rate:.2f} MB/s{swap_indicator}")
                    if os_m.swap_out_rate > 0:
                        lines.append(f"     -> System is swapping - memory pressure detected")
                lines.append("")
            
            # Load Average
            if os_m.load_avg_1min is not None or os_m.load_avg_5min is not None:
                lines.append("Load Average:")
                if os_m.load_avg_1min is not None:
                    lines.append(f"  1-minute:           {os_m.load_avg_1min:.2f}")
                if os_m.load_avg_5min is not None:
                    lines.append(f"  5-minute:           {os_m.load_avg_5min:.2f}")
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
                        "wait_events": q.wait_events,
                        "rows_affected": q.rows_affected,
                        # Enhanced metrics (optional fields)
                        "engine_type": q.engine_type,
                        "executions_per_second": q.executions_per_second,
                        "cpu_time": q.cpu_time,
                        "lock_time": q.lock_time,
                        "rows_examined": q.rows_examined,
                        "rows_returned": q.rows_returned,
                        "read_io_bytes": q.read_io_bytes,
                        "write_io_bytes": q.write_io_bytes
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
            lines.append("Status: [!] CRITICAL - Immediate Action Required")
        elif severity == Severity.WARNING:
            lines.append("Status: [*] WARNING - Attention Needed")
        else:
            lines.append("Status: [OK] NORMAL - No Issues Detected")
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
        
        # SQL Performance Summary (if Performance Insights available)
        if diagnostic_data.performance_insights_queries:
            sql_summary = ManagementReportFormatter.format_sql_performance_summary(
                diagnostic_data.performance_insights_queries,
                diagnostic_data.recommendations
            )
            lines.append("SQL PERFORMANCE SUMMARY")
            lines.append("-" * 70)
            lines.append(sql_summary)
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
    
    @staticmethod
    def format_sql_performance_summary(queries: List[SQLQuery], recommendations: List[str]) -> str:
        """
        Format SQL performance summary for management report.
        
        Args:
            queries: List of SQL queries
            recommendations: List of all recommendations
            
        Returns:
            Formatted SQL performance summary
        """
        lines = []
        
        # Count queries analyzed
        lines.append(f"Queries Analyzed: {len(queries)}")
        lines.append("")
        
        # Extract SQL-specific recommendations
        sql_recs = [r for r in recommendations if any(
            keyword in r for keyword in ['[INDEX]', '[LOCK]', '[CPU]', '[CACHE]', 'Query', 'SQL']
        )]
        
        if sql_recs:
            # Count by severity
            critical_sql = [r for r in sql_recs if 'CRITICAL' in r or '[INDEX]' in r]
            warning_sql = [r for r in sql_recs if 'WARNING' in r or '[LOCK]' in r or '[CPU]' in r]
            
            lines.append(f"SQL Issues Identified: {len(sql_recs)}")
            if critical_sql:
                lines.append(f"  • Critical: {len(critical_sql)} (require immediate attention)")
            if warning_sql:
                lines.append(f"  • Warnings: {len(warning_sql)} (should be addressed)")
            lines.append("")
            
            # Show top 3 problematic queries
            lines.append("Top Problematic Queries:")
            
            # Sort queries by total execution time (highest impact)
            sorted_queries = sorted(queries[:10], key=lambda q: q.total_execution_time, reverse=True)
            
            for i, query in enumerate(sorted_queries[:3], 1):
                lines.append(f"  {i}. Query {query.query_id}")
                lines.append(f"     Total Time: {query.total_execution_time:.2f} ms")
                
                # Add specific issues for this query
                issues = []
                
                # Check for index opportunity
                if query.rows_examined and query.rows_returned and query.rows_examined > 0:
                    efficiency = (query.rows_returned / query.rows_examined) * 100
                    if efficiency < 10:
                        issues.append(f"Low efficiency ({efficiency:.1f}%) - needs indexing")
                
                # Check for lock contention
                if query.lock_time and query.total_execution_time > 0:
                    lock_pct = (query.lock_time / query.total_execution_time) * 100
                    if lock_pct > 30:
                        issues.append(f"High lock contention ({lock_pct:.1f}%)")
                
                # Check for CPU intensity
                if query.cpu_time and query.total_execution_time > 0:
                    cpu_pct = (query.cpu_time / query.total_execution_time) * 100
                    if cpu_pct > 80:
                        issues.append(f"CPU-intensive ({cpu_pct:.1f}%)")
                
                # Check for high frequency
                if query.executions_per_second and query.executions_per_second > 10:
                    issues.append(f"Very high frequency ({query.executions_per_second:.1f} calls/sec)")
                
                if issues:
                    lines.append(f"     Issues: {'; '.join(issues)}")
                
                # Show truncated SQL
                sql_preview = query.query_text[:60].replace('\n', ' ')
                if len(query.query_text) > 60:
                    sql_preview += "..."
                lines.append(f"     SQL: {sql_preview}")
                lines.append("")
            
            # Key recommendations summary
            lines.append("Key SQL Recommendations:")
            index_count = len([r for r in sql_recs if '[INDEX]' in r])
            lock_count = len([r for r in sql_recs if '[LOCK]' in r])
            cpu_count = len([r for r in sql_recs if '[CPU]' in r])
            cache_count = len([r for r in sql_recs if '[CACHE]' in r])
            
            if index_count > 0:
                lines.append(f"  • {index_count} queries need index optimization")
            if lock_count > 0:
                lines.append(f"  • {lock_count} queries have lock contention issues")
            if cpu_count > 0:
                lines.append(f"  • {cpu_count} queries are CPU-intensive")
            if cache_count > 0:
                lines.append(f"  • {cache_count} queries are caching candidates")
        else:
            lines.append("No significant SQL performance issues detected.")
            lines.append("All queries are performing within acceptable parameters.")
        
        return "\n".join(lines)
