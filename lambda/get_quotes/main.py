import json
from urllib.request import urlopen
import boto3
import os
import datetime

def lambda_handler(event, context):
    lam = boto3.client('lambda')
    s3 = boto3.client('s3')
    bucket_name = event['bucket_name']
    print("bucket:",bucket_name)

    url_templ = 'https://markets.businessinsider.com/index/components/s&p_500?p={0}'
    dt = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    res = {'bucket_name':bucket_name, 'files':[]}
    file_name_templ = 'html/businessinsider_{0}_{1}.html'

    for n in range(1,11):
        url = url_templ.format(n)
        data = urlopen(url)
        file_name = file_name_templ.format(dt, n)
        s3.upload_fileobj(data, bucket_name, file_name)
        res['files'].append(file_name)
        
    return {
        'statusCode': 200,
        'body': res
    }

