import json
from urllib.request import urlopen
import boto3
import os
import datetime
import pytz

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket_name = event['bucket_name']
    
    #alert if quotes missing
    dt = datetime.datetime.now(pytz.timezone('US/Eastern'))
    if dt.hour > 9:
        bucket = s3.Bucket(bucket_name)
        hour = datetime.timedelta(hours=1)
        dt2 = (datetime.datetime.now()-hour).strftime('%Y%m%d%H')
        objs = bucket.filter(Prefix="/html/businessinsider_{}".format(dt2))
        if len(objs) == 0:
            sns_arn = event['sns_arn']
            sns = boto3.resource('sns')
            topic = sns.Topic(sns_arn)
            topic.publish(
                Message = "Missing quotes in /html for {}".format(dt2)
            )

    #get new quotes
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

