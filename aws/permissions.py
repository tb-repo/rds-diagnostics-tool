"""Permission validation for AWS services."""

import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class PermissionCheck:
    """Represents a permission check result."""
    service: str
    action: str
    required: bool
    has_permission: bool
    error_message: str = ""


class PermissionValidator:
    """Validates IAM permissions for RDS diagnostics operations."""
    
    # Required permissions for core functionality
    REQUIRED_PERMISSIONS = [
        ("rds", "DescribeDBInstances"),
        ("cloudwatch", "GetMetricStatistics"),
    ]
    
    # Optional permissions for enhanced functionality
    OPTIONAL_PERMISSIONS = [
        ("pi", "GetResourceMetrics"),
        ("pi", "DescribeDimensionKeys"),
    ]
    
    def __init__(self, profile: str = None, region: str = "ap-southeast-1"):
        """
        Initialize permission validator.
        
        Args:
            profile: AWS profile name
            region: AWS region
        """
        self.profile = profile
        self.region = region
        self.session = self._create_session()
    
    def _create_session(self) -> boto3.Session:
        """Create boto3 session with profile."""
        if self.profile:
            return boto3.Session(profile_name=self.profile, region_name=self.region)
        return boto3.Session(region_name=self.region)
    
    def check_rds_permissions(self) -> Tuple[bool, List[str]]:
        """
        Check RDS permissions by attempting to list instances.
        
        Returns:
            Tuple of (has_permission, missing_permissions)
        """
        missing = []
        
        try:
            rds_client = self.session.client('rds')
            # Try to list instances with a limit to minimize API calls
            rds_client.describe_db_instances(MaxRecords=20)
            logger.debug("RDS DescribeDBInstances permission verified")
            return True, []
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                missing.append("rds:DescribeDBInstances")
                logger.warning("Missing RDS DescribeDBInstances permission")
            elif error_code == 'InvalidClientTokenId':
                missing.append("Invalid AWS credentials")
            else:
                logger.error(f"Error checking RDS permissions: {e}")
                missing.append(f"RDS permission check failed: {error_code}")
            
            return False, missing
        except Exception as e:
            logger.error(f"Unexpected error checking RDS permissions: {e}")
            return False, [f"RDS permission check error: {str(e)}"]
    
    def check_cloudwatch_permissions(self) -> Tuple[bool, List[str]]:
        """
        Check CloudWatch permissions by attempting to get metric statistics.
        
        Returns:
            Tuple of (has_permission, missing_permissions)
        """
        missing = []
        
        try:
            from datetime import datetime, timedelta
            
            cloudwatch_client = self.session.client('cloudwatch')
            
            # Try a minimal GetMetricStatistics call
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            logger.debug("CloudWatch GetMetricStatistics permission verified")
            return True, []
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                missing.append("cloudwatch:GetMetricStatistics")
                logger.warning("Missing CloudWatch GetMetricStatistics permission")
            else:
                logger.error(f"Error checking CloudWatch permissions: {e}")
                missing.append(f"CloudWatch permission check failed: {error_code}")
            
            return False, missing
        except Exception as e:
            logger.error(f"Unexpected error checking CloudWatch permissions: {e}")
            return False, [f"CloudWatch permission check error: {str(e)}"]
    
    def check_performance_insights_permissions(self) -> Tuple[bool, List[str]]:
        """
        Check Performance Insights permissions.
        
        Returns:
            Tuple of (has_permission, missing_permissions)
        """
        missing = []
        
        try:
            pi_client = self.session.client('pi')
            
            # Try a minimal call - this will fail if no resources exist,
            # but we can detect permission issues
            from datetime import datetime, timedelta
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            # This call will fail with AccessDenied if no permission
            # or with InvalidParameterValue if permission exists but no resource
            pi_client.get_resource_metrics(
                ServiceType='RDS',
                Identifier='db-NONEXISTENT',  # Intentionally invalid
                MetricQueries=[
                    {
                        'Metric': 'db.load.avg'
                    }
                ],
                StartTime=start_time,
                EndTime=end_time
            )
            # If we get here, we have permission
            logger.debug("Performance Insights permissions verified")
            return True, []
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                missing.append("pi:GetResourceMetrics")
                missing.append("pi:DescribeDimensionKeys")
                logger.info("Missing Performance Insights permissions (optional)")
                return False, missing
            elif error_code in ['InvalidParameterValue', 'InvalidResourceId']:
                # Permission exists, just invalid resource (expected)
                logger.debug("Performance Insights permissions verified (via error)")
                return True, []
            else:
                logger.debug(f"Performance Insights check inconclusive: {error_code}")
                # Inconclusive - assume no permission
                return False, ["pi:GetResourceMetrics (unable to verify)"]
        except Exception as e:
            logger.debug(f"Performance Insights check error: {e}")
            return False, ["pi:GetResourceMetrics (unable to verify)"]
    
    def validate_all_permissions(self) -> Dict[str, any]:
        """
        Validate all required and optional permissions.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'has_required_permissions': True,
            'missing_required': [],
            'missing_optional': [],
            'checks': []
        }
        
        # Check RDS permissions (required)
        rds_ok, rds_missing = self.check_rds_permissions()
        results['checks'].append({
            'service': 'RDS',
            'required': True,
            'has_permission': rds_ok,
            'missing': rds_missing
        })
        
        if not rds_ok:
            results['has_required_permissions'] = False
            results['missing_required'].extend(rds_missing)
        
        # Check CloudWatch permissions (required)
        cw_ok, cw_missing = self.check_cloudwatch_permissions()
        results['checks'].append({
            'service': 'CloudWatch',
            'required': True,
            'has_permission': cw_ok,
            'missing': cw_missing
        })
        
        if not cw_ok:
            results['has_required_permissions'] = False
            results['missing_required'].extend(cw_missing)
        
        # Check Performance Insights permissions (optional)
        pi_ok, pi_missing = self.check_performance_insights_permissions()
        results['checks'].append({
            'service': 'Performance Insights',
            'required': False,
            'has_permission': pi_ok,
            'missing': pi_missing
        })
        
        if not pi_ok:
            results['missing_optional'].extend(pi_missing)
        
        return results
    
    def get_required_permissions_policy(self) -> Dict:
        """
        Get the IAM policy document for required permissions.
        
        Returns:
            IAM policy document as dictionary
        """
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "rds:DescribeDBInstances",
                        "rds:DescribeDBClusters",
                        "cloudwatch:GetMetricStatistics",
                        "cloudwatch:GetMetricData",
                        "pi:DescribeDimensionKeys",
                        "pi:GetResourceMetrics"
                    ],
                    "Resource": "*"
                }
            ]
        }
