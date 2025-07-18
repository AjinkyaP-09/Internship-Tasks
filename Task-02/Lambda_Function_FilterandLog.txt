# ----------------------------------------------------
# Lambda Function 1: EBS_FilterAndLog
# File: ebs_filter_and_log.py
# ----------------------------------------------------
import boto3
import os
from datetime import datetime

# Initialize clients
ec2 = boto3.client('ec2')
dynamodb = boto3.resource('dynamodb')

# Get table name from environment variable
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'EBSOptimizationLog')
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Scans for gp2 volumes with the 'AutoConvert=true' tag,
    logs their details to DynamoDB, and returns a list of eligible volumes.
    """
    print("Scanning for gp2 volumes tagged with AutoConvert=true...")

    # Define filters for the EC2 describe_volumes call
    filters = [
        {'Name': 'volume-type', 'Values': ['gp2']},
        {'Name': 'tag:AutoConvert', 'Values': ['true']}
    ]

    response = ec2.describe_volumes(Filters=filters)
    eligible_volumes = []

    for volume in response['Volumes']:
        volume_id = volume['VolumeId']
        
        # Prepare item details for logging
        instance_id = volume['Attachments'][0]['InstanceId'] if volume.get('Attachments') else "N/A"
        volume_details = {
            'VolumeId': volume_id,
            'InstanceId': instance_id,
            'VolumeType': volume['VolumeType'],
            'Size': volume['Size'],
            'Region': volume['AvailabilityZone'],
            'Timestamp': datetime.utcnow().isoformat()
        }
        
        # Log the volume details to the DynamoDB table
        try:
            table.put_item(Item=volume_details)
            print(f"Successfully logged {volume_id} to DynamoDB.")
            eligible_volumes.append(volume_details)
        except Exception as e:
            print(f"Error logging {volume_id} to DynamoDB: {str(e)}")

    print(f"Found {len(eligible_volumes)} volumes to convert.")
    
    # Return a structured response for Step Functions
    return {
        'statusCode': 200,
        'volumes_to_convert': eligible_volumes
    }
