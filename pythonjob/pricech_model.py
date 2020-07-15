import sys
from awsglue.utils import getResolvedOptions
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import glue_utils
from sklearn.preprocessing import KBinsDiscretizer
import pickle
from sklearn.neural_network import MLPClassifier
import datetime

#get params
args = getResolvedOptions(sys.argv, ['bucket_name','alert_topic','log_table','event_table','app','temporary'])
bucket_name = args['bucket_name']
alert_topic = args['alert_topic']
log_table_name = args['log_table']
event_table_name = args['event_table']
app = json.loads(args['app'])
temporary = True if args['temporary'] == "true" or args['temporary'] == "1" else False
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket_name)
db = boto3.resource('dynamodb')
event_table = db.Table(event_table_name)

#create model
try:
    model = glue_utils.PriceChModel(bucket)
    full_refresh = False
except:
    model = MLPClassifier(warm_start=True)
    model = glue_utils.PriceChModel(model=model)
    full_refresh = True

#get list of all company codes
comp_codes = glue_utils.list_companies(event_table)

#alert if input files missing
if not comp_codes:
    sns = boto3.resource('sns')
    topic = sns.Topic(alert_topic)
    topic.publish(
        Message = "Missing events"
    )
    print("Missing events")
    exit()

#get bins
discretizer = glue_utils.Discretizer(bucket)

#build model
start_dt = datetime.datetime.now()
start_dt -= datetime.timedelta(days=7)
start_dt = start_dt.strftime(glue_utils.DB_DATE_FORMAT)
for comp_code in comp_codes:
    expr = Key('comp_code').eq(comp_code)
    if not full_refresh:
        expr = expr & Key('quote_dt').gt(start_dt) 
    res = event_table.query(
        KeyConditionExpression = expr
    )
    
    if not res['Items']:
        continue

    event = None
    train_x = []
    train_y = []
    for item in res['Items']:
        quote_dt = item['quote_dt']
        prev_event = event
        event = glue_utils.Event(bucket=bucket, event_table=event_table, comp_code=comp_code, quote_dt=quote_dt)
        if prev_event is None:
            continue
        price1 = prev_event.get_price()
        price2 = event.get_price()
        high_price2 = event.get_high_price()
        low_price2 = event.get_low_price()
        if price1 < .01 or price2 < .01:
            continue
        if high_price2 < .01:
            high_price2 = price2
        if low_price2 < .01:
            low_price2 = price2
        price_ch = price2/price1-1
        price_class = discretizer.price_class(price_ch)
        high_ch = high_price2/price1-1
        high_class = discretizer.high_class(high_ch)
        low_ch = low_price2/price1-1
        low_class = discretizer.low_class(low_ch)
        inputs = event.get_inputs()
        train_x.append(inputs)
        train_y.append(price_class + high_class + low_class)
        
    if train_x and train_y:
        model.model.fit(train_x, train_y)

#save model
model.save(bucket)
