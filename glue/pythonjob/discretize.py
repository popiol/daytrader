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
import glue_utils
from sklearn.preprocessing import KBinsDiscretizer
import pickle
import numpy as np

def logg(x):
    print("---- [{}] ".format(datetime.datetime.now()), x)

#get params
args = getResolvedOptions(sys.argv, ['bucket_name','alert_topic','log_table','event_table','app'])
bucket_name = args['bucket_name']
alert_topic = args['alert_topic']
log_table_name = args['log_table']
event_table_name = args['event_table']
app = json.loads(args['app'])

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
if len(comp_codes) == 0:
    sns = boto3.resource('sns')
    topic = sns.Topic(alert_topic)
    topic.publish(
        Message = "Missing files in events/"
    )

#create list of price changes
price_ch = []
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
        event_key = glue_utils.create_event_key(comp_code, quote_dt)
        f = bucket.Object(event_key).get()
        event = f['Body'].read().decode('utf-8')
        event = json.loads(event)
        prev_price = price
        price = float(event['price'])
        if prev_price is not None and prev_price >= .01:
            price_ch.append(price/prev_price-1)

#discretize
discretizer = KBinsDiscretizer(n_bins=glue_utils.PRICE_CHANGE_N_BINS, encode='ordinal')
price_ch = np.reshape(price_ch, (-1, 1))
discretizer.fit(price_ch)

#save discretizer
discretizer = pickle.dumps(discretizer)
obj_key = "model/discretizer.pickle"
bucket.put_object(Key=obj_key, Body=bytearray(discretizer, 'utf-8'))
