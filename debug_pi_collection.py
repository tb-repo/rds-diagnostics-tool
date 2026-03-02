#!/usr/bin/env python3
"""Debug script to test Performance Insights collection."""

import logging
from datetime import datetime, timedelta
from core.config import Configuration
from core.models import TimeRange
from aws.clients import AWSClientFactory
from collectors.performance_insights import PerformanceInsightsCollector

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    # Configuration
    instance_id = 'ielts-ses-sit-v1-clusterinstance1'
    profile = 'LT-SIT'
    region = 'ap-southeast-1'
    
    logger.info(f"Testing PI collection for {instance_id}")
    logger.info(f"Profile: {profile}, Region: {region}")
    
    # Create clients
    factory = AWSClientFactory(profile=profile, region=region)
    rds_client = factory.create_rds_client()
    pi_client = factory.create_performance_insights_client()
    
    # Create collector
    collector = PerformanceInsightsCollector(pi_client, rds_client)
    
    # Create time range (last 24 hours)
    time_range = TimeRange.from_duration('24h')
    logger.info(f"Time range: {time_range.start} to {time_range.end}")
    
    # Test 1: Check if PI is enabled
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Check if Performance Insights is enabled")
    logger.info("="*80)
    is_enabled = collector.is_performance_insights_enabled(instance_id)
    logger.info(f"Performance Insights enabled: {is_enabled}")
    
    if not is_enabled:
        logger.error("Performance Insights is not enabled. Exiting.")
        return
    
    # Test 2: Get resource ID
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Get resource ID")
    logger.info("="*80)
    resource_id = rds_client.get_instance_resource_id(instance_id)
    logger.info(f"Resource ID: {resource_id}")
    
    # Test 3: Get instance details
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Get instance details")
    logger.info("="*80)
    instance_data = rds_client.describe_instance(instance_id)
    engine = instance_data.get('Engine', 'unknown')
    logger.info(f"Engine: {engine}")
    logger.info(f"Engine Version: {instance_data.get('EngineVersion', 'unknown')}")
    
    # Test 4: Try describe_dimension_keys WITHOUT additional_metrics
    logger.info("\n" + "="*80)
    logger.info("TEST 4: describe_dimension_keys WITHOUT additional_metrics")
    logger.info("="*80)
    try:
        keys = pi_client.describe_dimension_keys(
            resource_id=resource_id,
            group_by='db.sql',
            start_time=time_range.start,
            end_time=time_range.end,
            metric='db.load.avg'
        )
        logger.info(f"SUCCESS: Got {len(keys)} dimension keys")
        if keys:
            logger.info(f"First key structure: {keys[0]}")
            logger.info(f"First key Dimensions: {keys[0].get('Dimensions', {})}")
            logger.info(f"First key Total: {keys[0].get('Total', 0)}")
            logger.info(f"First key has AdditionalMetrics: {'AdditionalMetrics' in keys[0]}")
        else:
            logger.warning("No SQL queries found in the time range")
    except Exception as e:
        logger.error(f"FAILED: {e}", exc_info=True)
    
    # Test 5: Try describe_dimension_keys WITH additional_metrics
    logger.info("\n" + "="*80)
    logger.info("TEST 5: describe_dimension_keys WITH additional_metrics")
    logger.info("="*80)
    
    # Get engine-specific metrics
    metric_config = collector._get_engine_metrics_config(engine)
    additional_metrics = []
    for category, metric_names in metric_config.items():
        additional_metrics.extend(metric_names)
    
    logger.info(f"Requesting additional metrics: {additional_metrics}")
    
    try:
        keys = pi_client.describe_dimension_keys(
            resource_id=resource_id,
            group_by='db.sql',
            start_time=time_range.start,
            end_time=time_range.end,
            metric='db.load.avg',
            additional_metrics=additional_metrics
        )
        logger.info(f"SUCCESS: Got {len(keys)} dimension keys with additional metrics")
        if keys:
            logger.info(f"First key structure: {keys[0]}")
            logger.info(f"First key AdditionalMetrics: {keys[0].get('AdditionalMetrics', {})}")
        else:
            logger.warning("No SQL queries found in the time range")
    except Exception as e:
        logger.error(f"FAILED: {e}", exc_info=True)
    
    # Test 6: Try collect_top_sql_queries
    logger.info("\n" + "="*80)
    logger.info("TEST 6: collect_top_sql_queries")
    logger.info("="*80)
    try:
        queries = collector.collect_top_sql_queries(
            instance_id=instance_id,
            time_range=time_range,
            limit=10
        )
        logger.info(f"SUCCESS: Collected {len(queries)} SQL queries")
        for i, query in enumerate(queries[:3], 1):
            logger.info(f"\nQuery {i}:")
            logger.info(f"  ID: {query.query_id}")
            logger.info(f"  Text: {query.query_text[:100]}...")
            logger.info(f"  Total Load: {query.total_execution_time}")
            logger.info(f"  Executions/sec: {query.executions_per_second}")
            logger.info(f"  CPU Time: {query.cpu_time}")
            logger.info(f"  Rows Returned: {query.rows_returned}")
    except Exception as e:
        logger.error(f"FAILED: {e}", exc_info=True)
    
    # Test 7: Try collect_top_users
    logger.info("\n" + "="*80)
    logger.info("TEST 7: collect_top_users")
    logger.info("="*80)
    try:
        users = collector.collect_top_users(
            instance_id=instance_id,
            time_range=time_range,
            limit=10
        )
        logger.info(f"SUCCESS: Collected {len(users)} top users")
        for i, user in enumerate(users[:3], 1):
            logger.info(f"  User {i}: {user.user_name} - Load: {user.total_load:.2f} AAS ({user.load_percentage:.1f}%)")
    except Exception as e:
        logger.error(f"FAILED: {e}", exc_info=True)
    
    # Test 8: Try collect_top_databases
    logger.info("\n" + "="*80)
    logger.info("TEST 8: collect_top_databases")
    logger.info("="*80)
    try:
        databases = collector.collect_top_databases(
            instance_id=instance_id,
            time_range=time_range,
            limit=10
        )
        logger.info(f"SUCCESS: Collected {len(databases)} top databases")
        for i, db in enumerate(databases[:3], 1):
            logger.info(f"  Database {i}: {db.database_name} - Load: {db.total_load:.2f} AAS ({db.load_percentage:.1f}%)")
    except Exception as e:
        logger.error(f"FAILED: {e}", exc_info=True)

if __name__ == '__main__':
    main()
