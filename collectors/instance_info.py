"""Instance information collector."""

import logging
from typing import List

from aws.clients import RDSClient, AWSClientError
from core.models import RDSInstanceInfo

logger = logging.getLogger(__name__)


class InstanceInfoCollector:
    """Collects RDS instance information."""
    
    def __init__(self, rds_client: RDSClient):
        """
        Initialize instance info collector.
        
        Args:
            rds_client: RDS client wrapper
        """
        self.rds_client = rds_client
    
    def get_instance_details(self, instance_id: str) -> RDSInstanceInfo:
        """
        Get detailed information for a specific RDS instance.
        
        Args:
            instance_id: RDS instance identifier
            
        Returns:
            RDSInstanceInfo object
            
        Raises:
            AWSClientError: If instance cannot be retrieved
        """
        try:
            instance_data = self.rds_client.describe_instance(instance_id)
            return self._parse_instance_data(instance_data)
        except AWSClientError:
            raise
        except Exception as e:
            raise AWSClientError(
                f"Failed to get instance details for {instance_id}: {str(e)}"
            )
    
    def list_all_instances(self) -> List[RDSInstanceInfo]:
        """
        List all RDS instances in the current region.
        
        Returns:
            List of RDSInstanceInfo objects
            
        Raises:
            AWSClientError: If instances cannot be listed
        """
        try:
            instances_data = self.rds_client.list_instances()
            return [self._parse_instance_data(data) for data in instances_data]
        except AWSClientError:
            raise
        except Exception as e:
            raise AWSClientError(f"Failed to list instances: {str(e)}")
    
    def _parse_instance_data(self, instance_data: dict) -> RDSInstanceInfo:
        """
        Parse AWS API response into RDSInstanceInfo object.
        
        Args:
            instance_data: Raw instance data from AWS API
            
        Returns:
            RDSInstanceInfo object
        """
        # Extract max_connections from parameter group or use default
        max_connections = self._get_max_connections(instance_data)
        
        return RDSInstanceInfo(
            instance_id=instance_data.get('DBInstanceIdentifier', ''),
            resource_id=instance_data.get('DbiResourceId', ''),
            engine=instance_data.get('Engine', ''),
            engine_version=instance_data.get('EngineVersion', ''),
            instance_class=instance_data.get('DBInstanceClass', ''),
            status=instance_data.get('DBInstanceStatus', ''),
            storage_type=instance_data.get('StorageType', ''),
            allocated_storage=instance_data.get('AllocatedStorage', 0),
            max_connections=max_connections,
            availability_zone=instance_data.get('AvailabilityZone', '')
        )
    
    def _get_max_connections(self, instance_data: dict) -> int:
        """
        Estimate max_connections based on instance class.
        
        This is an approximation since the actual value depends on
        the parameter group configuration.
        
        Args:
            instance_data: Raw instance data from AWS API
            
        Returns:
            Estimated max connections
        """
        # Try to get from endpoint if available
        # Otherwise estimate based on instance class
        instance_class = instance_data.get('DBInstanceClass', '')
        
        # Basic estimation based on common patterns
        # In production, this should query the parameter group
        if 'micro' in instance_class or 't2.micro' in instance_class:
            return 66
        elif 't2.small' in instance_class or 't3.small' in instance_class:
            return 150
        elif 't2.medium' in instance_class or 't3.medium' in instance_class:
            return 296
        elif 'large' in instance_class:
            return 1000
        elif 'xlarge' in instance_class:
            return 2000
        else:
            # Default conservative estimate
            return 500
