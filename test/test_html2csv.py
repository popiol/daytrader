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

class TestHtml2Csv():

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
            if res['JobRunState'] not in ['STARTING', 'RUNNING', 'STOPPING']:
                break
            time.sleep(60)
        vars['job_status'] = res['JobRunState']
        return vars

    @pytest.fixture(scope='class')
    def files(self):
        vars = self.vars()
        bucket_name = vars['bucket_name']
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        files = []
        for obj in bucket.objects.all():
            if obj.last_modified.strftime('%Y%m%d%H%M%S') >= vars['timestamp']:
                files.append(obj.key)
        vars['files'] = files
        return vars

    def test_status(self, vars):
        job_status = vars['job_status']
        assert job_status == 'SUCCEEDED'
    
    def test_n_files(self, files):
        assert len(files['files']) > 0

    def test_files(self, files):
        bucket_name = files['bucket_name']
        s3 = boto3.resource('s3')
        for f in files:
            obj = s3.Object(bucket_name, f)
            csv = obj.get()['Body'].read().decode('utf-8')
