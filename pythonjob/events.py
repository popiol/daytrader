import sys
import datetime
from awsglue.utils import getResolvedOptions
import boto3
import csv
import io
from boto3.dynamodb.conditions import Key, Attr
import json
import glue_utils
import random

#get params
args = getResolvedOptions(sys.argv, ['bucket_name','alert_topic','log_table','event_table','app','temporary','repeat'])
bucket_name = args['bucket_name']
alert_topic = args['alert_topic']
log_table_name = args['log_table']
event_table_name = args['event_table']
app = json.loads(args['app'])
temporary = True if args['temporary'] == "true" or args['temporary'] == "1" else False
repeat = int(args['repeat'])

#get job id
job_id = None
job_name = '{}_events'.format(app['id'])
glue = boto3.client('glue')
res = glue.get_job_runs(
    JobName = job_name
)
while True:
    if not res['JobRuns']:
        break
    for run in res['JobRuns']:
        if run['JobRunState'] == 'RUNNING':
            job_id = run['Id']
            break
    if job_id is not None:
        break
    if 'NextToken' not in res:
        break
    token = res['NextToken']
    res = glue.get_job_runs(
        JobName = job_name,
        NextToken = token
    )
    
if job_id is None:
    print("Job ID not found")
    exit()

#logg("Job ID: {}".format(job_id))

#get input file list
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket_name)
objs = bucket.objects.all()
files = []
for obj in objs:
    if obj.key.startswith('csv_clean/') and datetime.date.today()-obj.last_modified.date() < datetime.timedelta(7):
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
event_table = db.Table(event_table_name)

for _ in range(repeat):
    #pick the oldest file
    process_key = None
    shift_dt = False
    stop_shift_dt = False
    for key in files:
        res = log_table.query(
            KeyConditionExpression = Key('obj_key').eq(key),
        )
        if not res['Items']:
            if process_key is None or key.split('_')[-2] < process_key.split('_')[-2] or shift_dt:
                process_key = key
                shift_dt = False
                stop_shift_dt = True
        elif temporary and not stop_shift_dt:
            res = event_table.scan(
                FilterExpression = Attr('source_file').eq(key)
            )
            last_quote_dt = None
            for item in res['Items']:
                if last_quote_dt is None or item['quote_dt'] > last_quote_dt:
                    last_quote_dt = item['quote_dt']
            if process_key is None or last_quote_dt is None or last_quote_dt < min_quote_dt:
                process_key = key
                shift_dt = True
                min_quote_dt = last_quote_dt

    if process_key is None:
        exit()

    process_dt = datetime.datetime.utcnow().strftime(glue_utils.DB_DATE_FORMAT)

    #add process log
    log_table.put_item(
        Item = {
            'obj_key': process_key,
            'process_dt': process_dt,
            'job_id' : job_id
        }
    )

    #logg("Process key: {}".format(process_key))

    #process records
    f = bucket.Object(process_key).get()
    inp = f['Body'].read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(inp))
    for row in csv_reader:
        comp_code = row['comp_code']
        quote_dt = row['quote_dt']
        price = float(row['price'])
        low_price = float(row['low_price'])
        high_price = float(row['high_price'])

        #check price
        if price < .01:
            continue

        #check high price
        if high_price < .01 or high_price < price or high_price > 2 * price:
            high_price = price
            row['high_price'] = high_price
        
        #check low price
        if low_price < .01 or low_price > price or low_price < price / 2:
            low_price = price
            row['low_price'] = low_price
        
        #get last quote_dt
        res = event_table.query(
            KeyConditionExpression = Key('comp_code').eq(comp_code),
            ScanIndexForward = False,
            Limit = 1
        )
        last_quote_dt = None
        if res['Items']:
            last_quote_dt = res['Items'][0]['quote_dt']
            if not temporary:
                last_quote_dt_minus_th = datetime.datetime.strptime(last_quote_dt, glue_utils.DB_DATE_FORMAT)
                last_quote_dt_minus_th -= datetime.timedelta(minutes=50)
                last_quote_dt_minus_th = last_quote_dt_minus_th.strftime(glue_utils.DB_DATE_FORMAT)
                if last_quote_dt_minus_th >= quote_dt:
                    continue
        
        if shift_dt:
            quote_dt = datetime.datetime.strptime(last_quote_dt, glue_utils.DB_DATE_FORMAT)
            quote_dt += datetime.timedelta(hours=1)
            quote_dt = quote_dt.strftime(glue_utils.DB_DATE_FORMAT)
            price *= 1 + random.gauss(0, .005)
        
        #get prev event
        prev_event = None
        if last_quote_dt is not None:
            #print(comp_code, last_quote_dt)
            prev_event = glue_utils.Event(bucket=bucket, event_table=event_table, comp_code=comp_code, quote_dt=last_quote_dt)
            event = prev_event.next(price, high_price, low_price, quote_dt)
        else:
            #print(row)
            event = glue_utils.Event(row)

        #add event to db
        event.source_file = process_key
        event.persist(event_table)
        