import json
import boto3
import os

def lambda_handler(event, context):
    app_id = event['app']['id']
    ec2 = boto3.resource('ec2')
    res = ec2.instances.filter(Filters=[
        {'Name':'tag:id', 'Values':[app_id]},
        {'Name':'tag:batch_job', 'Values':["ml"]}
    ])
    
    instance_ids = []
    for instance in res:
        instance_ids.append(instance.id)
        try:
            instance.terminate(DryRun=False)
        except:
            pass
    
    return {
        'statusCode': 200,
        'body': ', '.join(instance_ids)
    }

