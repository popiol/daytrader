import json
import boto3
import os
import time
import traceback

def get_query_result(queryString):
    logs = boto3.client('logs')
    res = logs.start_query(
        logGroupName='/aws/batch/job',
        queryString=queryString,
        startTime=0,
        endTime=int(time.time())
    )
    query_id = res['queryId']

    for _ in range(60):
        res = logs.get_query_results(queryId=query_id)
        if res['status'] in ['Complete','Failed','Cancelled']:
            break
        time.sleep(10)

    return res['results']

def get_field_value(results, field_name):
    val = []
    for result in results:
        for field in result:
            if field['field'] == field_name:
                val.append(field['value'])
                break
    return val

def lambda_handler(event, context):
    try:
        app_id = os.environ['app_id']
        job_name = event['queryStringParameters']['job_name']
        results = get_query_result(f'fields @logStream as logStream | filter @logStream like /{app_id}_{job_name}/ | sort @timestamp desc | limit 1')
        logStream = get_field_value(results, 'logStream')
        if logStream:
            logStream = logStream[0]
            results = get_query_result(f'fields @message as message | filter @logStream = "{logStream}"')
            messages = get_field_value(results, 'message')
            comp_code = None
            plots = {}
            for message in messages:
                message = message.strip()
                if comp_code is not None:
                    if message[0] == '[':
                        plots[comp_code] = json.loads(message)
                        comp_code = None
                elif len(message) == 3 and 'AAA' <= message <= 'ZZZ':
                    comp_code = message
        else:
            plots = {}
        
        return {
            'statusCode': 200,
            'body': json.dumps(plots)
        }
    except:
        return {
            'statusCode': 300,
            'body': json.dumps([[x.strip() for x in traceback.format_exc().splitlines()[-2:]], event])
        }
        