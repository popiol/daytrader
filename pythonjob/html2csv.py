import os

if 'GLUE_INSTALLATION' in os.environ.keys():
    import site
    import importlib
    from setuptools.command import easy_install
    install_path = os.environ['GLUE_INSTALLATION']
    easy_install.main( ["--install-dir", install_path, "lxml"] )
    importlib.reload(site)

import boto3
import pandas as pd
import re
from lxml import html as htmlparser
import datetime
from awsglue.utils import getResolvedOptions
import sys

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
    if obj.key.startswith('html/') and datetime.date.today()-obj.last_modified.date() < datetime.timedelta(7):
        files.append(obj.key)

#alert if input files missing
if not files:
    sns = boto3.resource('sns')
    topic = sns.Topic(alert_topic)
    topic.publish(
        Message = "Missing files in html/ from the last week"
    )

#for logging purpose
infiles = []
outfiles = []

for key in files:
    #output key
    csv_key = key.replace('html/','').replace('.html','.csv')
    nodes = csv_key.split('_')
    dtd = nodes[1][0:8]
    csv_key = 'csv/date={0}/{1}'.format(dtd, csv_key)
    
    #check if output exists
    if list(bucket.objects.filter(Prefix=csv_key)):
        continue
    
    #store in/out file names
    infiles.append(key)
    outfiles.append(csv_key)
    
    #parse input
    f = bucket.Object(key).get()
    html = f['Body'].read().decode('utf-8')
    pos1 = html.find('Latest Price')
    pos1 = html.rfind('<table ', 0, pos1)
    pos2 = html.find('</table>', pos1) + len('</table>')
    html = html[pos1:pos2]
    table = pd.read_html(html)[0]
    
    #add code from href
    parsed = htmlparser.fromstring(html)
    hrefs = parsed.xpath('//tr/td/a/@href')
    codes = [x.split('/')[-1].split('-')[0].upper() for x in hrefs]
    table['Code'] = codes
    
    #rename columns
    new_cols = {}
    mapping = {'+/-':'change','%':'',':':'',' ':'_','.':''}
    for col in table.columns:
        old_col = col
        for k in mapping:
            col = col.replace(k, mapping[k])
        col = re.sub(r"_+$", "", col)
        new_cols[old_col] = col
    table.rename(columns=new_cols, inplace=True)
    table.index.rename('id', inplace=True)
    
    #put output in bucket
    csv = table.to_csv()
    bucket.put_object(Key=csv_key, Body=bytearray(csv, 'utf-8'))

#logging
print("Input files:",infiles)
print("Output files:",outfiles)

