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
import json
import io

class TestEvents():

    ATTRIBUTES = [
        'quote_dt','comp_code','price','low_price','high_price','price2','price1024',
        'ch>10','ch>80','scale','start','end','low2','low1024','high2','high1024'
    ]
    
    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        job_name = vars['id'] + '_events'
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
            if obj.last_modified.strftime('%Y%m%d%H%M%S') >= vars['timestamp'] and obj.key.startswith('events/'):
                files.append(obj.key)
        vars['keys'] = files
        return vars

    def test_status(self, vars):
        job_status = vars['job_status']
        assert job_status == 'SUCCEEDED'
    
    def test_n_files(self, files):
        assert len(files['keys']) > 0
    
    def test_file_keys(self, files):
        for key in files['keys']:
            assert key.startswith('events/date=')
            assert key.endswith('.json')
            assert re.search(r"[0-9]{14}", key)
            assert re.search(r"/date=[0-9]{10}/", key)
    
    def check_header(self, content, key):
        file = io.StringIO(content)
        reader = csv.DictReader(file)
        header = [x.lower() for x in reader.fieldnames]
        if key.startswith('csv_clean'):
            cols = self.COLUMNS
        else:
            cols = self.REJ_COLUMNS
        for col in cols:
            assert col.lower() in header

    def check_count(self, content, key):
        file = io.StringIO(content)
        reader = csv.reader(file)
        n = sum(1 for row in reader)
        if key.startswith('csv_clean'):
            assert n > 40
        else:
            assert n > 1
        
    def test_files(self, files):
        bucket_name = files['bucket_name']
        s3 = boto3.resource('s3')
        for key in files['keys']:
            obj = s3.Object(bucket_name, key)
            content = obj.get()['Body'].read().decode('utf-8')
            obj = json.load(content)
            for attr in self.ATTRIBUTES:
                assert attr in obj
    