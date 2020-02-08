import json
from urllib.request import urlopen
import boto3
import os
import datetime

def lambda_handler(event, context):
    lam = boto3.client('lambda')
    s3 = boto3.client('s3')

    fun = lam.get_function_configuration(FunctionName=context.function_name)
    arn = fun['FunctionArn']
    tags = lam.list_tags(Resource=arn)['Tags']
    bucket_name = 'popiol.{0}-{1}-quotes'.format(tags['App'], tags['AppVer'])
    print("bucket:",bucket_name)

    url_templ = 'https://markets.businessinsider.com/index/components/s&p_500?p={0}'
    dt = datetime.date.today().strftime('%Y%m%d')
    res = {'bucket_name':bucket_name, 'files':[]}
    file_name_templ = 'businessinsider_{0}.html'

    for n in range(1,2):
        url = url_templ.format(n)
        data = urlopen(url)
        file_name = file_name_templ.format(dt)
        s3.upload_fileobj(data, bucket_name, file_name)
        res['files'].append(file_name)
        
    return {
        'statusCode': 200,
        'body': res
    }
