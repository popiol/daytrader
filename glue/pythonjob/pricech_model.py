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

#get bins
discretizer = glue_utils.get_discretizer(bucket)
n_bins = discretizer.n_bins_[0]
bins = discretizer.bin_edges_[0]

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
        if prev_price is None:
            continue
        price1 = float(prev_event['price']) * float(prev_event['scale'])
        price2 = float(event['price']) * float(event['scale'])
        if price1 < .01 or price2 < .01:
            continue
        price_ch = price2/price1-1
        price_class = [1 if x <= price_ch <= bins[i+1] else 0 for i,x in enumerate(bins[:-1])]
        attrs = ['low_price','high_price','start','end','ch>10','ch>20','ch>40','ch>80']
        period_attrs = ['price','high','low','jumpup','jumpdown']
        for exp in range(1,11):
            period = 2 ** exp
            for attr in period_attrs:
                attrs.append(f'{attr}{period}')
        inputs = [float(event[x]) for x in attrs]
        train_x.append(inputs)
        train_y.append(price_class)
    model.fit(train_x, train_y)

#save model
model = pickle.dumps(model)
obj_key = "model/pricech_model.pickle"
bucket.put_object(Key=obj_key, Body=discretizer)
