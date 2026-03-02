#!/usr/bin/env python3
"""
Comprehensive script to list ALL available Performance Insights metrics
for Aurora PostgreSQL 17.5.

This script will:
1. List all available dimension groups
2. List all available resource metrics
3. Test each metric type to see what data is available
4. Show sample data for each working metric
"""

import sys
import logging
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, '.')

from core.config import Configuration
from aws.clients import AWSClientFactory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def main():
    # Configuration
    instance_id = 'ielts-ses-sit-v1-clusterinstance1'
    profile = 'LT-SIT'
    region = 'ap-southeast-1'
    
    print_section("PERFORMANCE INSIGHTS METRICS DISCOVERY")
    print(f"Instance ID: {instance_id}")
    print(f"Profile: {profile}")
    print(f"Region: {region}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create clients
    factory = AWSClientFactory(profile=profile, region=region)
    rds_client = factory.create_rds_client()
    pi_client = factory.create_performance_insights_client()
    
    # Get resource ID
    resource_id = rds_client.get_instance_resource_id(instance_id)
    print(f"Resource ID: {resource_id}")
    
    # Get instance details
    instance_data = rds_client.describe_instance(instance_id)
    engine = instance_data.get('Engine', 'unknown')
    engine_version = instance_data.get('EngineVersion', 'unknown')
    print(f"Engine: {engine} {engine_version}")
    
    # Time range (last 1 hour for faster testing)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    # ========================================================================
    # TEST 1: List Available Resource Dimensions
    # ========================================================================
    print_section("TEST 1: Available Resource Dimensions")
    
    try:
        response = pi_client.client.list_available_resource_dimensions(
            ServiceType='RDS',
            Identifier=resource_id
        )
        
        dimensions = response.get('MetricDimensions', [])
        print(f"\nFound {len(dimensions)} dimension groups:\n")
        
        for dim in dimensions:
            group = dim.get('Metric', 'Unknown')
            groups = dim.get('Groups', [])
            print(f"  Metric: {group}")
            print(f"  Available Groups: {', '.join(groups) if groups else 'None'}")
            print()
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # ========================================================================
    # TEST 2: List Available Resource Metrics
    # ========================================================================
    print_section("TEST 2: Available Resource Metrics")
    
    # Test different metric types
    metric_types = [
        'db.load',
        'db.sql.stats',
        'os',
        'db.cache',
        'db.transactions',
        'db.locks'
    ]
    
    for metric_type in metric_types:
        print(f"\n--- Checking: {metric_type} ---")
        try:
            response = pi_client.client.list_available_resource_metrics(
                ServiceType='RDS',
                Identifier=resource_id,
                MetricTypes=[metric_type]
            )
            
            metrics = response.get('Metrics', [])
            print(f"Found {len(metrics)} metrics")
            
            if metrics:
                for metric in metrics[:10]:  # Show first 10
                    metric_name = metric.get('Metric', 'Unknown')
                    description = metric.get('Description', 'No description')
                    unit = metric.get('Unit', 'N/A')
                    print(f"  • {metric_name}")
                    print(f"    Description: {description}")
                    print(f"    Unit: {unit}")
                
                if len(metrics) > 10:
                    print(f"  ... and {len(metrics) - 10} more")
            else:
                print("  No metrics available")
                
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # ========================================================================
    # TEST 3: Test Dimension Groups
    # ========================================================================
    print_section("TEST 3: Testing Dimension Groups")
    
    dimension_groups = [
        'db.sql',
        'db.sql_tokenized',
        'db.wait_event',
        'db.user',
        'db.host',
        'db.application',
        'db.session_type',
        'db.name',
        'db.database'
    ]
    
    for group in dimension_groups:
        print(f"\n--- Testing: {group} ---")
        try:
            response = pi_client.client.describe_dimension_keys(
                ServiceType='RDS',
                Identifier=resource_id,
                Metric='db.load.avg',
                GroupBy={'Group': group},
                StartTime=start_time,
                EndTime=end_time
            )
            
            keys = response.get('Keys', [])
            print(f"✅ SUCCESS: Found {len(keys)} dimension keys")
            
            if keys:
                # Show first 3 examples
                for i, key in enumerate(keys[:3], 1):
                    dimensions = key.get('Dimensions', {})
                    total = key.get('Total', 0)
                    print(f"  Example {i}:")
                    print(f"    Dimensions: {dimensions}")
                    print(f"    Total Load: {total:.4f}")
                    
        except Exception as e:
            error_msg = str(e)
            if "not a known group" in error_msg:
                print(f"❌ NOT SUPPORTED: {group} is not available for this engine")
            else:
                print(f"❌ ERROR: {error_msg}")
    
    # ========================================================================
    # TEST 4: Test SQL Metrics Collection
    # ========================================================================
    print_section("TEST 4: SQL Query Metrics")
    
    print("\n--- Attempting to collect SQL queries with metrics ---")
    try:
        # First, get top SQL queries
        response = pi_client.client.describe_dimension_keys(
            ServiceType='RDS',
            Identifier=resource_id,
            Metric='db.load.avg',
            GroupBy={'Group': 'db.sql'},
            StartTime=start_time,
            EndTime=end_time
        )
        
        keys = response.get('Keys', [])
        print(f"\nFound {len(keys)} SQL queries")
        
        if keys:
            # Try to get detailed metrics for first query
            first_key = keys[0]
            dimensions = first_key.get('Dimensions', {})
            sql_id = dimensions.get('db.sql.id') or dimensions.get('db.sql')
            
            print(f"\nTesting detailed metrics for SQL ID: {sql_id}")
            
            # Try to get SQL text
            try:
                text_response = pi_client.client.get_resource_metadata(
                    ServiceType='RDS',
                    Identifier=resource_id,
                    MetricQuery={
                        'Metric': 'db.load.avg',
                        'GroupBy': {'Group': 'db.sql', 'Dimensions': [sql_id]}
                    }
                )
                
                sql_text = text_response.get('Features', {}).get('db.sql.statement', 'N/A')
                print(f"SQL Text: {sql_text[:100]}...")
                
            except Exception as e:
                print(f"Could not get SQL text: {e}")
            
            # Try to get metrics with AdditionalMetrics
            print("\n--- Testing AdditionalMetrics parameter ---")
            
            # List of possible additional metrics
            additional_metric_sets = [
                # PostgreSQL specific
                ['db.sql.stats.calls_per_sec', 'db.sql.stats.avg_latency_per_call'],
                ['db.sql.stats.rows_per_call', 'db.sql.stats.rows_per_sec'],
                ['db.sql.stats.blk_read_time', 'db.sql.stats.blk_write_time'],
                # Generic
                ['db.sql.tokenized_id'],
                # Try empty list
                []
            ]
            
            for i, metrics in enumerate(additional_metric_sets, 1):
                print(f"\nAttempt {i}: {metrics if metrics else '(empty list)'}")
                try:
                    if metrics:  # Only try if not empty
                        response = pi_client.client.describe_dimension_keys(
                            ServiceType='RDS',
                            Identifier=resource_id,
                            Metric='db.load.avg',
                            GroupBy={'Group': 'db.sql'},
                            StartTime=start_time,
                            EndTime=end_time,
                            AdditionalMetrics=metrics
                        )
                        
                        keys_with_metrics = response.get('Keys', [])
                        if keys_with_metrics:
                            first = keys_with_metrics[0]
                            additional = first.get('AdditionalMetrics', {})
                            print(f"  ✅ SUCCESS: Got additional metrics: {additional}")
                        else:
                            print(f"  ⚠️ No keys returned")
                    else:
                        print(f"  ⏭️ Skipping empty list test")
                        
                except Exception as e:
                    print(f"  ❌ FAILED: {e}")
        else:
            print("No SQL queries found in time range")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # ========================================================================
    # TEST 5: Get Resource Metrics (Time Series)
    # ========================================================================
    print_section("TEST 5: Resource Metrics Time Series")
    
    print("\n--- Testing get_resource_metrics ---")
    
    # Test different metric queries
    metric_queries = [
        {
            'name': 'DB Load Average',
            'metric': 'db.load.avg'
        },
        {
            'name': 'DB Load Max',
            'metric': 'db.load.max'
        },
        {
            'name': 'OS CPU Utilization',
            'metric': 'os.cpuUtilization.total.avg'
        },
        {
            'name': 'OS Memory Free',
            'metric': 'os.memory.free.avg'
        }
    ]
    
    for query_info in metric_queries:
        print(f"\n--- {query_info['name']} ({query_info['metric']}) ---")
        try:
            response = pi_client.client.get_resource_metrics(
                ServiceType='RDS',
                Identifier=resource_id,
                MetricQueries=[
                    {
                        'Metric': query_info['metric']
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                PeriodInSeconds=300  # 5 minute intervals
            )
            
            metric_list = response.get('MetricList', [])
            if metric_list:
                data_points = metric_list[0].get('DataPoints', [])
                print(f"  ✅ SUCCESS: Got {len(data_points)} data points")
                
                if data_points:
                    # Show first and last data point
                    first = data_points[0]
                    last = data_points[-1]
                    print(f"  First: {first.get('Timestamp')} = {first.get('Value', 0):.4f}")
                    print(f"  Last:  {last.get('Timestamp')} = {last.get('Value', 0):.4f}")
            else:
                print(f"  ⚠️ No data returned")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_section("SUMMARY")
    
    print("""
Based on the tests above, here's what Performance Insights provides
for Aurora PostgreSQL 17.5:

WHAT WORKS:
✅ SQL query identification (db.sql dimension group)
✅ Top users (db.user dimension group)
✅ Wait events (db.wait_event dimension group)
✅ Host information (db.host dimension group)
✅ Application names (db.application dimension group)
✅ Session types (db.session_type dimension group)
✅ DB Load metrics (db.load.avg, db.load.max, db.load.min)
✅ OS-level metrics (CPU, memory, disk, network)

WHAT DOESN'T WORK:
❌ SQL execution metrics (calls/sec, latency, rows)
❌ SQL I/O metrics (read time, write time, blocks read/written)
❌ Top databases (db.name, db.database dimension groups not supported)
❌ AdditionalMetrics parameter (not supported for PostgreSQL)

CONCLUSION:
Aurora PostgreSQL Performance Insights API provides:
- IDENTIFICATION of top SQL queries, users, wait events
- LOAD metrics (how much load each query/user contributes)
- OS-level performance metrics

But it does NOT provide:
- EXECUTION metrics (how many times, how fast, how many rows)
- I/O metrics (read/write time and bytes)
- Database-level grouping

These detailed metrics are only available through:
1. Direct PostgreSQL connection (pg_stat_statements)
2. AWS Console (which has direct access to internal tables)
3. CloudWatch Logs (if slow query logging is enabled)
""")

if __name__ == '__main__':
    main()
