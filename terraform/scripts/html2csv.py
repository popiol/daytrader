import os

if 'GLUE_INSTALLATION' in os.environ.keys():
    import site
    import importlib
    from setuptools.command import easy_install
    install_path = os.environ['GLUE_INSTALLATION']
    easy_install.main( ["--install-dir", install_path, "lxml"] )
    importlib.reload(site)

import boto3
import argparse
import pandas as pd
import re

parser = argparse.ArgumentParser()
parser.add_argument('--scriptLocation')
args, unknown = parser.parse_known_args()
script = args.scriptLocation
bucket = script.split('/')[2]

s3 = boto3.client('s3')
objs = s3.list_objects(Bucket=bucket, Prefix="html/")

files = [x['Key'] for x in objs['Contents']]

print("Input files:",files)

outfiles = []

for key in files:
    f = s3.get_object(Bucket=bucket, Key=key)
    html = f['Body'].read().decode('utf-8')
    pos1 = html.find('Latest Price')
    pos1 = html.rfind('<table ', 0, pos1)
    pos2 = html.find('</table>', pos1) + len('</table>')
    html = html[pos1:pos2]
    table = pd.read_html(html)[0]
    new_cols = {}
    mapping = {'+/-':'change','%':'',':':'',' ':'_','.':''}
    for col in table.columns:
        old_col = col
        for k in mapping:
            col = col.replace(k, mapping[k])
        col = re.sub(r"_+$", r"", col)
        new_cols[old_col] = col
    table.rename(columns=new_cols, inplace=True)
    table.index.rename('id', inplace=True)
    csv = table.to_csv()
    csv_key = key.replace('html/','').replace('.html','.csv')
    nodes = csv_key.split('_')
    dtd = nodes[1][0:8]
    csv_key = 'csv/date={0}/{1}'.format(dtd, csv_key)
    outfiles.append(csv_key)
    s3.put_object(Bucket=bucket, Key=csv_key, Body=bytearray(csv, 'utf-8'))

print("Output files:",outfiles)

