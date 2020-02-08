import json
from urllib.request import urlopen
import boto3
import os

def lambda_handler(event, context):
    print("Event", event)
    print("Context",context)
    s3 = boto3.client('s3')
    client = boto3.client('lambda')
    fun = client.get_function(FunctionName=context.function_name)
    print("Function", fun)
    tags = fun['Tags']
    #url_temp = 'https://markets.businessinsider.com/index/components/s&p_500?p=<N>'
    #for n in range(1,2):
    #    url = url_temp.replace('<N>',str(n))
    #    data = urlopen(url).read().decode('utf-8')
    return {
        'statusCode': 200,
        'body': tags
    }

