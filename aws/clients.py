"""AWS service client wrappers with error handling and retry logic."""

import boto3
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from botocore.exceptions import ClientError, BotoCoreError

from core.models import MetricDataPoint

logger = logging.getLogger(__name__)


class AWSClientError(Exception):
    """Base exception for AWS client errors."""
    pass


class AuthenticationError(AWSClientError):
    """Authentication or authorization error."""
    pass


class ResourceNotFoundError(AWSClientError):
    """Requested resource not found."""
    pass


class RateLimitError(AWSClientError):
    """API rate limit exceeded."""
    pass


class AWSClientFactory:
    """Factory for creating AWS service clients."""
    
    def __init__(self, profile: Optional[str] = None, region: str = "ap-southeast-1"):
        """
        Initialize AWS client factory.
        
        Args:
            profile: AWS CLI profile name (None for default)
            region: AWS region
        """
        self.profile = profile
        self.region = region
        self.session = self._create_session()
    
    def _create_session(self) -> boto3.Session:
        """Create boto3 session with profile."""
        try:
            if self.profile:
                session = boto3.Session(profile_name=self.profile, region_name=self.region)
                logger.info(f"Created AWS session with profile: {self.profile}")
            else:
                session = boto3.Session(region_name=self.region)
                logger.info("Created AWS session with default profile")
            return session
        except Exception as e:
            raise AuthenticationError(
                f"Failed to create AWS session: {str(e)}\n"
                f"Suggestion: Verify AWS profile '{self.profile}' exists and credentials are valid"
            )
    
    def create_rds_client(self) -> "RDSClient":
        """Create RDS client."""
        return RDSClient(self.session)
    
    def create_cloudwatch_client(self) -> "CloudWatchClient":
        """Create CloudWatch client."""
        return CloudWatchClient(self.session)
    
    def create_performance_insights_client(self) -> "PerformanceInsightsClient":
        """Create Performance Insights client."""
        return PerformanceInsightsClient(self.session)


class BaseAWSClient:
    """Base class for AWS clients with retry logic."""
    
    MAX_RETRIES = 5
    BASE_DELAY = 1.0  # seconds
    
    def __init__(self, session: boto3.Session, service_name: str):
        """
        Initialize base AWS client.
        
        Args:
            session: boto3 session
            service_name: AWS service name (e.g., 'rds', 'cloudwatch')
        """
        self.session = session
        self.service_name = service_name
        self.client = session.client(service_name)
    
    def _execute_with_retry(self, operation: str, **kwargs) -> Any:
        """
        Execute AWS API call with exponential backoff retry.
        
        Args:
            operation: API operation name
            **kwargs: Operation parameters
            
        Returns:
            API response
            
        Raises:
            AuthenticationError: Authentication/authorization failed
            RateLimitError: Rate limit exceeded after retries
            AWSClientError: Other AWS errors
        """
        last_exception = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                method = getattr(self.client, operation)
                response = method(**kwargs)
                
                if attempt > 0:
                    logger.info(f"Retry succeeded for {operation} on attempt {attempt + 1}")
                
                return response
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                
                # Authentication/Authorization errors - don't retry
                if error_code in ['AccessDenied', 'UnauthorizedOperation', 'InvalidClientTokenId']:
                    raise AuthenticationError(
                        f"Authentication failed: {e.response['Error']['Message']}\n"
                        f"Suggestion: Check AWS credentials and IAM permissions"
                    )
                
                # Rate limiting - retry with backoff
                if error_code in ['Throttling', 'ThrottlingException', 'RequestLimitExceeded']:
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.BASE_DELAY * (2 ** attempt)
                        logger.warning(
                            f"Rate limited on {operation}, retrying in {delay}s "
                            f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                        )
                        time.sleep(delay)
                        last_exception = e
                        continue
                    else:
                        raise RateLimitError(
                            f"Rate limit exceeded after {self.MAX_RETRIES} retries\n"
                            f"Suggestion: Wait a few minutes and try again"
                        )
                
                # Resource not found - don't retry
                if error_code in ['DBInstanceNotFound', 'ResourceNotFoundException']:
                    raise ResourceNotFoundError(
                        f"Resource not found: {e.response['Error']['Message']}"
                    )
                
                # Transient errors - retry
                if error_code in ['ServiceUnavailable', 'InternalFailure']:
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.BASE_DELAY * (2 ** attempt)
                        logger.warning(
                            f"Transient error on {operation}, retrying in {delay}s "
                            f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                        )
                        time.sleep(delay)
                        last_exception = e
                        continue
                
                # Other errors - raise immediately
                raise AWSClientError(
                    f"AWS API error: {e.response['Error']['Message']}"
                )
                
            except BotoCoreError as e:
                # Network or other boto errors - retry
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Network error on {operation}, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)
                    last_exception = e
                    continue
                else:
                    raise AWSClientError(f"Network error: {str(e)}")
        
        # If we exhausted retries
        if last_exception:
            raise AWSClientError(
                f"Operation failed after {self.MAX_RETRIES} retries: {str(last_exception)}"
            )


