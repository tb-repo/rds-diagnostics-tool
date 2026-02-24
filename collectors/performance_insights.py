"""Performance Insights data collector."""

import logging
from typing import List, Optional, Dict

from aws.clients import PerformanceInsightsClient, RDSClient, AWSClientError
from core.models import TimeRange, SQLQuery, WaitEvent, TopDatabase, TopUser

logger = logging.getLogger(__name__)


# Engine-specific Performance Insights metrics mapping
# Maps RDS engine types to available PI metrics organized by category
ENGINE_METRICS = {
    'mysql': {
        'execution': [
            'db.sql.stats.executions_per_sec',
            'db.sql.stats.total_time_ms'
        ],
        'resource': [
            'db.sql.stats.cpu_time_ms',
            'db.sql.stats.lock_time_ms'
        ],
        'rows': [
            'db.sql.stats.rows_examined',
            'db.sql.stats.rows_sent'
        ],
        'io': [
            'db.sql.stats.innodb_io_r_bytes',
            'db.sql.stats.innodb_io_w_bytes'
        ]
    },
    'mariadb': {
        'execution': [
            'db.sql.stats.executions_per_sec',
            'db.sql.stats.total_time_ms'
        ],
        'resource': [
            'db.sql.stats.cpu_time_ms',
            'db.sql.stats.lock_time_ms'
        ],
        'rows': [
            'db.sql.stats.rows_examined',
            'db.sql.stats.rows_sent'
        ],
        'io': [
            'db.sql.stats.innodb_io_r_bytes',
            'db.sql.stats.innodb_io_w_bytes'
        ]
    },
    'postgres': {
        'execution': [
            'db.sql.stats.calls_per_sec',
            'db.sql.stats.total_time_ms'
        ],
        'resource': [
            'db.sql.stats.cpu_time_ms'
        ],
        'rows': [
            'db.sql.stats.rows'
        ],
        'io': [
            'db.sql.stats.shared_blks_read',
            'db.sql.stats.shared_blks_written'
        ]
    },
    'aurora-mysql': {
        'execution': [
            'db.sql.stats.executions_per_sec',
            'db.sql.stats.total_time_ms'
        ],
        'resource': [
            'db.sql.stats.cpu_time_ms',
            'db.sql.stats.lock_time_ms'
        ],
        'rows': [
            'db.sql.stats.rows_examined',
            'db.sql.stats.rows_sent'
        ],
        'io': [
            'db.sql.stats.innodb_io_r_bytes',
            'db.sql.stats.innodb_io_w_bytes'
        ]
    },
    'aurora-postgresql': {
        'execution': [
            'db.sql.stats.calls_per_sec',
            'db.sql.stats.total_time_ms'
        ],
        'resource': [
            'db.sql.stats.cpu_time_ms'
        ],
        'rows': [
            'db.sql.stats.rows'
        ],
        'io': [
            'db.sql.stats.shared_blks_read',
            'db.sql.stats.shared_blks_written'
        ]
    },
    'oracle-ee': {
        'execution': [
            'db.sql.stats.executions_per_sec',
            'db.sql.stats.elapsed_time_per_sec_ms'
        ],
        'resource': [
            'db.sql.stats.cpu_time_per_sec_ms'
        ],
        'rows': [
            'db.sql.stats.rows_processed_per_sec'
        ],
        'io': [
            'db.sql.stats.physical_read_bytes_per_sec',
            'db.sql.stats.physical_write_bytes_per_sec'
        ]
    },
    'oracle-se2': {
        'execution': [
            'db.sql.stats.executions_per_sec',
            'db.sql.stats.elapsed_time_per_sec_ms'
        ],
        'resource': [
            'db.sql.stats.cpu_time_per_sec_ms'
        ],
        'rows': [
            'db.sql.stats.rows_processed_per_sec'
        ],
        'io': [
            'db.sql.stats.physical_read_bytes_per_sec',
            'db.sql.stats.physical_write_bytes_per_sec'
        ]
    },
    'sqlserver-ee': {
        'execution': [
            'db.sql.stats.executions_per_sec',
            'db.sql.stats.total_elapsed_time_ms'
        ],
        'resource': [
            'db.sql.stats.total_worker_time_ms'
        ],
        'rows': [
            'db.sql.stats.total_rows'
        ],
        'io': [
            'db.sql.stats.total_physical_reads',
            'db.sql.stats.total_logical_writes'
        ]
    },
    'sqlserver-se': {
        'execution': [
            'db.sql.stats.executions_per_sec',
            'db.sql.stats.total_elapsed_time_ms'
        ],
        'resource': [
            'db.sql.stats.total_worker_time_ms'
        ],
        'rows': [
            'db.sql.stats.total_rows'
        ],
        'io': [
            'db.sql.stats.total_physical_reads',
            'db.sql.stats.total_logical_writes'
        ]
    }
}

