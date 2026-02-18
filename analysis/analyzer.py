"""Diagnostic analysis engine."""

import logging
from typing import List
from datetime import datetime

from core.config import MetricThresholds
from core.models import (
    CloudWatchMetrics, MetricAnalysis, Violation, TrendAnalysis,
    Severity, Trend, SQLQuery, MetricSeries
)

logger = logging.getLogger(__name__)


class DiagnosticAnalyzer:
    """Analyzes collected metrics to identify issues and trends."""
    
    def __init__(self, thresholds: MetricThresholds):
        """
        Initialize diagnostic analyzer.
        
        Args:
            thresholds: Metric threshold configuration
        """
        self.thresholds = thresholds
    
    def analyze_metrics(self, metrics: CloudWatchMetrics) -> MetricAnalysis:
        """
        Perform complete analysis of collected metrics.
        
        Args:
            metrics: CloudWatch metrics data
            
        Returns:
            MetricAnalysis object with violations, trends, and severity
        """
        logger.info("Analyzing metrics for violations and trends")
        
        violations = self.identify_threshold_violations(metrics)
        trends = self.calculate_trends(metrics)
        overall_severity = self.assess_overall_severity(violations)
        summary = self._generate_summary(violations, trends, overall_severity)
        
        return MetricAnalysis(
            violations=violations,
            trends=trends,
            overall_severity=overall_severity,
            summary=summary
        )
    
    def identify_threshold_violations(
        self,
        metrics: CloudWatchMetrics
    ) -> List[Violation]:
        """
        Identify metrics that exceed configured thresholds.
        
        Args:
            metrics: CloudWatch metrics data
            
        Returns:
            List of Violation objects
        """
        violations = []
        
        # Check CPU utilization
        cpu_latest = metrics.cpu_utilization.get_latest()
        if cpu_latest:
            if cpu_latest.value >= self.thresholds.cpu_critical:
                violations.append(Violation(
                    metric_name='CPUUtilization',
                    severity=Severity.CRITICAL,
                    current_value=cpu_latest.value,
                    threshold_value=self.thresholds.cpu_critical,
                    timestamp=cpu_latest.timestamp,
                    message=f"CPU utilization at {cpu_latest.value:.1f}% "
                           f"(critical threshold: {self.thresholds.cpu_critical}%)"
                ))
            elif cpu_latest.value >= self.thresholds.cpu_warning:
                violations.append(Violation(
                    metric_name='CPUUtilization',
                    severity=Severity.WARNING,
                    current_value=cpu_latest.value,
                    threshold_value=self.thresholds.cpu_warning,
                    timestamp=cpu_latest.timestamp,
                    message=f"CPU utilization at {cpu_latest.value:.1f}% "
                           f"(warning threshold: {self.thresholds.cpu_warning}%)"
                ))
        
        # Check memory utilization (freeable memory)
        memory_latest = metrics.freeable_memory.get_latest()
        if memory_latest:
            # Convert bytes to percentage (assuming we know total memory)
            # For now, we'll use a simple heuristic
            memory_gb = memory_latest.value / (1024 ** 3)
            
            # If freeable memory is very low, it's a problem
            if memory_gb < 0.5:  # Less than 500MB free
                violations.append(Violation(
                    metric_name='FreeableMemory',
                    severity=Severity.CRITICAL,
                    current_value=memory_gb,
                    threshold_value=0.5,
                    timestamp=memory_latest.timestamp,
                    message=f"Freeable memory critically low: {memory_gb:.2f} GB"
                ))
            elif memory_gb < 1.0:  # Less than 1GB free
                violations.append(Violation(
                    metric_name='FreeableMemory',
                    severity=Severity.WARNING,
                    current_value=memory_gb,
                    threshold_value=1.0,
                    timestamp=memory_latest.timestamp,
                    message=f"Freeable memory low: {memory_gb:.2f} GB"
                ))
        
        # Check database connections
        conn_latest = metrics.database_connections.get_latest()
        if conn_latest:
            max_conn = metrics.instance_info.max_connections
            conn_percentage = (conn_latest.value / max_conn) * 100 if max_conn > 0 else 0
            
            if conn_percentage >= self.thresholds.connections_critical:
                violations.append(Violation(
                    metric_name='DatabaseConnections',
                    severity=Severity.CRITICAL,
                    current_value=conn_percentage,
                    threshold_value=self.thresholds.connections_critical,
                    timestamp=conn_latest.timestamp,
                    message=f"Database connections at {conn_percentage:.1f}% of max "
                           f"({int(conn_latest.value)}/{max_conn})"
                ))
            elif conn_percentage >= self.thresholds.connections_warning:
                violations.append(Violation(
                    metric_name='DatabaseConnections',
                    severity=Severity.WARNING,
                    current_value=conn_percentage,
                    threshold_value=self.thresholds.connections_warning,
                    timestamp=conn_latest.timestamp,
                    message=f"Database connections at {conn_percentage:.1f}% of max "
                           f"({int(conn_latest.value)}/{max_conn})"
                ))
        
        # Check storage usage
        storage_usage = metrics.storage.get_usage_percentage()
        if storage_usage >= self.thresholds.storage_critical:
            violations.append(Violation(
                metric_name='StorageUsage',
                severity=Severity.CRITICAL,
                current_value=storage_usage,
                threshold_value=self.thresholds.storage_critical,
                timestamp=datetime.now(),
                message=f"Storage usage at {storage_usage:.1f}% "
                       f"(critical threshold: {self.thresholds.storage_critical}%)"
            ))
        elif storage_usage >= self.thresholds.storage_warning:
            violations.append(Violation(
                metric_name='StorageUsage',
                severity=Severity.WARNING,
                current_value=storage_usage,
                threshold_value=self.thresholds.storage_warning,
                timestamp=datetime.now(),
                message=f"Storage usage at {storage_usage:.1f}% "
                       f"(warning threshold: {self.thresholds.storage_warning}%)"
            ))
        
        logger.info(f"Identified {len(violations)} threshold violations")
        return violations
    
    def calculate_trends(self, metrics: CloudWatchMetrics) -> List[TrendAnalysis]:
        """
        Calculate trends for key metrics.
        
        Args:
            metrics: CloudWatch metrics data
            
        Returns:
            List of TrendAnalysis objects
        """
        trends = []
        
        # Analyze CPU trend
        cpu_trend = self._analyze_metric_trend(
            metrics.cpu_utilization,
            'CPUUtilization'
        )
        if cpu_trend:
            trends.append(cpu_trend)
        
        # Analyze connections trend
        conn_trend = self._analyze_metric_trend(
            metrics.database_connections,
            'DatabaseConnections'
        )
        if conn_trend:
            trends.append(conn_trend)
        
        # Analyze IOPS trend
        total_iops = metrics.iops.get_total_iops_series()
        iops_trend = self._analyze_metric_trend(total_iops, 'TotalIOPS')
        if iops_trend:
            trends.append(iops_trend)
        
        return trends
    
    def _analyze_metric_trend(
        self,
        metric_series: MetricSeries,
        metric_name: str
    ) -> TrendAnalysis:
        """
        Analyze trend for a single metric series.
        
        Args:
            metric_series: Metric data series
            metric_name: Name of the metric
            
        Returns:
            TrendAnalysis object or None if insufficient data
        """
        if len(metric_series.data_points) < 2:
            return None
        
        # Sort by timestamp
        sorted_points = sorted(
            metric_series.data_points,
            key=lambda dp: dp.timestamp
        )
        
        # Compare first half vs second half
        mid_point = len(sorted_points) // 2
        first_half_avg = sum(dp.value for dp in sorted_points[:mid_point]) / mid_point
        second_half_avg = sum(dp.value for dp in sorted_points[mid_point:]) / (len(sorted_points) - mid_point)
        
        # Calculate percentage change
        if first_half_avg == 0:
            change_pct = 0.0
        else:
            change_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        
        # Determine trend direction
        if abs(change_pct) < 5:  # Less than 5% change is stable
            trend = Trend.STABLE
            description = f"{metric_name} is stable (change: {change_pct:+.1f}%)"
        elif change_pct > 0:
            trend = Trend.DEGRADING
            description = f"{metric_name} is increasing by {change_pct:.1f}%"
        else:
            trend = Trend.IMPROVING
            description = f"{metric_name} is decreasing by {abs(change_pct):.1f}%"
        
        return TrendAnalysis(
            metric_name=metric_name,
            trend=trend,
            change_percentage=change_pct,
            description=description
        )
    
    def assess_overall_severity(self, violations: List[Violation]) -> Severity:
        """
        Assess overall severity based on violations.
        
        Args:
            violations: List of violations
            
        Returns:
            Overall Severity level
        """
        if not violations:
            return Severity.NORMAL
        
        # If any critical violations, overall is critical
        if any(v.severity == Severity.CRITICAL for v in violations):
            return Severity.CRITICAL
        
        # If any warnings, overall is warning
        if any(v.severity == Severity.WARNING for v in violations):
            return Severity.WARNING
        
        return Severity.NORMAL
    
    def generate_recommendations(
        self,
        analysis: MetricAnalysis,
        queries: List[SQLQuery]
    ) -> List[str]:
        """
        Generate actionable recommendations based on analysis.
        
        Args:
            analysis: Metric analysis results
            queries: Top SQL queries (if available)
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Recommendations based on violations
        for violation in analysis.violations:
            if violation.metric_name == 'CPUUtilization':
                if violation.severity == Severity.CRITICAL:
                    recommendations.append(
                        "CRITICAL: CPU utilization is very high. Consider scaling up "
                        "the instance class or optimizing queries."
                    )
                    if queries:
                        recommendations.append(
                            "Review top SQL queries for optimization opportunities."
                        )
                else:
                    recommendations.append(
                        "WARNING: CPU utilization is elevated. Monitor for continued growth."
                    )
            
            elif violation.metric_name == 'FreeableMemory':
                recommendations.append(
                    "Memory is low. Consider increasing instance size or optimizing "
                    "memory-intensive queries."
                )
            
            elif violation.metric_name == 'DatabaseConnections':
                recommendations.append(
                    "Connection count is high. Review connection pooling settings "
                    "and check for connection leaks in applications."
                )
            
            elif violation.metric_name == 'StorageUsage':
                if violation.severity == Severity.CRITICAL:
                    recommendations.append(
                        "CRITICAL: Storage is nearly full. Increase allocated storage "
                        "immediately to prevent outage."
                    )
                else:
                    recommendations.append(
                        "Storage usage is high. Plan to increase allocated storage soon."
                    )
        
        # Recommendations based on trends
        for trend in analysis.trends:
            if trend.trend == Trend.DEGRADING and abs(trend.change_percentage) > 20:
                recommendations.append(
                    f"{trend.metric_name} is increasing rapidly ({trend.change_percentage:.1f}%). "
                    "Investigate root cause and plan capacity adjustments."
                )
        
        # Query-specific recommendations
        if queries:
            high_impact_queries = [q for q in queries if q.total_execution_time > 1000]
            if high_impact_queries:
                recommendations.append(
                    f"Found {len(high_impact_queries)} high-impact queries. "
                    "Review execution plans and add appropriate indexes."
                )
        
        if not recommendations:
            recommendations.append(
                "No immediate action required. All metrics are within normal thresholds."
            )
        
        return recommendations
    
    def _generate_summary(
        self,
        violations: List[Violation],
        trends: List[TrendAnalysis],
        severity: Severity
    ) -> str:
        """
        Generate a summary of the analysis.
        
        Args:
            violations: List of violations
            trends: List of trend analyses
            severity: Overall severity
            
        Returns:
            Summary string
        """
        if severity == Severity.CRITICAL:
            summary = f"CRITICAL: Found {len(violations)} metric violations requiring immediate attention."
        elif severity == Severity.WARNING:
            summary = f"WARNING: Found {len(violations)} metric violations that should be monitored."
        else:
            summary = "All metrics are within normal thresholds."
        
        # Add trend information
        degrading_trends = [t for t in trends if t.trend == Trend.DEGRADING]
        if degrading_trends:
            summary += f" {len(degrading_trends)} metrics show increasing trends."
        
        return summary


class QueryAnalyzer:
    """Analyzes SQL queries from Performance Insights."""
    
    @staticmethod
    def rank_queries_by_impact(queries: List[SQLQuery]) -> List[SQLQuery]:
        """
        Rank queries by their impact (total execution time).
        
        Args:
            queries: List of SQL queries
            
        Returns:
            Sorted list of queries (highest impact first)
        """
        return sorted(
            queries,
            key=lambda q: q.total_execution_time,
            reverse=True
        )
    
    @staticmethod
    def identify_problematic_queries(
        queries: List[SQLQuery],
        threshold: float = 1000.0
    ) -> List[SQLQuery]:
        """
        Identify queries that exceed a performance threshold.
        
        Args:
            queries: List of SQL queries
            threshold: Total execution time threshold
            
        Returns:
            List of problematic queries
        """
        return [q for q in queries if q.total_execution_time > threshold]
