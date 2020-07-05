import sys
from awsglue.utils import getResolvedOptions
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import glue_utils
from sklearn.preprocessing import KBinsDiscretizer
import pickle
from sklearn.neural_network import MLPClassifier

#get params
args = getResolvedOptions(sys.argv, ['bucket_name','alert_topic','log_table','event_table','app','temporary'])
bucket_name = args['bucket_name']
alert_topic = args['alert_topic']
log_table_name = args['log_table']
event_table_name = args['event_table']
app = json.loads(args['app'])
temporary = True if args['temporary'] == "true" or args['temporary'] == "1" else False

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

#get bins
discretizer = glue_utils.Discretizer(bucket)

#create model
model = MLPClassifier(warm_start=True)

#build model
db = boto3.resource('dynamodb')
event_table = db.Table(event_table_name)
for comp_code in comp_codes:
    res = event_table.query(
        KeyConditionExpression = Key('comp_code').eq(comp_code)
    )
    
    if not res['Items']:
        continue

    event = None
    train_x = []
    train_y = []
    for item in res['Items']:
        quote_dt = item['quote_dt']
        event_key = glue_utils.create_event_key(comp_code, quote_dt)
        f = bucket.Object(event_key).get()
        prev_event = event
        event = f['Body'].read().decode('utf-8')
        event = json.loads(event)
        event = glue_utils.Event(event)
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
        model.fit(train_x, train_y)

#save model
model = glue_utils.PriceChModel(model=model)
model.save(bucket)