class RDSClient(BaseAWSClient):
    """RDS service client wrapper."""
    
    def __init__(self, session: boto3.Session):
        """Initialize RDS client."""
        super().__init__(session, 'rds')
    
    def list_instances(self) -> List[Dict]:
        """
        List all RDS instances.
        
        Returns:
            List of RDS instance descriptions
        """
        try:
            response = self._execute_with_retry('describe_db_instances')
            return response.get('DBInstances', [])
        except AWSClientError:
            raise
        except Exception as e:
            raise AWSClientError(f"Failed to list RDS instances: {str(e)}")
    
    def describe_instance(self, instance_id: str) -> Dict:
        """
        Get details for a specific RDS instance.
        
        Args:
            instance_id: RDS instance identifier
            
        Returns:
            Instance description dictionary
        """
        try:
            response = self._execute_with_retry(
                'describe_db_instances',
                DBInstanceIdentifier=instance_id
            )
            instances = response.get('DBInstances', [])
            
            if not instances:
                raise ResourceNotFoundError(
                    f"RDS instance not found: {instance_id}\n"
                    f"Suggestion: Verify instance ID and region"
                )
            
            return instances[0]
            
        except ResourceNotFoundError:
            raise
        except AWSClientError:
            raise
        except Exception as e:
            raise AWSClientError(f"Failed to describe instance {instance_id}: {str(e)}")
    
    def get_instance_resource_id(self, instance_id: str) -> str:
        """
        Get the resource ID (DbiResourceId) for Performance Insights.
        
        Args:
            instance_id: RDS instance identifier
            
        Returns:
            Resource ID string
        """
        instance = self.describe_instance(instance_id)
        resource_id = instance.get('DbiResourceId')
        
        if not resource_id:
            raise AWSClientError(
                f"Could not retrieve resource ID for instance {instance_id}"
            )
        
        return resource_id


class CloudWatchClient(BaseAWSClient):
    """CloudWatch service client wrapper."""
    
    def __init__(self, session: boto3.Session):
        """Initialize CloudWatch client."""
        super().__init__(session, 'cloudwatch')
    
    def get_metric_statistics(
        self,
        namespace: str,
        metric_name: str,
        dimensions: List[Dict],
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
        statistics: List[str] = None
    ) -> List[MetricDataPoint]:
        """
        Get metric statistics from CloudWatch.
        
        Args:
            namespace: CloudWatch namespace (e.g., 'AWS/RDS')
            metric_name: Metric name
            dimensions: Metric dimensions
            start_time: Start of time range
            end_time: End of time range
            period: Period in seconds (default 300 = 5 minutes)
            statistics: List of statistics to retrieve (default ['Average'])
            
        Returns:
            List of MetricDataPoint objects
        """
        if statistics is None:
            statistics = ['Average']
        
        try:
            response = self._execute_with_retry(
                'get_metric_statistics',
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=statistics
            )
            
            datapoints = response.get('Datapoints', [])
            
            # Convert to MetricDataPoint objects
            result = []
            for dp in datapoints:
                # Use the first available statistic
                value = None
                unit = dp.get('Unit', 'None')
                
                for stat in statistics:
                    if stat in dp:
                        value = dp[stat]
                        break
                
                if value is not None:
                    result.append(MetricDataPoint(
                        timestamp=dp['Timestamp'],
                        value=float(value),
                        unit=unit
                    ))
            
            # Sort by timestamp
            result.sort(key=lambda x: x.timestamp)
            
            return result
            
        except AWSClientError:
            raise
        except Exception as e:
            raise AWSClientError(
                f"Failed to get metric {metric_name}: {str(e)}"
            )


class PerformanceInsightsClient(BaseAWSClient):
    """Performance Insights service client wrapper."""
    
    def __init__(self, session: boto3.Session):
        """Initialize Performance Insights client."""
        super().__init__(session, 'pi')
    
    def get_resource_metrics(
        self,
        resource_id: str,
        metric_queries: List[Dict],
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """
        Get resource metrics from Performance Insights.
        
        Args:
            resource_id: RDS resource ID
            metric_queries: List of metric query specifications
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Metrics response dictionary
        """
        try:
            response = self._execute_with_retry(
                'get_resource_metrics',
                ServiceType='RDS',
                Identifier=resource_id,
                MetricQueries=metric_queries,
                StartTime=start_time,
                EndTime=end_time
            )
            return response
            
        except AWSClientError:
            raise
        except Exception as e:
            raise AWSClientError(
                f"Failed to get Performance Insights metrics: {str(e)}"
            )
    
    def describe_dimension_keys(
        self,
        resource_id: str,
        group_by: str,
        start_time: datetime,
        end_time: datetime,
        metric: str = 'db.load.avg'
    ) -> List[Dict]:
        """
        Get dimension keys (e.g., top SQL queries) from Performance Insights.
        
        Args:
            resource_id: RDS resource ID
            group_by: Dimension to group by (e.g., 'db.sql')
            start_time: Start of time range
            end_time: End of time range
            metric: Metric to analyze (default 'db.load.avg')
            
        Returns:
            List of dimension key dictionaries
        """
        try:
            response = self._execute_with_retry(
                'describe_dimension_keys',
                ServiceType='RDS',
                Identifier=resource_id,
                StartTime=start_time,
                EndTime=end_time,
                Metric=metric,
                GroupBy={'Group': group_by}
            )
            return response.get('Keys', [])
            
        except AWSClientError:
            raise
        except Exception as e:
            raise AWSClientError(
                f"Failed to describe dimension keys: {str(e)}"
            )
