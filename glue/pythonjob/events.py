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


def logg(x):
    print("---- [{}] ".format(datetime.datetime.now()), x)

#get params
args = getResolvedOptions(sys.argv, ['bucket_name','alert_topic','JOB_NAME'])
bucket_name = args['bucket_name']
alert_topic = args['alert_topic']
log_table_name = args['log_table']
event_table_name = args['event_table']
job_name = args['JOB_NAME']
job_id = args['JOB_RUN_ID']

logg("Job name: {}".format(job_name))
logg("Job ID: {}".format(job_id))

#get input file list
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket_name)
objs = bucket.objects.all()
files = []
for obj in objs:
    if obj.key.startswith('csv_clean/') and obj.storage_class == 'STANDARD' and datetime.date.today()-obj.last_modified.date() < datetime.timedelta(7):
        files.append(obj.key)

#alert if input files missing
if not files:
    sns = boto3.resource('sns')
    topic = sns.Topic(alert_topic)
    topic.publish(
        Message = "Missing files in csv_clean/ from the last week"
    )

db = boto3.resource('dynamodb')
log_table = db.Table(log_table_name)
process_key = None
for key in files:
    res = log_table.get_item(
        Key = {"obj_key": key}
    )
    if not res['Item']:
        if process_key is None or key.split('_')[-1] < process_key.split('_')[-1]:
            process_key = key

if process_key is None:
    exit(0)

log_table.put_item(
    Item = {
        'obj_key': process_key,
        'job_id' : job_id
    }
)

logg("Process key: {}".format(process_key))

f = bucket.Object(process_key).get()
inp = f['Body'].read().decode('utf-8')
csv_reader = csv.DictReader(io.StringIO(inp))
event_table = db.Table(event_table_name)
for row in csv_reader:
    comp_code = row['comp_code']
    quote_dt = row['quote_dt']
    price = row['price']
    
    #get last quote_dt
    res = log_table.query(
        KeyConditionExpression = Key('comp_code').eq(comp_code),
        ScanIndexForward = False,
        Limit = 1
    )
    last_quote_dt = None
    if res['Items']:
        last_quote_dt = res['Items']['quote_dt']
        if last_quote_dt >= quote_dt:
            continue
    
    #add event to db
    event_table.put_item(
        Item = {
            'comp_code': comp_code,
            'quote_dt' : quote_dt
        }
    )

    #get prev event
    prev_event = None
    if last_quote_dt is not None:
        obj_key = "events/{}_{}.json".format(comp_code, last_quote_dt)
        f = bucket.Object(obj_key).get()
        prev_event = f['Body'].read().decode('utf-8')
        prev_event = json.loads(prev_event)

    #calc new event
    event = row
    scale = prev_event['scale'] if prev_event is not None else 1
    for exp in range(1,11):
        period = 2 ** exp
        key = 'price{}'.format(period)
        if prev_event is not None:
            event[key] = price / period + prev_event[key] * (1-1/period)
        else:
            event[key] = price
    hour = int(quote_dt[11:13])
    event['start'] = 1 if hour <= 9 else 0
    event['end'] = 1 if hour >= 16 else 0
    ch = price/prev_event['price']-1 if prev_event is not None else 0
    for th in [10,20,40,80]:
        event['ch>'+th] = 1 if ch > th/100 or ch < 1/(th/100+1)-1 else 0
    if event['ch>80']:
        scale *= prev_event['price'] / price
    event['scale'] = scale
    
    #add event to s3
    dt = quote_dt[:13].replace('-','').replace(' ','')
    obj_key = "events/date={}/{}_{}.json".format(dt, comp_code, quote_dt)
    event = json.dumps(event)
    bucket.put_object(Key=obj_key, Body=bytearray(event, 'utf-8'))

