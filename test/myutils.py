import boto3
import datetime
import time

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

    return vars

def run_glue_job(job_name):
    vars = {}
    glue = boto3.client('glue')
    vars['timestamp'] = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
    res = glue.start_job_run(
        JobName = job_name
    )
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
    return vars