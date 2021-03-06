import boto3
import datetime
import time
import json
import os
import pythonjob.glue_utils as glue_utils

def get_vars():
    vars = {}

    #read vars from config.tfvars
    with open('config.tfvars','r') as f:
        for line in f:
            if '=' not in line:
                continue
            key, val = line.split('=')
            key = key.strip()
            val = val.strip()
            if val[0] == '"' and val[-1] == '"':
                vars[key] = val[1:-1]
    
    #add bucket name
    vars['bucket_name'] = "{}.{}-quotes".format(vars['aws_user'], vars['id'].replace('_','-'))

    #find sns
    sns_arn = ""
    sns = boto3.client('sns')
    topics = sns.list_topics()['Topics']
    for topic in topics:
        arn = topic['TopicArn']
        tags = sns.list_tags_for_resource(ResourceArn=arn)['Tags']
        for tag in tags:
            if tag['Key'] == 'id' and tag['Value'] == vars['id']:
                sns_arn = arn
                break
        if sns_arn:
            break
    vars['alert_topic'] = sns_arn

    #get terraform outputs
    #os.system('terraform init')
    #os.system('terraform output > out.txt')
    #with open('out.txt','r') as f:
    #    for line in f:
    #        if '=' not in line:
    #            continue
    #        key, val = line.split('=')
    #        key = key.strip()
    #        val = val.strip()
    #        vars[key] = val

    return vars

def run_glue_job(job_name, args={}):
    vars = {}
    glue = boto3.client('glue')

    while True:
        try:
            vars['timestamp'] = datetime.datetime.utcnow().strftime(glue_utils.DB_DATE_FORMAT)
            res = glue.start_job_run(
                JobName = job_name,
                Arguments = args
            )
        except glue.exceptions.ConcurrentRunsExceededException:
            time.sleep(10)
        else:
            break
    run_id = res['JobRunId']
    for _ in range(10):
        res = glue.get_job_run(
            JobName = job_name,
            RunId = run_id
        )
        if res['JobRun']['JobRunState'] not in ['STARTING', 'RUNNING', 'STOPPING']:
            break
        time.sleep(60)
    vars['job_status'] = res['JobRun']['JobRunState']
    if vars['job_status'] == 'FAILED':
        vars['aaa_error'] = res['JobRun']['ErrorMessage']
    return vars

def run_lambda_fun(fun_name, inp, sync=True):
    vars = {}
    fun = boto3.client('lambda')
    res = fun.invoke(
        FunctionName = fun_name,
        InvocationType = 'RequestResponse' if sync else 'Event',
        LogType = 'None',
        Payload = json.dumps(inp),
    )
    vars['status'] = res['StatusCode']
    if sync:
        vars['res'] = json.loads(res['Payload'].read().decode('utf-8'))
        if vars['status'] != 200:
            vars['aaa_error'] = res['FunctionError']
    return vars

def copy_from_prod(bucket_name, obj_key):
    prod_bucket_name = 'popiol.daytrader-master-quotes'
    if prod_bucket_name == bucket_name:
        return
    filename = 'tmp_' + obj_key.split('/')[-1]
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(prod_bucket_name)
    bucket.Object(obj_key)
    bucket.download_file(obj_key, filename)
    bucket = s3.Bucket(bucket_name)
    bucket.upload_file(filename, obj_key)
