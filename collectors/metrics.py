"""CloudWatch metrics collector."""

import logging
from datetime import datetime
from typing import List

from aws.clients import CloudWatchClient, RDSClient, AWSClientError
from core.models import (
    TimeRange, MetricSeries, MetricDataPoint, IOPSMetrics,
    StorageMetrics, CloudWatchMetrics, RDSInstanceInfo
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects CloudWatch metrics for RDS instances."""
    
    def __init__(self, cloudwatch_client: CloudWatchClient, rds_client: RDSClient):
        """
        Initialize metrics collector.
        
        Args:
            cloudwatch_client: CloudWatch client wrapper
            rds_client: RDS client wrapper
        """
        self.cloudwatch_client = cloudwatch_client
        self.rds_client = rds_client
    
    def collect_cpu_metrics(
        self,
        instance_id: str,
        time_range: TimeRange
    ) -> MetricSeries:
        """
        Collect CPU utilization metrics.
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for metrics
            
        Returns:
            MetricSeries for CPU utilization
        """
        try:
            data_points = self.cloudwatch_client.get_metric_statistics(
                namespace='AWS/RDS',
                metric_name='CPUUtilization',
                dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': instance_id}],
                start_time=time_range.start,
                end_time=time_range.end,
                period=300,
                statistics=['Average']
            )
            
            return MetricSeries(
                metric_name='CPUUtilization',
                data_points=data_points,
                unit='Percent'
            )
        except AWSClientError as e:
            logger.error(f"Failed to collect CPU metrics: {e}")
            return MetricSeries(metric_name='CPUUtilization', data_points=[], unit='Percent')
    
    def collect_memory_metrics(
        self,
        instance_id: str,
        time_range: TimeRange
    ) -> MetricSeries:
        """
        Collect freeable memory metrics.
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for metrics
            
        Returns:
            MetricSeries for freeable memory
        """
        try:
            data_points = self.cloudwatch_client.get_metric_statistics(
                namespace='AWS/RDS',
                metric_name='FreeableMemory',
                dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': instance_id}],
                start_time=time_range.start,
                end_time=time_range.end,
                period=300,
                statistics=['Average']
            )
            
            return MetricSeries(
                metric_name='FreeableMemory',
                data_points=data_points,
                unit='Bytes'
            )
        except AWSClientError as e:
            logger.error(f"Failed to collect memory metrics: {e}")
            return MetricSeries(metric_name='FreeableMemory', data_points=[], unit='Bytes')
    
    def collect_connection_metrics(
        self,
        instance_id: str,
        time_range: TimeRange
    ) -> MetricSeries:
        """
        Collect database connection count metrics.
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for metrics
            
        Returns:
            MetricSeries for database connections
        """
        try:
            data_points = self.cloudwatch_client.get_metric_statistics(
                namespace='AWS/RDS',
                metric_name='DatabaseConnections',
                dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': instance_id}],
                start_time=time_range.start,
                end_time=time_range.end,
                period=300,
                statistics=['Average']
            )
            
            return MetricSeries(
                metric_name='DatabaseConnections',
                data_points=data_points,
                unit='Count'
            )
        except AWSClientError as e:
            logger.error(f"Failed to collect connection metrics: {e}")
            return MetricSeries(metric_name='DatabaseConnections', data_points=[], unit='Count')
    
    def collect_iops_metrics(
        self,
        instance_id: str,
        time_range: TimeRange
    ) -> IOPSMetrics:
        """
        Collect IOPS metrics (read and write).
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for metrics
            
        Returns:
            IOPSMetrics object
        """
        try:
            read_data_points = self.cloudwatch_client.get_metric_statistics(
                namespace='AWS/RDS',
                metric_name='ReadIOPS',
                dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': instance_id}],
                start_time=time_range.start,
                end_time=time_range.end,
                period=300,
                statistics=['Average']
            )
            
            write_data_points = self.cloudwatch_client.get_metric_statistics(
                namespace='AWS/RDS',
                metric_name='WriteIOPS',
                dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': instance_id}],
                start_time=time_range.start,
                end_time=time_range.end,
                period=300,
                statistics=['Average']
            )
            
            return IOPSMetrics(
                read_iops=MetricSeries(
                    metric_name='ReadIOPS',
                    data_points=read_data_points,
                    unit='Count/Second'
                ),
                write_iops=MetricSeries(
                    metric_name='WriteIOPS',
                    data_points=write_data_points,
                    unit='Count/Second'
                )
            )
        except AWSClientError as e:
            logger.error(f"Failed to collect IOPS metrics: {e}")
            return IOPSMetrics(
                read_iops=MetricSeries(metric_name='ReadIOPS', data_points=[], unit='Count/Second'),
                write_iops=MetricSeries(metric_name='WriteIOPS', data_points=[], unit='Count/Second')
            )
    
    def collect_storage_metrics(
        self,
        instance_id: str,
        time_range: TimeRange
    ) -> StorageMetrics:
        """
        Collect storage metrics.
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for metrics
            
        Returns:
            StorageMetrics object
        """
        try:
            # Get free storage space
            free_data_points = self.cloudwatch_client.get_metric_statistics(
                namespace='AWS/RDS',
                metric_name='FreeStorageSpace',
                dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': instance_id}],
                start_time=time_range.start,
                end_time=time_range.end,
                period=300,
                statistics=['Average']
            )
            
            # Get instance details for total storage
            instance_data = self.rds_client.describe_instance(instance_id)
            allocated_storage_gb = instance_data.get('AllocatedStorage', 0)
            total_storage_bytes = allocated_storage_gb * 1024 * 1024 * 1024
            
            # Calculate used storage from free storage
            used_data_points = []
            for dp in free_data_points:
                used_value = total_storage_bytes - dp.value
                used_data_points.append(
                    MetricDataPoint(
                        timestamp=dp.timestamp,
                        value=used_value,
                        unit='Bytes'
                    )
                )
            
            return StorageMetrics(
                free_storage=MetricSeries(
                    metric_name='FreeStorageSpace',
                    data_points=free_data_points,
                    unit='Bytes'
                ),
                used_storage=MetricSeries(
                    metric_name='UsedStorageSpace',
                    data_points=used_data_points,
                    unit='Bytes'
                ),
                total_storage=total_storage_bytes
            )
        except AWSClientError as e:
            logger.error(f"Failed to collect storage metrics: {e}")
            return StorageMetrics(
                free_storage=MetricSeries(metric_name='FreeStorageSpace', data_points=[], unit='Bytes'),
                used_storage=MetricSeries(metric_name='UsedStorageSpace', data_points=[], unit='Bytes'),
                total_storage=0
            )
    
    def collect_all_metrics(
        self,
        instance_id: str,
        time_range: TimeRange,
        instance_info: RDSInstanceInfo
    ) -> CloudWatchMetrics:
        """
        Collect all CloudWatch metrics for an instance.
        
        Args:
            instance_id: RDS instance identifier
            time_range: Time range for metrics
            instance_info: RDS instance information
            
        Returns:
            CloudWatchMetrics object with all metrics
        """
        logger.info(f"Collecting all metrics for instance {instance_id}")
        
        cpu = self.collect_cpu_metrics(instance_id, time_range)
        memory = self.collect_memory_metrics(instance_id, time_range)
        connections = self.collect_connection_metrics(instance_id, time_range)
        iops = self.collect_iops_metrics(instance_id, time_range)
        storage = self.collect_storage_metrics(instance_id, time_range)
        
        return CloudWatchMetrics(
            instance_info=instance_info,
            cpu_utilization=cpu,
            freeable_memory=memory,
            database_connections=connections,
            iops=iops,
            storage=storage,
            collection_time=datetime.now()
        )
