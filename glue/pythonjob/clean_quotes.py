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


def transform(row):
    out = {}
    
    #id
    out['row_id'] = int(row['id']) + 1
    
    #comp code
    comp_code = row['Code'].upper()
    assert len(comp_code) <= 10
    out['comp_code'] = comp_code
    
    #low high
    low_price, high_price = row['Low_High'].split()
    out['low_price'] = float(low_price.replace(',',''))
    out['high_price'] = float(high_price.replace(',',''))

    #date
    dt = dateutil.parser.parse(row['Time_Date'])
    dt = dt.strftime("%Y-%m-%d %H:%M:%S")
    assert dt > '2020-01-01 00:00:00'
    out['quote_dt'] = dt

    #price
    price = row['Latest_Price_Previous_Close'].split()[0]
    price = float(price.replace(',',''))
    assert price > 0
    out['price'] = price
    
    return out
    
    
col_names = ['row_id','quote_dt','comp_code','price','low_price','high_price']

#get bucket name
args = getResolvedOptions(sys.argv, ['scriptLocation'])
bucket = args['scriptLocation'].split('/')[2]

logg("Bucket: {}".format(bucket))

#get input file list
s3 = boto3.resource('s3')
s3bucket = s3.Bucket(bucket)
objs = s3bucket.objects.all()
files = []
for obj in objs:
    if obj.key.startswith('csv/') and obj.storage_class == 'STANDARD' and datetime.date.today()-obj.last_modified.date() < datetime.timedelta(7):
        files.append(obj.key)

#process files
for key in files:
    clean_key = key.replace('csv/','csv_clean/')
    rejected_key = key.replace('csv/','csv_rejected/')
    
    if list(s3bucket.objects.filter(Prefix=clean_key)) or list(s3bucket.objects.filter(Prefix=rejected_key)):
        continue
    
    logg(key)
    
    f = s3bucket.Object(key).get()
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
        s3bucket.put_object(Key=clean_key, Body=bytearray(out.getvalue(), 'utf-8'))
    
    if n_rej > 0:
        s3bucket.put_object(Key=rejected_key, Body=bytearray(rej.getvalue(), 'utf-8'))

    out.close()
    rej.close()
    