#!/usr/bin/env python3
"""Simple test to check if we can get SQL queries at all."""

import boto3
from datetime import datetime, timedelta

# Configuration
instance_id = 'ielts-ses-sit-v1-clusterinstance1'
profile = 'LT-SIT'
region = 'ap-southeast-1'

print("="*80)
print("Simple Performance Insights Test")
print("="*80)
print(f"Instance: {instance_id}")
print(f"Profile: {profile}")
print(f"Region: {region}")
print()

# Create session
session = boto3.Session(profile_name=profile, region_name=region)

# Create clients
rds = session.client('rds')
pi = session.client('pi')

print("Step 1: Get instance details...")
try:
    response = rds.describe_db_instances(DBInstanceIdentifier=instance_id)
    instance = response['DBInstances'][0]
    resource_id = instance['DbiResourceId']
    engine = instance['Engine']
    pi_enabled = instance.get('PerformanceInsightsEnabled', False)
    
    print(f"  Resource ID: {resource_id}")
    print(f"  Engine: {engine}")
    print(f"  PI Enabled: {pi_enabled}")
    print()
except Exception as e:
    print(f"  ERROR: {e}")
    exit(1)

if not pi_enabled:
    print("ERROR: Performance Insights is not enabled!")
    exit(1)

# Time range
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=24)

print(f"Step 2: Get SQL queries (last 24 hours)...")
print(f"  Start: {start_time}")
print(f"  End: {end_time}")
print()

try:
    # Try basic call first
    print("  Trying basic describe_dimension_keys (no additional metrics)...")
    response = pi.describe_dimension_keys(
        ServiceType='RDS',
        Identifier=resource_id,
        StartTime=start_time,
        EndTime=end_time,
        Metric='db.load.avg',
        GroupBy={'Group': 'db.sql'}
    )
    
    keys = response.get('Keys', [])
    print(f"  SUCCESS: Got {len(keys)} SQL queries")
    print()
    
    if keys:
        print("First 3 queries:")
        for i, key in enumerate(keys[:3], 1):
            dims = key.get('Dimensions', {})
            sql_id = dims.get('db.sql.id', 'N/A')
            sql_text = dims.get('db.sql.statement', 'N/A')
            total_load = key.get('Total', 0.0)
            
            print(f"\n  Query {i}:")
            print(f"    SQL ID: {sql_id}")
            print(f"    Total Load: {total_load:.4f} AAS")
            print(f"    SQL Text: {sql_text[:100]}...")
            print(f"    Has AdditionalMetrics: {'AdditionalMetrics' in key}")
            if 'AdditionalMetrics' in key:
                print(f"    AdditionalMetrics: {key['AdditionalMetrics']}")
    else:
        print("  WARNING: No SQL queries found in the time range")
        print("  This could mean:")
        print("    - No queries were executed during this period")
        print("    - The database was idle")
        print("    - Performance Insights data retention period has passed")
    
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("Test completed")
print("="*80)
