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

class TestCleanQuotes():

    REJ_COLUMNS = ['id','Name','Latest_Price_Previous_Close','Low_High','Time_Date','Code','error_message']
    COLUMNS = ['row_id','quote_dt','comp_code','price','low_price','high_price']
    SAMPLE = ['1','ASD Inc.','10.10 9.52','10.01 10.20','04:15 PM 07.02.2020','ASD']
    
    def write_wrong_id(self, writer):
        row = dict(zip(self.REJ_COLUMNS[:-1], self.SAMPLE))
        row['id'] = 'asd'
        writer.writerow(row)

    def write_wrong_code(self, writer):
        row = dict(zip(self.REJ_COLUMNS[:-1], self.SAMPLE))
        row['Code'] = '1234567890123456789'
        writer.writerow(row)

    def write_wrong_price(self, writer):
        row = dict(zip(self.REJ_COLUMNS[:-1], self.SAMPLE))
        row['Latest_Price_Previous_Close'] = 'asd'
        writer.writerow(row)

    def create_fake_file(self, vars):
        f = io.StringIO()
        writer = csv.DictWriter(f, fieldnames=self.REJ_COLUMNS[:-1])
        self.write_wrong_id(writer)
        self.write_wrong_code(writer)
        self.write_wrong_price(writer)
        s3 = boto3.resource('s3')
        bucket_name = vars['bucket_name']
        bucket = s3.Bucket(bucket_name)
        bucket.put_object(
            Key = 'csv/date=20200101/fake_20200202151515.csv',
            Body = bytearray(contents)
        )

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        self.create_fake_file(vars)
        job_name = vars['id'] + '_clean_quotes'
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
        n_clean = 0
        n_rejected = 0
        for key in files['keys']:
            if key.startswith('csv_clean'):
                n_clean += 1
            else:
                n_rejected += 1
        assert n_clean >= 10
        assert n_rejected > 0
    
    def test_file_keys(self, files):
        for key in files['keys']:
            assert key.startswith('csv_clean/date=') or key.startswith('csv_rejected/date=')
            assert key.endswith('.csv')
            assert re.search(r"[0-9]{14}", key)
            assert re.search(r"/date=[0-9]{8}/", key)
    
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
            csv = obj.get()['Body'].read().decode('utf-8')
            self.check_header(csv, key)
            self.check_count(csv, key)

    