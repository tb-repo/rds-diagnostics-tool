"""Performance Insights data collector."""

import logging
from typing import List, Optional

from aws.clients import PerformanceInsightsClient, RDSClient, AWSClientError
from core.models import TimeRange, SQLQuery, WaitEvent, TopDatabase, TopUser

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
            seen_queries = set()  # For deduplication
            
            for i, key in enumerate(dimension_keys[:limit * 2]):  # Get more to account for duplicates
                dimensions = key.get('Dimensions', {})
                sql_text = dimensions.get('db.sql.statement', 'N/A')
                sql_id = dimensions.get('db.sql.id', f'query_{i}')
                
                # Deduplicate by query ID
                if sql_id in seen_queries:
                    continue
                seen_queries.add(sql_id)
                
                # Get metrics for this query
                total_load = key.get('Total', 0.0)
                
                # The 'Total' represents the total database load (AAS - Average Active Sessions)
                # contributed by this query over the time period
                # This is NOT execution time in seconds, but load units
                
                # For execution count and average time, we need to look at partitions
                # Each partition represents a time slice
                partitions = key.get('Partitions', [])
                
                # Calculate more accurate execution statistics
                # The load value represents average active sessions
                # We can't get exact execution count from describe_dimension_keys alone
                # But we can provide the load value which is more meaningful
                
                # For now, we'll use the load as total_execution_time
                # and indicate that execution_count is not available from this API
                exec_count = len(partitions) if partitions else 1
                avg_load = total_load / exec_count if exec_count > 0 else total_load
                
                # Get wait events for this query
                wait_events = self._extract_wait_events(key)
                
                queries.append(SQLQuery(
                    query_id=sql_id,
                    query_text=sql_text,
                    total_execution_time=total_load,  # This is actually load, not time
                    average_execution_time=avg_load,  # Average load per partition
                    execution_count=exec_count,  # Number of time partitions
                    rows_affected=None,  # Not available in PI API
                    wait_events=wait_events
                ))
                
                # Stop when we have enough unique queries
                if len(queries) >= limit:
                    break
            
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
    
    def collect_top_databases(
        self,
        instance_id: str,
        time_range: TimeRange,
        limit: int = 10
    ) -> List[TopDatabase]:
        """
        Collect top databases by load.
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for database data
            limit: Maximum number of databases to return
            
        Returns:
            List of TopDatabase objects
        """
        if not self.is_performance_insights_enabled(instance_id):
            logger.warning(
                f"Performance Insights not enabled for {instance_id}"
            )
            return []
        
        try:
            # Get resource ID for PI API
            resource_id = self.rds_client.get_instance_resource_id(instance_id)
            
            # Get top databases by load
            dimension_keys = self.pi_client.describe_dimension_keys(
                resource_id=resource_id,
                group_by='db.name',
                start_time=time_range.start,
                end_time=time_range.end,
                metric='db.load.avg'
            )
            
            # Calculate total load for percentage
            total_load = sum(key.get('Total', 0.0) for key in dimension_keys)
            
            # Parse and convert to TopDatabase objects
            databases = []
            for key in dimension_keys[:limit]:
                dimensions = key.get('Dimensions', {})
                db_name = dimensions.get('db.name', 'Unknown')
                
                db_load = key.get('Total', 0.0)
                load_pct = (db_load / total_load * 100) if total_load > 0 else 0.0
                
                databases.append(TopDatabase(
                    database_name=db_name,
                    total_load=db_load,
                    load_percentage=load_pct
                ))
            
            logger.info(f"Collected {len(databases)} top databases")
            return databases
            
        except AWSClientError as e:
            logger.error(f"Failed to collect top databases: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error collecting top databases: {e}")
            return []
    
    def collect_top_users(
        self,
        instance_id: str,
        time_range: TimeRange,
        limit: int = 10
    ) -> List[TopUser]:
        """
        Collect top users by load.
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for user data
            limit: Maximum number of users to return
            
        Returns:
            List of TopUser objects
        """
        if not self.is_performance_insights_enabled(instance_id):
            logger.warning(
                f"Performance Insights not enabled for {instance_id}"
            )
            return []
        
        try:
            # Get resource ID for PI API
            resource_id = self.rds_client.get_instance_resource_id(instance_id)
            
            # Get top users by load
            dimension_keys = self.pi_client.describe_dimension_keys(
                resource_id=resource_id,
                group_by='db.user',
                start_time=time_range.start,
                end_time=time_range.end,
                metric='db.load.avg'
            )
            
            # Calculate total load for percentage
            total_load = sum(key.get('Total', 0.0) for key in dimension_keys)
            
            # Parse and convert to TopUser objects
            users = []
            for key in dimension_keys[:limit]:
                dimensions = key.get('Dimensions', {})
                user_name = dimensions.get('db.user', 'Unknown')
                
                user_load = key.get('Total', 0.0)
                load_pct = (user_load / total_load * 100) if total_load > 0 else 0.0
                
                users.append(TopUser(
                    user_name=user_name,
                    total_load=user_load,
                    load_percentage=load_pct
                ))
            
            logger.info(f"Collected {len(users)} top users")
            return users
            
        except AWSClientError as e:
            logger.error(f"Failed to collect top users: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error collecting top users: {e}")
            return []
