import sys
import datetime
import dateutil.parser
from awsglue.utils import getResolvedOptions
import boto3
import csv
import re
import io
import traceback
from boto3.dynamodb.conditions import Key, Attr
import json
import math

#get params
args = getResolvedOptions(sys.argv, ['bucket_name','alert_topic','log_table','event_table','app'])
bucket_name = args['bucket_name']
alert_topic = args['alert_topic']
log_table_name = args['log_table']
event_table_name = args['event_table']
app = json.loads(args['app'])

#find objects to delete
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket_name)
objs = bucket.objects.all()
files = []
for obj in objs:
    if obj.key.startswith('events/'):
        files.append({'Key': obj.key})

#delete events from bucket
for batch_n in range(math.ceil(len(files)/1000)):
    bucket.delete_objects(
        Delete = {
            'Objects': files[batch_n*1000:(batch_n+1)*1000]
        }
    )

def truncate_table(db, table_name):
    table = db.describe_table(TableName=table_name)['Table']
    db.delete_table(TableName=table_name)
    arg_keys = ['AttributeDefinitions', 'TableName', 'KeySchema', 'LocalSecondaryIndexes', 'GlobalSecondaryIndexes', 'BillingMode', 'ProvisionedThroughput', 'StreamSpecification', 'SSESpecification', 'Tags']
    args = {table[x] for x in arg_keys}
    db.create_table(**args)

#truncate tables
db = boto3.client('dynamodb')
truncate_table(db, log_table_name)
truncate_table(db, event_table_name)
