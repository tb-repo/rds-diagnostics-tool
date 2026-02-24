"""SQL query analysis and recommendation generation."""

import logging
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

from core.models import SQLQuery

logger = logging.getLogger(__name__)


@dataclass
class SQLRecommendation:
    """A recommendation for SQL query optimization."""
    
    query_id: str
    query_text: str
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'index', 'lock', 'cache', 'cpu', 'efficiency'
    recommendation: str
    impact_estimate: str
    metrics: Dict[str, float]  # Supporting metrics for the recommendation


class SQLRecommendationGenerator:
    """Generates recommendations based on SQL query metrics."""
    
    def __init__(
        self,
        index_efficiency_threshold: float = 0.1,
        lock_time_threshold_pct: float = 30.0,
        cpu_time_threshold_pct: float = 80.0,
        high_frequency_threshold: float = 1.0,
        high_execution_time_threshold: float = 1000.0
    ):
        """
        Initialize SQL recommendation generator.
        
        Args:
            index_efficiency_threshold: Efficiency ratio below which to suggest indexing (default: 0.1)
            lock_time_threshold_pct: Lock time percentage above which to flag contention (default: 30%)
            cpu_time_threshold_pct: CPU time percentage above which to flag CPU-intensive (default: 80%)
            high_frequency_threshold: Executions per second above which to suggest caching (default: 1.0)
            high_execution_time_threshold: Total execution time above which to prioritize (default: 1000ms)
        """
        self.index_efficiency_threshold = index_efficiency_threshold
        self.lock_time_threshold_pct = lock_time_threshold_pct
        self.cpu_time_threshold_pct = cpu_time_threshold_pct
        self.high_frequency_threshold = high_frequency_threshold
        self.high_execution_time_threshold = high_execution_time_threshold
    
    def generate_recommendations(
        self,
        queries: List[SQLQuery]
    ) -> List[SQLRecommendation]:
        """
        Generate prioritized recommendations for SQL queries.
        
        Args:
            queries: List of SQL queries with metrics
            
        Returns:
            List of recommendation objects, prioritized by impact
            
        Note:
            All calculations (efficiency ratios, percentages) happen here.
            Raw data in SQLQuery objects remains unmodified.
        """
        recommendations = []
        
        # Collect recommendations from each analysis method
        recommendations.extend(self._identify_index_opportunities(queries))
        recommendations.extend(self._detect_lock_contention(queries))
        recommendations.extend(self._suggest_caching_candidates(queries))
        recommendations.extend(self._identify_cpu_intensive(queries))
        
        # Sort by priority (highest total execution time first)
        recommendations.sort(
            key=lambda r: r.metrics.get('total_execution_time', 0),
            reverse=True
        )
        
        logger.info(f"Generated {len(recommendations)} SQL recommendations")
        return recommendations
    
    def _calculate_efficiency_ratio(
        self,
        query: SQLQuery
    ) -> Optional[float]:
        """
        Calculate efficiency ratio (rows_returned / rows_examined).
        
        Args:
            query: SQL query with metrics
            
        Returns:
            Ratio between 0 and 1, or None if metrics unavailable
            
        Note:
            This is the ONLY place where calculations happen.
            Raw data remains unmodified.
        """
        if query.rows_examined is None or query.rows_returned is None:
            return None
        
        if query.rows_examined == 0:
            return None
        
        # Calculate ratio
        ratio = query.rows_returned / query.rows_examined
        
        # Clamp to [0, 1] range (shouldn't exceed 1, but handle edge cases)
        return max(0.0, min(1.0, ratio))
    
    def _calculate_lock_time_percentage(
        self,
        query: SQLQuery
    ) -> Optional[float]:
        """
        Calculate lock time as percentage of total execution time.
        
        Args:
            query: SQL query with metrics
            
        Returns:
            Percentage (0-100), or None if metrics unavailable
        """
        if query.lock_time is None or query.total_execution_time is None:
            return None
        
        if query.total_execution_time == 0:
            return None
        
        return (query.lock_time / query.total_execution_time) * 100
    
    def _calculate_cpu_time_percentage(
        self,
        query: SQLQuery
    ) -> Optional[float]:
        """
        Calculate CPU time as percentage of total execution time.
        
        Args:
            query: SQL query with metrics
            
        Returns:
            Percentage (0-100), or None if metrics unavailable
        """
        if query.cpu_time is None or query.total_execution_time is None:
            return None
        
        if query.total_execution_time == 0:
            return None
        
        return (query.cpu_time / query.total_execution_time) * 100
    
    def _identify_index_opportunities(
        self,
        queries: List[SQLQuery]
    ) -> List[SQLRecommendation]:
        """
        Identify queries that may benefit from indexing.
        
        Criteria:
            - rows_examined >> rows_returned (ratio < threshold)
            - High total_execution_time
            - High execution_count
            
        Args:
            queries: List of SQL queries with metrics
            
        Returns:
            List of index-related recommendations
        """
        recommendations = []
        
        for query in queries:
            efficiency_ratio = self._calculate_efficiency_ratio(query)
            
            if efficiency_ratio is None:
                continue
            
            # Check if efficiency is below threshold
            if efficiency_ratio < self.index_efficiency_threshold:
                # Calculate impact estimate
                if query.total_execution_time > self.high_execution_time_threshold:
                    severity = 'critical'
                    impact = 'High - Query consumes significant database time'
                elif query.execution_count > 100:
                    severity = 'warning'
                    impact = 'Medium - Query executes frequently'
                else:
                    severity = 'info'
                    impact = 'Low - Consider if query frequency increases'
                
                # Build recommendation text
                recommendation_text = (
                    f"Query examines {query.rows_examined:,} rows but returns only "
                    f"{query.rows_returned:,} rows (efficiency: {efficiency_ratio:.1%}). "
                    f"Consider adding indexes to improve query selectivity. "
                    f"Review WHERE clause conditions and JOIN predicates."
                )
                
                recommendations.append(SQLRecommendation(
                    query_id=query.query_id,
                    query_text=query.query_text[:200] + '...' if len(query.query_text) > 200 else query.query_text,
                    severity=severity,
                    category='index',
                    recommendation=recommendation_text,
                    impact_estimate=impact,
                    metrics={
                        'efficiency_ratio': efficiency_ratio,
                        'rows_examined': float(query.rows_examined),
                        'rows_returned': float(query.rows_returned),
                        'total_execution_time': query.total_execution_time,
                        'execution_count': float(query.execution_count)
                    }
                ))
        
        logger.debug(f"Identified {len(recommendations)} index opportunities")
        return recommendations
    
    def _detect_lock_contention(
        self,
        queries: List[SQLQuery]
    ) -> List[SQLRecommendation]:
        """
        Identify queries with significant lock contention.
        
        Criteria:
            - lock_time > threshold% of total_execution_time
            - High execution_count
            
        Args:
            queries: List of SQL queries with metrics
            
        Returns:
            List of lock contention recommendations
        """
        recommendations = []
        
        for query in queries:
            lock_pct = self._calculate_lock_time_percentage(query)
            
            if lock_pct is None:
                continue
            
            # Check if lock time exceeds threshold
            if lock_pct > self.lock_time_threshold_pct:
                # Calculate impact estimate
                if lock_pct > 50:
                    severity = 'critical'
                    impact = 'High - Lock contention is severe'
                elif query.execution_count > 100:
                    severity = 'warning'
                    impact = 'Medium - Frequent lock contention'
                else:
                    severity = 'info'
                    impact = 'Low - Monitor for increased frequency'
                
                # Build recommendation text
                recommendation_text = (
                    f"Query spends {lock_pct:.1f}% of execution time waiting for locks "
                    f"({query.lock_time:.2f}ms of {query.total_execution_time:.2f}ms total). "
                    f"Consider: 1) Reviewing transaction isolation levels, "
                    f"2) Reducing transaction scope, "
                    f"3) Optimizing query to reduce lock duration, "
                    f"4) Reviewing concurrent access patterns."
                )
                
                recommendations.append(SQLRecommendation(
                    query_id=query.query_id,
                    query_text=query.query_text[:200] + '...' if len(query.query_text) > 200 else query.query_text,
                    severity=severity,
                    category='lock',
                    recommendation=recommendation_text,
                    impact_estimate=impact,
                    metrics={
                        'lock_time_percentage': lock_pct,
                        'lock_time': query.lock_time,
                        'total_execution_time': query.total_execution_time,
                        'execution_count': float(query.execution_count)
                    }
                ))
        
        logger.debug(f"Detected {len(recommendations)} lock contention issues")
        return recommendations
    
    def _suggest_caching_candidates(
        self,
        queries: List[SQLQuery]
    ) -> List[SQLRecommendation]:
        """
        Identify queries that may benefit from caching.
        
        Criteria:
            - High execution_count or executions_per_second
            - Low average_execution_time (query is fast but frequent)
            - Consistent results (heuristic: SELECT queries)
            
        Args:
            queries: List of SQL queries with metrics
            
        Returns:
            List of caching recommendations
        """
        recommendations = []
        
        for query in queries:
            # Check execution frequency
            is_high_frequency = False
            frequency_metric = None
            
            if query.executions_per_second is not None:
                if query.executions_per_second >= self.high_frequency_threshold:
                    is_high_frequency = True
                    frequency_metric = f"{query.executions_per_second:.2f} calls/sec"
            elif query.execution_count > 1000:
                is_high_frequency = True
                frequency_metric = f"{query.execution_count:,} executions"
            
            if not is_high_frequency:
                continue
            
            # Check if query is fast (good candidate for caching)
            if query.average_execution_time > 100:  # Skip slow queries
                continue
            
            # Heuristic: Only suggest caching for SELECT queries
            query_upper = query.query_text.upper().strip()
            if not query_upper.startswith('SELECT'):
                continue
            
            # Calculate impact estimate
            if query.executions_per_second and query.executions_per_second > 10:
                severity = 'warning'
                impact = 'High - Very high frequency query'
            elif query.execution_count > 5000:
                severity = 'warning'
                impact = 'Medium - High frequency query'
            else:
                severity = 'info'
                impact = 'Low - Consider for application-level caching'
            
            # Build recommendation text
            recommendation_text = (
                f"Query executes very frequently ({frequency_metric}) with fast execution time "
                f"({query.average_execution_time:.2f}ms average). "
                f"Consider: 1) Application-level caching (Redis, Memcached), "
                f"2) Query result caching, "
                f"3) Materialized views if data changes infrequently."
            )
            
            recommendations.append(SQLRecommendation(
                query_id=query.query_id,
                query_text=query.query_text[:200] + '...' if len(query.query_text) > 200 else query.query_text,
                severity=severity,
                category='cache',
                recommendation=recommendation_text,
                impact_estimate=impact,
                metrics={
                    'executions_per_second': query.executions_per_second or 0.0,
                    'execution_count': float(query.execution_count),
                    'average_execution_time': query.average_execution_time,
                    'total_execution_time': query.total_execution_time
                }
            ))
        
        logger.debug(f"Identified {len(recommendations)} caching candidates")
        return recommendations
    
    def _identify_cpu_intensive(
        self,
        queries: List[SQLQuery]
    ) -> List[SQLRecommendation]:
        """
        Identify CPU-intensive queries.
        
        Criteria:
            - cpu_time is disproportionately high relative to total_execution_time
            - High total CPU consumption
            
        Args:
            queries: List of SQL queries with metrics
            
        Returns:
            List of CPU-intensive query recommendations
        """
        recommendations = []
        
        for query in queries:
            cpu_pct = self._calculate_cpu_time_percentage(query)
            
            if cpu_pct is None:
                continue
            
            # Check if CPU time exceeds threshold
            if cpu_pct > self.cpu_time_threshold_pct:
                # Calculate impact estimate
                if query.cpu_time > 5000:  # More than 5 seconds
                    severity = 'critical'
                    impact = 'High - Significant CPU consumption'
                elif query.cpu_time > 1000:  # More than 1 second
                    severity = 'warning'
                    impact = 'Medium - Moderate CPU consumption'
                else:
                    severity = 'info'
                    impact = 'Low - Monitor CPU usage'
                
                # Build recommendation text
                recommendation_text = (
                    f"Query is CPU-intensive, using {cpu_pct:.1f}% of execution time on CPU "
                    f"({query.cpu_time:.2f}ms of {query.total_execution_time:.2f}ms total). "
                    f"Consider: 1) Query optimization (reduce complexity, simplify calculations), "
                    f"2) Adding indexes to reduce CPU-intensive operations, "
                    f"3) Moving complex calculations to application layer, "
                    f"4) Scaling database compute resources if optimization is not possible."
                )
                
                recommendations.append(SQLRecommendation(
                    query_id=query.query_id,
                    query_text=query.query_text[:200] + '...' if len(query.query_text) > 200 else query.query_text,
                    severity=severity,
                    category='cpu',
                    recommendation=recommendation_text,
                    impact_estimate=impact,
                    metrics={
                        'cpu_time_percentage': cpu_pct,
                        'cpu_time': query.cpu_time,
                        'total_execution_time': query.total_execution_time,
                        'execution_count': float(query.execution_count)
                    }
                ))
        
        logger.debug(f"Identified {len(recommendations)} CPU-intensive queries")
        return recommendations