# Mapping from Performance Insights metric names to SQLQuery field names
# This allows us to map engine-specific PI metrics to our standardized model
METRIC_FIELD_MAPPING = {
    # Execution metrics
    'db.sql.stats.executions_per_sec': 'executions_per_second',
    'db.sql.stats.calls_per_sec': 'executions_per_second',
    'db.sql.stats.total_time_ms': 'total_execution_time',
    'db.sql.stats.elapsed_time_per_sec_ms': 'total_execution_time',
    'db.sql.stats.total_elapsed_time_ms': 'total_execution_time',
    
    # Resource metrics
    'db.sql.stats.cpu_time_ms': 'cpu_time',
    'db.sql.stats.cpu_time_per_sec_ms': 'cpu_time',
    'db.sql.stats.total_worker_time_ms': 'cpu_time',
    'db.sql.stats.lock_time_ms': 'lock_time',
    
    # Row metrics
    'db.sql.stats.rows_examined': 'rows_examined',
    'db.sql.stats.rows_sent': 'rows_returned',
    'db.sql.stats.rows': 'rows_returned',
    'db.sql.stats.rows_processed_per_sec': 'rows_returned',
    'db.sql.stats.total_rows': 'rows_returned',
    
    # I/O metrics
    'db.sql.stats.innodb_io_r_bytes': 'read_io_bytes',
    'db.sql.stats.shared_blks_read': 'read_io_bytes',
    'db.sql.stats.physical_read_bytes_per_sec': 'read_io_bytes',
    'db.sql.stats.total_physical_reads': 'read_io_bytes',
    'db.sql.stats.innodb_io_w_bytes': 'write_io_bytes',
    'db.sql.stats.shared_blks_written': 'write_io_bytes',
    'db.sql.stats.physical_write_bytes_per_sec': 'write_io_bytes',
    'db.sql.stats.total_logical_writes': 'write_io_bytes'
}


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
    
    def _normalize_engine_name(self, engine: str) -> str:
        """
        Normalize engine name to match ENGINE_METRICS keys.
        
        Args:
            engine: Raw engine name from RDS API
            
        Returns:
            Normalized engine name
            
        Examples:
            'aurora-mysql' -> 'aurora-mysql'
            'aurora' -> 'aurora-mysql' (default to MySQL variant)
            'postgres' -> 'postgres'
            'postgresql' -> 'postgres'
        """
        engine_lower = engine.lower()
        
        # Handle Aurora variants
        if 'aurora-mysql' in engine_lower or engine_lower == 'aurora':
            return 'aurora-mysql'
        if 'aurora-postgresql' in engine_lower or 'aurora-postgres' in engine_lower:
            return 'aurora-postgresql'
        
        # Handle PostgreSQL variants
        if 'postgres' in engine_lower:
            return 'postgres'
        
        # Handle MySQL variants
        if 'mysql' in engine_lower:
            return 'mysql'
        
        # Handle MariaDB
        if 'mariadb' in engine_lower:
            return 'mariadb'
        
        # Handle Oracle variants
        if 'oracle-ee' in engine_lower:
            return 'oracle-ee'
        if 'oracle-se2' in engine_lower or 'oracle-se' in engine_lower:
            return 'oracle-se2'
        
        # Handle SQL Server variants
        if 'sqlserver-ee' in engine_lower:
            return 'sqlserver-ee'
        if 'sqlserver-se' in engine_lower or 'sqlserver' in engine_lower:
            return 'sqlserver-se'
        
        # Return as-is if no match
        return engine_lower
    
    def _get_engine_metrics_config(self, engine: str) -> Dict[str, List[str]]:
        """
        Get available Performance Insights metrics for a specific engine.
        
        Args:
            engine: RDS engine type (e.g., 'mysql', 'postgres', 'aurora-mysql')
            
        Returns:
            Dictionary mapping metric categories to metric names
            
        Example return:
            {
                'execution': ['db.sql.stats.executions_per_sec', 'db.sql.stats.total_time_ms'],
                'resource': ['db.sql.stats.cpu_time_ms', 'db.sql.stats.lock_time_ms'],
                'rows': ['db.sql.stats.rows_examined', 'db.sql.stats.rows_sent'],
                'io': ['db.sql.stats.innodb_io_r_bytes', 'db.sql.stats.innodb_io_w_bytes']
            }
        """
        normalized_engine = self._normalize_engine_name(engine)
        
        if normalized_engine in ENGINE_METRICS:
            return ENGINE_METRICS[normalized_engine]
        
        # Log warning for unknown engine and return standard metrics (MySQL-like)
        logger.warning(
            f"Unknown engine type '{engine}' (normalized: '{normalized_engine}'). "
            f"Using standard MySQL metrics as fallback."
        )
        return ENGINE_METRICS['mysql']
    
    def _map_metric_name(self, pi_metric_name: str, engine: str) -> Optional[str]:
        """
        Map Performance Insights metric name to SQLQuery field name.
        
        Args:
            pi_metric_name: Performance Insights metric name (e.g., 'db.sql.stats.cpu_time_ms')
            engine: RDS engine type (used for logging context)
            
        Returns:
            SQLQuery field name (e.g., 'cpu_time') or None if unmapped
            
        Examples:
            'db.sql.stats.cpu_time_ms' -> 'cpu_time'
            'db.sql.stats.rows_examined' -> 'rows_examined'
            'db.sql.stats.calls_per_sec' -> 'executions_per_second'
        """
        field_name = METRIC_FIELD_MAPPING.get(pi_metric_name)
        
        if field_name is None:
            logger.debug(
                f"No mapping found for PI metric '{pi_metric_name}' "
                f"(engine: {engine})"
            )
        
        return field_name
    
    def _validate_metric_value(self, metric_name: str, value: any) -> Optional[float]:
        """
        Validate a metric value for basic sanity checks.
        
        Args:
            metric_name: Name of the metric
            value: Raw value from API
            
        Returns:
            Validated float value or None if invalid
            
        Validation rules:
            - Must be numeric
            - Must be non-negative for time/count metrics
            - Must not be infinity or NaN
            - Logs warning for invalid values
        """
        # Handle None values
        if value is None:
            return None
        
        # Try to convert to float
        try:
            float_value = float(value)
        except (TypeError, ValueError):
            logger.warning(
                f"Invalid metric value for '{metric_name}': {value} "
                f"(not numeric). Setting to None."
            )
            return None
        
        # Check for infinity
        if float_value == float('inf') or float_value == float('-inf'):
            logger.warning(
                f"Invalid metric value for '{metric_name}': {value} "
                f"(infinity). Setting to None."
            )
            return None
        
        # Check for NaN
        if float_value != float_value:  # NaN != NaN is True
            logger.warning(
                f"Invalid metric value for '{metric_name}': {value} "
                f"(NaN). Setting to None."
            )
            return None
        
        # Check for negative values (all our metrics should be non-negative)
        if float_value < 0:
            logger.warning(
                f"Invalid metric value for '{metric_name}': {value} "
                f"(negative). Setting to None."
            )
            return None
        
        return float_value
    
    def _collect_query_metrics(
        self,
        resource_id: str,
        sql_id: str,
        engine: str,
        time_range: TimeRange
    ) -> Dict[str, Optional[float]]:
        """
        Collect detailed metrics for a specific SQL query.
        
        Args:
            resource_id: Performance Insights resource identifier
            sql_id: SQL query identifier
            engine: RDS engine type
            time_range: Time range for metric collection
            
        Returns:
            Dictionary of field names to values (None if unavailable)
            
        Note:
            - Uses get_resource_metrics API
            - Returns values exactly as provided by API
            - No aggregation or calculation performed
        """
        # Get engine-specific metric configuration
        metric_config = self._get_engine_metrics_config(engine)
        
        # Build metric queries for get_resource_metrics
        metric_queries = []
        for category, metric_names in metric_config.items():
            for metric_name in metric_names:
                metric_queries.append({
                    'Metric': metric_name,
                    'GroupBy': {
                        'Group': 'db.sql',
                        'Dimensions': ['db.sql.id']
                    },
                    'Filter': {
                        'db.sql.id': sql_id
                    }
                })
        
        try:
            # Call get_resource_metrics
            response = self.pi_client.get_resource_metrics(
                resource_id=resource_id,
                metric_queries=metric_queries,
                start_time=time_range.start,
                end_time=time_range.end
            )
            
            # Parse response and extract metrics
            metrics = {}
            
            for metric_data in response.get('MetricList', []):
                metric_key = metric_data.get('Key', {})
                metric_name = metric_key.get('Metric')
                
                if not metric_name:
                    continue
                
                # Get data points
                data_points = metric_data.get('DataPoints', [])
                
                if not data_points:
                    logger.debug(
                        f"No data points for metric '{metric_name}' "
                        f"(SQL ID: {sql_id}, engine: {engine})"
                    )
                    continue
                
                # Calculate average across data points
                # This is aggregation of time-series data, not calculation of derived metrics
                values = [dp.get('Value') for dp in data_points if 'Value' in dp]
                
                if not values:
                    continue
                
                # Average the values across the time range
                avg_value = sum(values) / len(values)
                
                # Validate the metric value
                validated_value = self._validate_metric_value(metric_name, avg_value)
                
                # Map PI metric name to our field name
                field_name = self._map_metric_name(metric_name, engine)
                
                if field_name:
                    metrics[field_name] = validated_value
            
            logger.debug(
                f"Collected {len(metrics)} metrics for SQL ID {sql_id} "
                f"(engine: {engine})"
            )
            
            return metrics
            
        except AWSClientError as e:
            logger.warning(
                f"Failed to collect enhanced metrics for SQL ID {sql_id}: {e}"
            )
            return {}
        except Exception as e:
            logger.warning(
                f"Unexpected error collecting metrics for SQL ID {sql_id}: {e}"
            )
            return {}
    
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
        Collect top SQL queries with enhanced metrics.
        
        Enhanced behavior:
            1. Use describe_dimension_keys to identify top queries
            2. For each query, call _collect_query_metrics for enhanced data
            3. Build SQLQuery with all available metrics
            4. Handle missing metrics gracefully (set to None)
            5. Fall back to basic collection if enhanced fails
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for query data
            limit: Maximum number of queries to return
            
        Returns:
            List of SQLQuery objects with enhanced metrics when available
            
        Backward compatibility:
            - Maintains existing signature
            - Returns same SQLQuery type (with optional new fields)
            - Gracefully degrades if get_resource_metrics unavailable
        """
        if not self.is_performance_insights_enabled(instance_id):
            logger.warning(
                f"Performance Insights not enabled for {instance_id}"
            )
            return []
        
        try:
            # Get resource ID and engine type for PI API
            resource_id = self.rds_client.get_instance_resource_id(instance_id)
            instance_data = self.rds_client.describe_instance(instance_id)
            engine = instance_data.get('Engine', 'unknown')
            
            logger.debug(f"Collecting SQL queries for {instance_id} (engine: {engine})")
            
            # Phase 1: Identify top queries using describe_dimension_keys
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
                
                # Get basic metrics from dimension keys
                total_load = key.get('Total', 0.0)
                partitions = key.get('Partitions', [])
                exec_count = len(partitions) if partitions else 1
                avg_load = total_load / exec_count if exec_count > 0 else total_load
                wait_events = self._extract_wait_events(key)
                
                # Phase 2: Try to collect enhanced metrics for this query
                enhanced_metrics = {}
                try:
                    enhanced_metrics = self._collect_query_metrics(
                        resource_id=resource_id,
                        sql_id=sql_id,
                        engine=engine,
                        time_range=time_range
                    )
                    
                    if enhanced_metrics:
                        logger.debug(
                            f"Collected {len(enhanced_metrics)} enhanced metrics "
                            f"for SQL ID {sql_id}"
                        )
                except Exception as e:
                    logger.warning(
                        f"Enhanced metric collection failed for SQL ID {sql_id}: {e}. "
                        f"Using basic metrics only."
                    )
                    enhanced_metrics = {}
                
                # Build SQLQuery with enhanced metrics when available
                queries.append(SQLQuery(
                    query_id=sql_id,
                    query_text=sql_text,
                    total_execution_time=total_load,  # Load from dimension keys
                    average_execution_time=avg_load,  # Average load per partition
                    execution_count=exec_count,  # Number of time partitions
                    rows_affected=None,  # Not available in PI API
                    wait_events=wait_events,
                    # Enhanced optional fields (from _collect_query_metrics)
                    engine_type=engine,
                    executions_per_second=enhanced_metrics.get('executions_per_second'),
                    cpu_time=enhanced_metrics.get('cpu_time'),
                    lock_time=enhanced_metrics.get('lock_time'),
                    rows_examined=enhanced_metrics.get('rows_examined'),
                    rows_returned=enhanced_metrics.get('rows_returned'),
                    read_io_bytes=enhanced_metrics.get('read_io_bytes'),
                    write_io_bytes=enhanced_metrics.get('write_io_bytes')
                ))
                
                # Stop when we have enough unique queries
                if len(queries) >= limit:
                    break
            
            logger.info(
                f"Collected {len(queries)} top SQL queries for {instance_id} "
                f"(engine: {engine})"
            )
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
