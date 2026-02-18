"""Performance Insights data collector."""

import logging
from typing import List, Optional

from aws.clients import PerformanceInsightsClient, RDSClient, AWSClientError
from core.models import TimeRange, SQLQuery, WaitEvent

logger = logging.getLogger(__name__)


class PerformanceInsightsCollector:
    """Collects Performance Insights data for RDS instances."""
    
    def __init__(
        self,
        pi_client: PerformanceInsightsClient,
        rds_client: RDSClient
    ):
        """
        Initialize Performance Insights collector.
        
        Args:
            pi_client: Performance Insights client wrapper
            rds_client: RDS client wrapper
        """
        self.pi_client = pi_client
        self.rds_client = rds_client
    
    def is_performance_insights_enabled(self, instance_id: str) -> bool:
        """
        Check if Performance Insights is enabled for an instance.
        
        Args:
            instance_id: RDS instance identifier
            
        Returns:
            True if PI is enabled, False otherwise
        """
        try:
            instance_data = self.rds_client.describe_instance(instance_id)
            return instance_data.get('PerformanceInsightsEnabled', False)
        except AWSClientError as e:
            logger.error(f"Failed to check PI status: {e}")
            return False
    
    def collect_top_sql_queries(
        self,
        instance_id: str,
        time_range: TimeRange,
        limit: int = 10
    ) -> List[SQLQuery]:
        """
        Collect top SQL queries by execution time.
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for query data
            limit: Maximum number of queries to return
            
        Returns:
            List of SQLQuery objects
        """
        if not self.is_performance_insights_enabled(instance_id):
            logger.warning(
                f"Performance Insights not enabled for {instance_id}"
            )
            return []
        
        try:
            # Get resource ID for PI API
            resource_id = self.rds_client.get_instance_resource_id(instance_id)
            
            # Get top SQL queries by database load
            dimension_keys = self.pi_client.describe_dimension_keys(
                resource_id=resource_id,
                group_by='db.sql',
                start_time=time_range.start,
                end_time=time_range.end,
                metric='db.load.avg'
            )
            
            # Parse and convert to SQLQuery objects
            queries = []
            for i, key in enumerate(dimension_keys[:limit]):
                dimensions = key.get('Dimensions', {})
                sql_text = dimensions.get('db.sql.statement', 'N/A')
                sql_id = dimensions.get('db.sql.id', f'query_{i}')
                
                # Get metrics for this query
                total_load = key.get('Total', 0.0)
                partitions = key.get('Partitions', [])
                
                # Calculate execution stats from partitions
                exec_count = 0
                avg_exec_time = 0.0
                
                if partitions:
                    # Estimate from load data
                    exec_count = len(partitions)
                    avg_exec_time = total_load / exec_count if exec_count > 0 else 0.0
                
                # Get wait events for this query
                wait_events = self._extract_wait_events(key)
                
                queries.append(SQLQuery(
                    query_id=sql_id,
                    query_text=sql_text,
                    total_execution_time=total_load,
                    average_execution_time=avg_exec_time,
                    execution_count=exec_count,
                    rows_affected=None,  # Not available in PI API
                    wait_events=wait_events
                ))
            
            logger.info(f"Collected {len(queries)} top SQL queries")
            return queries
            
        except AWSClientError as e:
            logger.error(f"Failed to collect top SQL queries: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error collecting SQL queries: {e}")
            return []
    
    def collect_wait_events(
        self,
        instance_id: str,
        time_range: TimeRange
    ) -> List[WaitEvent]:
        """
        Collect wait event data.
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for wait event data
            
        Returns:
            List of WaitEvent objects
        """
        if not self.is_performance_insights_enabled(instance_id):
            logger.warning(
                f"Performance Insights not enabled for {instance_id}"
            )
            return []
        
        try:
            # Get resource ID for PI API
            resource_id = self.rds_client.get_instance_resource_id(instance_id)
            
            # Get wait events
            dimension_keys = self.pi_client.describe_dimension_keys(
                resource_id=resource_id,
                group_by='db.wait_event',
                start_time=time_range.start,
                end_time=time_range.end,
                metric='db.load.avg'
            )
            
            # Parse and convert to WaitEvent objects
            wait_events = []
            for key in dimension_keys:
                dimensions = key.get('Dimensions', {})
                event_name = dimensions.get('db.wait_event.name', 'Unknown')
                
                total_wait = key.get('Total', 0.0)
                partitions = key.get('Partitions', [])
                wait_count = len(partitions)
                
                wait_events.append(WaitEvent(
                    event_name=event_name,
                    total_wait_time=total_wait,
                    wait_count=wait_count
                ))
            
            logger.info(f"Collected {len(wait_events)} wait events")
            return wait_events
            
        except AWSClientError as e:
            logger.error(f"Failed to collect wait events: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error collecting wait events: {e}")
            return []
    
    def _extract_wait_events(self, dimension_key: dict) -> List[str]:
        """
        Extract wait event names from dimension key data.
        
        Args:
            dimension_key: Dimension key data from PI API
            
        Returns:
            List of wait event names
        """
        wait_events = []
        
        # Try to extract wait events from additional dimensions
        additional_dims = dimension_key.get('AdditionalMetrics', {})
        for key, value in additional_dims.items():
            if 'wait' in key.lower():
                wait_events.append(key)
        
        return wait_events
