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
            'db.sql.stats.total_time_ms',
            'db.sql.stats.avg_latency_ms'  # Added for Aurora PG 17+
        ],
        'resource': [
            'db.sql.stats.cpu_time_ms',
            'db.sql.stats.read_latency_ms',  # Added for Aurora PG 17+
            'db.sql.stats.write_latency_ms'  # Added for Aurora PG 17+
        ],
        'rows': [
            'db.sql.stats.rows',
            'db.sql.stats.rows_per_sec'  # Added for Aurora PG 17+
        ],
        'io': [
            'db.sql.stats.shared_blks_read',
            'db.sql.stats.shared_blks_written',
            'db.sql.stats.blk_read_time',  # Added for Aurora PG 17+
            'db.sql.stats.blk_write_time'  # Added for Aurora PG 17+
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
    'db.sql.stats.avg_latency_ms': 'average_execution_time',  # Aurora PG 17+
    'db.sql.stats.elapsed_time_per_sec_ms': 'total_execution_time',
    'db.sql.stats.total_elapsed_time_ms': 'total_execution_time',
    
    # Resource metrics
    'db.sql.stats.cpu_time_ms': 'cpu_time',
    'db.sql.stats.cpu_time_per_sec_ms': 'cpu_time',
    'db.sql.stats.total_worker_time_ms': 'cpu_time',
    'db.sql.stats.lock_time_ms': 'lock_time',
    'db.sql.stats.read_latency_ms': 'read_io_time',  # Aurora PG 17+ - NEW FIELD
    'db.sql.stats.write_latency_ms': 'write_io_time',  # Aurora PG 17+ - NEW FIELD
    'db.sql.stats.blk_read_time': 'read_io_time',  # Aurora PG 17+ - alternative name
    'db.sql.stats.blk_write_time': 'write_io_time',  # Aurora PG 17+ - alternative name
    
    # Row metrics
    'db.sql.stats.rows_examined': 'rows_examined',
    'db.sql.stats.rows_sent': 'rows_returned',
    'db.sql.stats.rows': 'rows_returned',
    'db.sql.stats.rows_per_sec': 'rows_per_second',  # Aurora PG 17+ - NEW FIELD
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
        
        logger.debug(
            f"Building metric queries for SQL ID {sql_id}, engine {engine}. "
            f"Metrics config: {metric_config}"
        )
        
        # Build metric queries for get_resource_metrics
        metric_queries = []
        for category, metric_names in metric_config.items():
            for metric_name in metric_names:
                # Build query without Filter first - let's get all data and filter locally
                metric_queries.append({
                    'Metric': metric_name
                })
        
        logger.debug(f"Built {len(metric_queries)} metric queries: {metric_queries}")
        
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
            
            logger.debug(f"get_resource_metrics response for SQL ID {sql_id}: {response}")
            
            for metric_data in response.get('MetricList', []):
                metric_key = metric_data.get('Key', {})
                metric_name = metric_key.get('Metric')
                
                logger.debug(f"Processing metric: {metric_name}, data: {metric_data}")
                
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
            2. Request additional metrics in the same API call
            3. Build SQLQuery with all available metrics
            4. Handle missing metrics gracefully (set to None)
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for query data
            limit: Maximum number of queries to return
            
        Returns:
            List of SQLQuery objects with enhanced metrics when available
            
        Backward compatibility:
            - Maintains existing signature
            - Returns same SQLQuery type (with optional new fields)
            - Gracefully degrades if metrics unavailable
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
            
            # Get engine-specific metrics to request
            metric_config = self._get_engine_metrics_config(engine)
            additional_metrics = []
            for category, metric_names in metric_config.items():
                additional_metrics.extend(metric_names)
            
            logger.debug(f"Requesting additional metrics: {additional_metrics}")
            
            # Phase 1: Identify top queries using describe_dimension_keys
            # Try with additional_metrics first, fall back to basic if it fails
            dimension_keys = []
            try:
                if additional_metrics:
                    dimension_keys = self.pi_client.describe_dimension_keys(
                        resource_id=resource_id,
                        group_by='db.sql',
                        start_time=time_range.start,
                        end_time=time_range.end,
                        metric='db.load.avg',
                        additional_metrics=additional_metrics
                    )
                    logger.debug(f"Successfully retrieved {len(dimension_keys)} dimension keys with additional metrics")
                else:
                    # No additional metrics to request, go straight to basic
                    raise ValueError("No additional metrics configured")
            except Exception as e:
                logger.warning(
                    f"Failed to get dimension keys with additional_metrics: {e}. "
                    f"Retrying without additional metrics..."
                )
                # Fallback: try without additional_metrics
                try:
                    dimension_keys = self.pi_client.describe_dimension_keys(
                        resource_id=resource_id,
                        group_by='db.sql',
                        start_time=time_range.start,
                        end_time=time_range.end,
                        metric='db.load.avg'
                        # No additional_metrics parameter
                    )
                    logger.info(f"Successfully retrieved {len(dimension_keys)} dimension keys without additional metrics")
                except Exception as e2:
                    logger.error(f"Failed to get dimension keys even without additional_metrics: {e2}")
                    raise
            
            # Parse and convert to SQLQuery objects
            queries = []
            seen_queries = set()  # For deduplication
            
            logger.debug(f"Processing {len(dimension_keys)} dimension keys")
            
            if not dimension_keys:
                logger.warning(f"No SQL queries found for {instance_id} in the specified time range")
                return []
            
            for i, key in enumerate(dimension_keys[:limit * 2]):  # Get more to account for duplicates
                logger.debug(f"Processing dimension key {i+1}: {key}")
                
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
                # NOTE: Partitions represent time buckets, NOT execution count
                # Execution count is not available from PI API for PostgreSQL
                time_buckets = len(partitions) if partitions else 1
                avg_load = total_load / time_buckets if time_buckets > 0 else total_load
                wait_events = self._extract_wait_events(key)
                
                # Extract additional metrics from the key's AdditionalMetrics field
                additional_metrics_data = key.get('AdditionalMetrics', {})
                
                logger.debug(
                    f"SQL ID {sql_id}: AdditionalMetrics = {additional_metrics_data}"
                )
                
                # Map additional metrics to our field names
                enhanced_metrics = {}
                for pi_metric_name, value in additional_metrics_data.items():
                    field_name = self._map_metric_name(pi_metric_name, engine)
                    if field_name and value is not None:
                        validated_value = self._validate_metric_value(pi_metric_name, value)
                        if validated_value is not None:
                            enhanced_metrics[field_name] = validated_value
                
                logger.debug(
                    f"SQL ID {sql_id}: Mapped {len(enhanced_metrics)} enhanced metrics"
                )
                
                # Build SQLQuery with enhanced metrics when available
                queries.append(SQLQuery(
                    query_id=sql_id,
                    query_text=sql_text,
                    total_execution_time=total_load,  # Total load (AAS)
                    average_execution_time=avg_load,  # Average load per time bucket
                    execution_count=time_buckets,  # Number of time buckets (NOT actual executions)
                    rows_affected=None,  # Not available in PI API
                    wait_events=wait_events,
                    # Enhanced optional fields (from AdditionalMetrics)
                    engine_type=engine,
                    executions_per_second=enhanced_metrics.get('executions_per_second'),
                    cpu_time=enhanced_metrics.get('cpu_time'),
                    lock_time=enhanced_metrics.get('lock_time'),
                    rows_examined=enhanced_metrics.get('rows_examined'),
                    rows_returned=enhanced_metrics.get('rows_returned'),
                    read_io_bytes=enhanced_metrics.get('read_io_bytes'),
                    write_io_bytes=enhanced_metrics.get('write_io_bytes'),
                    read_io_time=enhanced_metrics.get('read_io_time'),  # NEW - Aurora PG 17+
                    write_io_time=enhanced_metrics.get('write_io_time'),  # NEW - Aurora PG 17+
                    rows_per_second=enhanced_metrics.get('rows_per_second')  # NEW - Aurora PG 17+
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
        limit: int = 10,
        sql_queries: Optional[List['SQLQuery']] = None
    ) -> List[TopDatabase]:
        """
        Collect top databases by load.
        
        For MySQL/MariaDB: Uses PI API db.name dimension group
        For PostgreSQL: Extracts database names from SQL query text (fallback)
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for database data
            limit: Maximum number of databases to return
            sql_queries: Optional list of SQL queries (for PostgreSQL fallback)
            
        Returns:
            List of TopDatabase objects (empty list if not supported)
        """
        if not self.is_performance_insights_enabled(instance_id):
            logger.warning(
                f"Performance Insights not enabled for {instance_id}"
            )
            return []
        
        try:
            # Get resource ID for PI API
            resource_id = self.rds_client.get_instance_resource_id(instance_id)
            
            # Get engine type to check if db.name is supported
            engine = self.rds_client.get_instance_engine(instance_id)
            
            # db.name dimension group is not supported for Aurora PostgreSQL
            # Use fallback method: extract from SQL queries
            if 'postgres' in engine.lower():
                logger.info(
                    f"Using SQL query analysis for database load (db.name dimension not supported for {engine})"
                )
                
                # If SQL queries were provided, extract databases from them
                if sql_queries:
                    databases = self.extract_databases_from_queries(sql_queries)
                    return databases[:limit]
                else:
                    logger.info(
                        "No SQL queries provided for database extraction. "
                        "Top databases will not be available."
                    )
                    return []
            
            # For MySQL/MariaDB: Use PI API directly
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
                
                # Try multiple possible key names for database
                db_name = (
                    dimensions.get('db.name') or
                    dimensions.get('db.database') or
                    dimensions.get('db.database.name') or
                    key.get('db.name') or
                    'Unknown'
                )
                
                db_load = key.get('Total', 0.0)
                load_pct = (db_load / total_load * 100) if total_load > 0 else 0.0
                
                databases.append(TopDatabase(
                    database_name=db_name,
                    total_load=db_load,
                    load_percentage=load_pct
                ))
            
            logger.info(f"Collected {len(databases)} top databases from PI API")
            return databases
            
        except AWSClientError as e:
            # For PostgreSQL, try fallback if queries are available
            if sql_queries and 'postgres' in engine.lower():
                logger.info("Falling back to SQL query analysis for database load")
                databases = self.extract_databases_from_queries(sql_queries)
                return databases[:limit]
            
            # Log as info instead of error since this is expected for some engines
            logger.info(
                f"Top databases not available for {instance_id}: {e}. "
                "This is normal for Aurora PostgreSQL."
            )
            return []
        except Exception as e:
            logger.error(f"Unexpected error collecting top databases: {e}")
            return []
    
    def extract_databases_from_queries(
        self,
        queries: List['SQLQuery']
    ) -> List[TopDatabase]:
        """
        Extract database information from SQL queries for engines that don't support db.name.
        
        This is a workaround for Aurora PostgreSQL where the db.name dimension is not available.
        We parse the SQL query text to identify which databases are being accessed and
        aggregate the load by database.
        
        Args:
            queries: List of SQLQuery objects
            
        Returns:
            List of TopDatabase objects sorted by load
        """
        import re
        from collections import defaultdict
        import time
        
        start_time = time.time()
        
        # Dictionary to accumulate load per database
        db_loads = defaultdict(float)
        extracted_count = 0
        
        for query in queries:
            # Try to extract database name from SQL query text
            db_name = self._extract_database_from_sql(query.query_text)
            
            # Accumulate load for this database
            if db_name:
                db_loads[db_name] += query.total_execution_time
                extracted_count += 1
        
        elapsed = time.time() - start_time
        
        # If no databases found, return empty list
        if not db_loads:
            logger.info(
                f"No database names could be extracted from SQL queries "
                f"({len(queries)} queries analyzed in {elapsed:.2f}s)"
            )
            return []
        
        # Calculate total load for percentages
        total_load = sum(db_loads.values())
        
        # Convert to TopDatabase objects
        databases = []
        for db_name, load in sorted(db_loads.items(), key=lambda x: x[1], reverse=True):
            load_pct = (load / total_load * 100) if total_load > 0 else 0.0
            databases.append(TopDatabase(
                database_name=db_name,
                total_load=load,
                load_percentage=load_pct
            ))
        
        logger.info(
            f"Extracted {len(databases)} databases from {extracted_count}/{len(queries)} SQL queries "
            f"(total load: {total_load:.2f} AAS, time: {elapsed:.2f}s)"
        )
        return databases
    
    def _extract_database_from_sql(self, sql_text: str) -> Optional[str]:
        """
        Extract database name from SQL query text.
        
        Supports various SQL patterns:
        - FROM schema.table
        - JOIN schema.table
        - INSERT INTO schema.table
        - UPDATE schema.table
        - DELETE FROM schema.table
        - USE database
        - database.schema.table (3-part names)
        - WHERE datname = 'database' (PostgreSQL specific)
        
        Args:
            sql_text: SQL query text
            
        Returns:
            Database/schema name or None if not found
        """
        import re
        
        if not sql_text:
            return None
        
        # Convert to lowercase for case-insensitive matching
        sql_lower = sql_text.lower()
        
        # Pattern 1: PostgreSQL specific - WHERE datname = 'database_name'
        # Common in system queries
        datname_match = re.search(r"datname\s*=\s*['\"]([a-z_][a-z0-9_]*)['\"]", sql_lower)
        if datname_match:
            db_name = datname_match.group(1)
            # Filter out template databases
            if db_name not in ['template0', 'template1', 'rdsadmin', 'postgres']:
                return db_name
        
        # Pattern 2: USE database
        use_match = re.search(r'\buse\s+([a-z_][a-z0-9_]*)', sql_lower)
        if use_match:
            return use_match.group(1)
        
        # Pattern 3: schema.table or database.schema.table
        # Look for FROM, JOIN, INTO, UPDATE patterns
        patterns = [
            r'\bfrom\s+([a-z_][a-z0-9_]*)\.', 
            r'\bjoin\s+([a-z_][a-z0-9_]*)\.', 
            r'\binto\s+([a-z_][a-z0-9_]*)\.', 
            r'\bupdate\s+([a-z_][a-z0-9_]*)\.', 
        ]
        
        for pattern in patterns:
            match = re.search(pattern, sql_lower)
            if match:
                schema_or_db = match.group(1)
                # Filter out common PostgreSQL system schemas
                if schema_or_db not in ['pg_catalog', 'information_schema', 'pg_temp', 'pg_toast']:
                    return schema_or_db
        
        # Pattern 4: Look for database name in connection context
        # Some queries include database name in comments
        comment_match = re.search(r'/\*.*?database[:\s]+([a-z_][a-z0-9_]*).*?\*/', sql_lower)
        if comment_match:
            return comment_match.group(1)
        
        # If no database found, return None
        return None
    
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
                
                # Debug: Log the actual dimensions structure
                logger.debug(f"Top user dimension key structure: {key}")
                logger.debug(f"Dimensions: {dimensions}")
                
                # Try multiple possible key names for user
                user_name = (
                    dimensions.get('db.user') or 
                    dimensions.get('db.user.name') or
                    key.get('db.user') or
                    'Unknown'
                )
                
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

    def collect_os_metrics(
        self,
        instance_id: str,
        time_range: TimeRange
    ) -> Optional['OSMetrics']:
        """
        Collect OS-level performance metrics from Performance Insights.
        
        These metrics provide system-level insights including:
        - CPU utilization (total, user, system, I/O wait)
        - Memory usage (free, active, cached)
        - Disk I/O (IOPS, latency, throughput, queue depth)
        - Temp usage (blocks read/written)
        - Swap usage
        - Load average
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for metric collection
            
        Returns:
            OSMetrics object with collected metrics, or None if PI not enabled
        """
        from core.models import OSMetrics
        
        if not self.is_performance_insights_enabled(instance_id):
            logger.warning(
                f"Performance Insights not enabled for {instance_id}"
            )
            return None
        
        try:
            # Get resource ID for PI API
            resource_id = self.rds_client.get_instance_resource_id(instance_id)
            
            # Define OS metrics to collect (in smaller batches to avoid validation errors)
            os_metric_names = [
                # CPU metrics
                'os.cpuUtilization.total.avg',
                'os.cpuUtilization.user.avg',
                'os.cpuUtilization.system.avg',
                'os.cpuUtilization.wait.avg',  # I/O wait - key metric!
                
                # Memory metrics
                'os.memory.free.avg',
                'os.memory.active.avg',
                'os.memory.cached.avg',
                
                # Disk I/O metrics - THE KEY METRICS
                'os.diskIO.readIOsPS.avg',
                'os.diskIO.writeIOsPS.avg',
                'os.diskIO.readLatency.avg',
                'os.diskIO.writeLatency.avg',
                'os.diskIO.readKb.avg',
                'os.diskIO.writeKb.avg',
                'os.diskIO.diskQueueDepth.avg',
                'os.diskIO.await.avg',
                'os.diskIO.util.avg',
                
                # Load average
                'os.loadAverageMinute.one.avg',
                'os.loadAverageMinute.five.avg',
            ]
            
            # Build metric queries
            os_metric_queries = [{'Metric': name} for name in os_metric_names]
            
            logger.debug(f"Collecting {len(os_metric_queries)} OS metrics for {instance_id}")
            
            # Try to collect metrics - if validation fails, try individual metrics
            try:
                response = self.pi_client.get_resource_metrics(
                    resource_id=resource_id,
                    metric_queries=os_metric_queries,
                    start_time=time_range.start,
                    end_time=time_range.end
                )
            except AWSClientError as e:
                if "Validation error" in str(e):
                    logger.warning(f"Batch metric collection failed, trying individual metrics: {e}")
                    # Try collecting metrics individually
                    response = {'MetricList': []}
                    for metric_query in os_metric_queries:
                        try:
                            single_response = self.pi_client.get_resource_metrics(
                                resource_id=resource_id,
                                metric_queries=[metric_query],
                                start_time=time_range.start,
                                end_time=time_range.end
                            )
                            response['MetricList'].extend(single_response.get('MetricList', []))
                        except Exception as single_error:
                            logger.debug(f"Failed to collect {metric_query['Metric']}: {single_error}")
                            continue
                else:
                    raise
            
            # Parse response and extract average values
            metrics_data = {}
            
            for metric_data in response.get('MetricList', []):
                metric_key = metric_data.get('Key', {})
                metric_name = metric_key.get('Metric')
                
                if not metric_name:
                    continue
                
                # Get data points and calculate average
                data_points = metric_data.get('DataPoints', [])
                
                if not data_points:
                    logger.debug(f"No data points for OS metric '{metric_name}'")
                    continue
                
                # Calculate average across time range
                values = [dp.get('Value') for dp in data_points if 'Value' in dp]
                
                if values:
                    avg_value = sum(values) / len(values)
                    metrics_data[metric_name] = avg_value
                    logger.debug(f"OS metric '{metric_name}': {avg_value:.2f}")
            
            # Build OSMetrics object
            os_metrics = OSMetrics(
                # CPU metrics
                cpu_total=metrics_data.get('os.cpuUtilization.total.avg'),
                cpu_user=metrics_data.get('os.cpuUtilization.user.avg'),
                cpu_system=metrics_data.get('os.cpuUtilization.system.avg'),
                cpu_wait=metrics_data.get('os.cpuUtilization.wait.avg'),
                
                # Memory metrics (convert bytes to GB)
                memory_free_gb=self._bytes_to_gb(metrics_data.get('os.memory.free.avg')),
                memory_active_gb=self._bytes_to_gb(metrics_data.get('os.memory.active.avg')),
                memory_cached_gb=self._bytes_to_gb(metrics_data.get('os.memory.cached.avg')),
                
                # Disk I/O metrics
                read_iops=metrics_data.get('os.diskIO.readIOsPS.avg'),
                write_iops=metrics_data.get('os.diskIO.writeIOsPS.avg'),
                read_latency_ms=metrics_data.get('os.diskIO.readLatency.avg'),
                write_latency_ms=metrics_data.get('os.diskIO.writeLatency.avg'),
                read_throughput_kbps=metrics_data.get('os.diskIO.readKb.avg'),
                write_throughput_kbps=metrics_data.get('os.diskIO.writeKb.avg'),
                disk_queue_depth=metrics_data.get('os.diskIO.diskQueueDepth.avg'),
                disk_await_ms=metrics_data.get('os.diskIO.await.avg'),
                disk_utilization_pct=metrics_data.get('os.diskIO.util.avg'),
                
                # Temp usage
                temp_blocks_read=metrics_data.get('os.diskIO.tempBlksRead.avg'),
                temp_blocks_written=metrics_data.get('os.diskIO.tempBlksWritten.avg'),
                
                # Swap metrics (convert bytes to GB)
                swap_free_gb=self._bytes_to_gb(metrics_data.get('os.swap.free.avg')),
                swap_in_rate=metrics_data.get('os.swap.in.avg'),
                swap_out_rate=metrics_data.get('os.swap.out.avg'),
                
                # Load average
                load_avg_1min=metrics_data.get('os.loadAverageMinute.one.avg'),
                load_avg_5min=metrics_data.get('os.loadAverageMinute.five.avg'),
            )
            
            logger.info(f"Successfully collected OS metrics for {instance_id}")
            return os_metrics
            
        except AWSClientError as e:
            logger.error(f"Failed to collect OS metrics: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error collecting OS metrics: {e}")
            return None
    
    def _bytes_to_gb(self, bytes_value: Optional[float]) -> Optional[float]:
        """
        Convert bytes to gigabytes.
        
        Args:
            bytes_value: Value in bytes
            
        Returns:
            Value in GB, or None if input is None
        """
        if bytes_value is None:
            return None
        return bytes_value / (1024 ** 3)
