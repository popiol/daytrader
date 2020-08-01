import sys
from awsglue.utils import getResolvedOptions
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import glue_utils
from sklearn.preprocessing import KBinsDiscretizer
import pickle
import numpy as np
import random
from decimal import Decimal

#get params
args = getResolvedOptions(sys.argv, ['bucket_name','alert_topic','log_table','event_table','app','temporary'])
bucket_name = args['bucket_name']
alert_topic = args['alert_topic']
log_table_name = args['log_table']
event_table_name = args['event_table']
app = json.loads(args['app'])
temporary = True if args['temporary'] == "true" or args['temporary'] == "1" else False
db = boto3.resource('dynamodb')
event_table = db.Table(event_table_name)
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket_name)

#get list of all company codes
comp_codes, quote_dts = glue_utils.list_companies(event_table)

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
for comp_code in comp_codes:
    res = event_table.query(
        KeyConditionExpression = Key('comp_code').eq(comp_code)
    )
    
    if not res['Items']:
        continue

    price = None
    for item in res['Items']:
        quote_dt = item['quote_dt']
        prev_price = price
        event = glue_utils.Event(bucket=bucket, event_table=event_table, comp_code=comp_code, quote_dt=quote_dt)
        price = event.get_price()
        high_price = event.get_high_price()
        low_price = event.get_low_price()

        if high_price < .01:
            high_price = price
        if low_price < .01:
            low_price = price
        if prev_price is not None and prev_price >= .01 and price >= .01:
            price_ch.append(price/prev_price-1)
            high_ch.append(high_price/prev_price-1)
            low_ch.append(low_price/prev_price-1)

if not price_ch:
    if temporary:
        price_ch = [0,.01,-.01]
    else:
        print("No price changes")
        exit()

if temporary:
    for _ in range(10):
        price_ch.append(random.gauss(0, .005))
        high_ch.append(random.gauss(0, .005))
        low_ch.append(random.gauss(0, .005))

#discretize
discretizer = KBinsDiscretizer(n_bins=[glue_utils.PRICE_CHANGE_N_BINS, glue_utils.HIGH_CHANGE_N_BINS, glue_utils.LOW_CHANGE_N_BINS], encode='ordinal')
X = list(zip(price_ch, high_ch, low_ch))
discretizer.fit(X)
print(discretizer.bin_edges_)

#avg
discretizer.avg = np.average(price_ch)

#save discretizer
discretizer = glue_utils.Discretizer(discretizer=discretizer)
discretizer.save(bucket)
