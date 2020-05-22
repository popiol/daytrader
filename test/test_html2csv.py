import boto3
import re
import importlib
import os
import sys
import pytest
import json
import myutils
import time
import datetime
import csv
import io

class TestHtml2Csv():

    COLUMNS = ['id','Name','Latest_Price_Previous_Close','Low_High','change','Time_Date','Code']

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        job_name = vars['id'] + '_html2csv'
        vars['job_name'] = job_name
        res = myutils.run_glue_job(job_name)
        vars.update(res)
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
        assert len(files['keys']) >= 10
    
    def test_file_keys(self, files):
        for key in files['keys']:
            assert key.startswith('csv/date=')
            assert key.endswith('.csv')
            assert re.search(r"[0-9]{14}", key)
            assert re.search(r"/date=[0-9]{8}/", key)
    
    def check_header(self, content):
        file = io.StringIO(content)
        reader = csv.DictReader(file)
        header = [x.lower() for x in reader.fieldnames]
        for col in self.COLUMNS:
            assert col.lower() in header

    def check_count(self, content):
        file = io.StringIO(content)
        reader = csv.reader(file)
        n = sum(1 for row in reader)
        assert n > 40
        
    def test_files(self, files):
        bucket_name = files['bucket_name']
        s3 = boto3.resource('s3')
        for key in files['keys']:
            obj = s3.Object(bucket_name, key)
            csv = obj.get()['Body'].read().decode('utf-8')
            self.check_header(csv)
            self.check_count(csv)

    def test_failure(self, vars):
        job_name = vars['job_name']
        res = myutils.run_glue_job(job_name, {'--bucket_name':''})
        assert res['job_status'] == 'FAILED'
    
