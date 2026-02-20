import boto3

session = boto3.Session(profile_name='LT-DEV', region_name='ap-southeast-1')
rds = session.client('rds')

print("Fetching RDS instances...")
response = rds.describe_db_instances(MaxRecords=20)

instances = response['DBInstances']
print(f"\nFound {len(instances)} RDS instance(s):\n")

for instance in instances:
    print(f"  - {instance['DBInstanceIdentifier']}")
    print(f"    Engine: {instance['Engine']}")
    print(f"    Status: {instance['DBInstanceStatus']}")
    print()
