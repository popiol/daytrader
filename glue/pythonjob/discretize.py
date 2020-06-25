import sys
from awsglue.utils import getResolvedOptions
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import glue_utils
from sklearn.preprocessing import KBinsDiscretizer
import pickle
import numpy as np

#get params
args = getResolvedOptions(sys.argv, ['bucket_name','alert_topic','log_table','event_table','app','temporary'])
bucket_name = args['bucket_name']
alert_topic = args['alert_topic']
log_table_name = args['log_table']
event_table_name = args['event_table']
app = json.loads(args['app'])
temporary = args['temporary']

#get list of all company codes
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket_name)
objs = bucket.objects.all()
comp_codes = {}
for obj in objs:
    if obj.key.startswith('events/'):
        comp_code = obj.key.split('/')[-1].split('_')[0]
        comp_codes[comp_code] = 1

#alert if input files missing
if not comp_codes:
    sns = boto3.resource('sns')
    topic = sns.Topic(alert_topic)
    topic.publish(
        Message = "Missing files in events/"
    )
    print("Missing files in events/")
    exit()

#create list of price changes
price_ch = []
high_ch = []
low_ch = []
db = boto3.resource('dynamodb')
event_table = db.Table(event_table_name)
for comp_code in comp_codes:
    res = event_table.query(
        KeyConditionExpression = Key('comp_code').eq(comp_code)
    )
    
    if not res['Items']:
        continue

    price = None
    for item in res['Items']:
        quote_dt = item['quote_dt']
        event = glue_utils.Event(bucket=bucket, comp_code=comp_code, quote_dt=quote_dt)
        prev_price = price
        price = event.get_price()
        low_price = event.get_low_price()
        high_price = event.get_high_price()
        if prev_price is not None and prev_price >= .01:
            price_ch.append(price/prev_price-1)
            high_ch.append(high_price/prev_price-1)
            low_ch.append(low_price/prev_price-1)

if not price_ch:
    print("temporary:", temporary)
    if temporary:
        price_ch = [0,.01,-.01]
    else:
        print("No price changes")
        exit()

#discretize
discretizer = KBinsDiscretizer(n_bins=[glue_utils.PRICE_CHANGE_N_BINS, glue_utils.HIGH_CHANGE_N_BINS, glue_utils.LOW_CHANGE_N_BINS], encode='ordinal')
X = list(zip(price_ch, high_ch, low_ch))
discretizer.fit(X)

#save discretizer
discretizer = glue_utils.Discretizer(discretizer=discretizer)
discretizer.save(bucket)
