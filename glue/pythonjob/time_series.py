import sys
import datetime
import dateutil.parser
from awsglue.utils import getResolvedOptions
import boto3
import csv
import re
import io
import traceback


def logg(x):
    print("---- [{}] ".format(datetime.datetime.now()), x)

#get params
args = getResolvedOptions(sys.argv, ['bucket_name','alert_topic'])
bucket_name = args['bucket_name']
alert_topic = args['alert_topic']

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
        Message = "Missing files in csv/ from the last week"
    )

#process files
for key in files:
    clean_key = key.replace('csv/','csv_clean/')
    rejected_key = key.replace('csv/','csv_rejected/')
    
    if list(bucket.objects.filter(Prefix=clean_key)) or list(bucket.objects.filter(Prefix=rejected_key)):
        continue
    
    logg(key)
    
    f = bucket.Object(key).get()
    inp = f['Body'].read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(inp))
    out = io.StringIO()
    n_out = 0
    out_writer = csv.DictWriter(out, fieldnames=col_names)
    out_writer.writeheader()
    rej = io.StringIO()
    n_rej = 0
    rej_writer = csv.DictWriter(rej, fieldnames=csv_reader.fieldnames+['error_message'])
    rej_writer.writeheader()
    for row in csv_reader:
        try:
            out_writer.writerow(transform(row))
            n_out += 1
        except:
            row['error_message'] = ' | '.join([x.strip() for x in traceback.format_exc().splitlines()[-2:]])
            rej_writer.writerow(row)
            n_rej += 1
    
    logg("# out: {}, # rej: {}".format(n_out, n_rej))
    
    if n_out > 0:
        bucket.put_object(Key=clean_key, Body=bytearray(out.getvalue(), 'utf-8'))
    
    if n_rej > 0:
        bucket.put_object(Key=rejected_key, Body=bytearray(rej.getvalue(), 'utf-8'))

    out.close()
    rej.close()
    