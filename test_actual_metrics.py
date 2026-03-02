#!/usr/bin/env python3
"""Test to see what metrics are actually available from Performance Insights."""

import boto3
from datetime import datetime, timedelta
import json

# Configuration
instance_id = 'ielts-ses-sit-v1-clusterinstance1'
profile = 'LT-SIT'
region = 'ap-southeast-1'

print("="*80)
print("Performance Insights Available Metrics Test")
print("="*80)
print()

# Create session
session = boto3.Session(profile_name=profile, region_name=region)
rds = session.client('rds')
pi = session.client('pi')

# Get instance details
response = rds.describe_db_instances(DBInstanceIdentifier=instance_id)
instance = response['DBInstances'][0]
resource_id = instance['DbiResourceId']
engine = instance['Engine']

print(f"Instance: {instance_id}")
print(f"Resource ID: {resource_id}")
print(f"Engine: {engine}")
print()

# Time range
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=24)

print("="*80)
print("TEST 1: Get available metrics for this resource")
print("="*80)

try:
    # List available metrics
    response = pi.list_available_resource_metrics(
        ServiceType='RDS',
        Identifier=resource_id,
        MetricTypes=['db.sql.stats']
    )
    
    print(f"Available SQL metrics for {engine}:")
    print()
    
    metrics = response.get('Metrics', [])
    for metric in metrics:
        metric_name = metric.get('Metric', 'N/A')
        description = metric.get('Description', 'No description')
        print(f"  • {metric_name}")
        print(f"    {description}")
        print()
    
    print(f"Total: {len(metrics)} metrics available")
    print()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("="*80)
print("TEST 2: Get SQL queries with ALL available metrics")
print("="*80)

try:
    # Get list of all available SQL metrics
    response = pi.list_available_resource_metrics(
        ServiceType='RDS',
        Identifier=resource_id,
        MetricTypes=['db.sql.stats']
    )
    
    all_metrics = [m['Metric'] for m in response.get('Metrics', [])]
    print(f"Requesting {len(all_metrics)} additional metrics...")
    print()
    
    # Get SQL queries with all available metrics
    response = pi.describe_dimension_keys(
        ServiceType='RDS',
        Identifier=resource_id,
        StartTime=start_time,
        EndTime=end_time,
        Metric='db.load.avg',
        GroupBy={'Group': 'db.sql'},
        AdditionalMetrics=all_metrics[:10]  # Limit to first 10 to avoid API limits
    )
    
    keys = response.get('Keys', [])
    print(f"Got {len(keys)} SQL queries")
    print()
    
    if keys:
        print("="*80)
        print("First query details:")
        print("="*80)
        
        key = keys[0]
        dims = key.get('Dimensions', {})
        
        print(f"SQL ID: {dims.get('db.sql.id', 'N/A')}")
        print(f"SQL Text: {dims.get('db.sql.statement', 'N/A')[:100]}...")
        print(f"Total Load: {key.get('Total', 0.0):.4f} AAS")
        print()
        
        print("AdditionalMetrics returned:")
        additional = key.get('AdditionalMetrics', {})
        if additional:
            for metric_name, value in additional.items():
                print(f"  {metric_name}: {value}")
        else:
            print("  (None - AdditionalMetrics field is empty or missing)")
        print()
        
        print("Full key structure:")
        print(json.dumps(key, indent=2, default=str))
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("TEST 3: Try get_resource_metrics for specific query")
print("="*80)

try:
    # Get first query ID
    response = pi.describe_dimension_keys(
        ServiceType='RDS',
        Identifier=resource_id,
        StartTime=start_time,
        EndTime=end_time,
        Metric='db.load.avg',
        GroupBy={'Group': 'db.sql'}
    )
    
    keys = response.get('Keys', [])
    if keys:
        sql_id = keys[0]['Dimensions']['db.sql.id']
        print(f"Testing with SQL ID: {sql_id}")
        print()
        
        # Get available metrics
        metrics_response = pi.list_available_resource_metrics(
            ServiceType='RDS',
            Identifier=resource_id,
            MetricTypes=['db.sql.stats']
        )
        
        available_metrics = [m['Metric'] for m in metrics_response.get('Metrics', [])]
        
        # Try to get metrics for this specific query
        print(f"Requesting metrics: {available_metrics[:5]}")
        print()
        
        metric_queries = []
        for metric in available_metrics[:5]:
            metric_queries.append({
                'Metric': metric
            })
        
        response = pi.get_resource_metrics(
            ServiceType='RDS',
            Identifier=resource_id,
            StartTime=start_time,
            EndTime=end_time,
            MetricQueries=metric_queries
        )
        
        print("Metrics returned:")
        for metric_data in response.get('MetricList', []):
            metric_name = metric_data.get('Key', {}).get('Metric', 'N/A')
            data_points = metric_data.get('DataPoints', [])
            
            if data_points:
                values = [dp.get('Value', 0) for dp in data_points if 'Value' in dp]
                if values:
                    avg_value = sum(values) / len(values)
                    print(f"  {metric_name}: {avg_value:.2f} (avg of {len(values)} data points)")
            else:
                print(f"  {metric_name}: No data points")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("Test completed")
print("="*80)
