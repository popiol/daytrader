import boto3
import re
import importlib
import os
import sys
import pytest
import json
import get_vars
import time
import datetime
import csv
import io

class TestHtml2Csv():

    COLUMNS = ['id','Name','Latest_Price_Previous_Close','Low_High','change','Time_Date','Code']

    @pytest.fixture(scope='class')
    def vars(self):
        vars = get_vars.get_vars()
        job_name = vars['id'] + '_html2csv'
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

    @pytest.fixture(scope='class')
    def files(self, vars):
        bucket_name = vars['bucket_name']
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        files = []
        for obj in bucket.objects.all():
            if obj.last_modified.strftime('%Y%m%d%H%M%S') >= vars['timestamp']:
                files.append(obj.key)
        vars['keys'] = files
        return vars

    def test_status(self, vars):
        job_status = vars['job_status']
        assert job_status == 'SUCCEEDED'
    
    def test_n_files(self, files):
        assert len(files['keys']) > 0
    
    def check_header(self, content):
        file = io.StringIO(content)
        reader = csv.reader(file)
        header = [x.lower() for x in reader.fieldnames]
        for col in self.COLUMNS:
            assert col.lower() in header

    def check_count(self, content):
        file = io.StringIO(content)
        reader = csv.DictReader(file)
        n = sum(1 for row in reader)
        assert n > 40
        
    def test_files(self, files):
        bucket_name = files['bucket_name']
        s3 = boto3.resource('s3')
        for f in files['keys']:
            obj = s3.Object(bucket_name, f)
            csv = obj.get()['Body'].read().decode('utf-8')
            self.check_header(csv)
            self.check_count(csv)
