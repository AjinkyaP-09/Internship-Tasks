# ----------------------------------------------------
# Lambda Function 2: EBS_ModifyVolume
# File: ebs_modify_volume.py
# ----------------------------------------------------
import boto3

# Initialize EC2 client
ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    """
    Receives details for a single volume and modifies its type to gp3.
    Returns a status message.
    """
    # The input 'event' is a single item from the Step Functions Map state
    volume_id = event['VolumeId']
    
    print(f"Attempting to modify Volume ID: {volume_id} to gp3.")

    try:
        # Call the modify_volume API to change the type to gp3
        response = ec2.modify_volume(
            VolumeId=volume_id,
            VolumeType='gp3'
        )
        
        modification_state = response.get('VolumeModification', {}).get('ModificationState', 'unknown')
        print(f"Modification initiated for {volume_id}. State: {modification_state}")
        
        return {
            'Status': 'Success',
            'VolumeId': volume_id,
            'Region': event.get('Region', 'N/A'),
            'Message': f'Successfully initiated conversion of {volume_id} to gp3. Current state: {modification_state}'
        }

    except Exception as e:
        error_message = str(e)
        print(f"Error modifying volume {volume_id}: {error_message}")
        return {
            'Status': 'Error',
            'VolumeId': volume_id,
            'Region': event.get('Region', 'N/A'),
            'Message': f'Error converting {volume_id}: {error_message}'
        }
