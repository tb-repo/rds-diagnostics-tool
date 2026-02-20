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
        Get actual max_connections value from parameter group.
        
        Args:
            instance_data: Raw instance data from AWS API
            
        Returns:
            Actual max connections from parameter group, or 0 if unavailable
        """
        try:
            # Get parameter group name
            param_groups = instance_data.get('DBParameterGroups', [])
            if not param_groups:
                logger.warning("No parameter groups found for instance")
                return 0
            
            param_group_name = param_groups[0].get('DBParameterGroupName')
            if not param_group_name:
                logger.warning("Parameter group name not found")
                return 0
            
            # Query max_connections parameter
            max_conn_value = self.rds_client.get_db_parameter_value(
                parameter_group_name=param_group_name,
                parameter_name='max_connections'
            )
            
            if max_conn_value:
                # Handle formula-based values (e.g., "{DBInstanceClassMemory/12582880}")
                if '{' in max_conn_value:
                    # For Aurora and some RDS engines, max_connections is calculated
                    # We'll return 0 to indicate it's dynamic
                    logger.info(
                        f"max_connections uses formula: {max_conn_value}"
                    )
                    return 0
                
                try:
                    return int(max_conn_value)
                except ValueError:
                    logger.warning(
                        f"Could not parse max_connections value: {max_conn_value}"
                    )
                    return 0
            else:
                logger.warning("max_connections parameter not found")
                return 0
                
        except Exception as e:
            logger.warning(f"Failed to get max_connections: {str(e)}")
            return 0
