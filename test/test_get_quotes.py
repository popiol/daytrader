import boto3
import re
import importlib
import os
import sys
import pytest
import json
import get_vars

class TestGetQuotes():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = get_vars.get_vars()
        fun = boto3.client('lambda')
        res = fun.invoke(
            FunctionName = vars['id'] + '_get_quotes',
            InvocationType = 'RequestResponse',
            LogType = 'None',
            Payload = json.dumps(vars),
        )
        vars['status'] = res['StatusCode']
        vars['res'] = json.loads(res['Payload'].read().decode('utf-8'))
        return vars
        
    def test_status(self, vars):
        status = vars['status']
        assert status == 200
        res = vars['res']
        assert res['statusCode'] == 200
        
    def test_bucket_name(self, vars):
        bucket_name = vars['bucket_name']
        res = vars['res']
        assert res['body']['bucket_name'] == bucket_name
        
    def test_n_files(self, vars):
        res = vars['res']
        assert len(res['body']['files']) > 0
    
    def test_files(self, vars):
        bucket_name = vars['bucket_name']
        res = vars['res']
        files = res['body']['files']
        s3 = boto3.resource('s3')
        for key in files:
            obj = s3.Object(bucket_name, key)
            html = obj.get()['Body'].read().decode('utf-8')
            assert re.search("<table.+<th.+Name.*</th>", html, re.DOTALL)
            assert re.search("<table.+<th.+Latest Price.*</th>", html, re.DOTALL)
            assert re.search("<table.+<th.+Low.*</th>", html, re.DOTALL)
            assert re.search("<table.+<th.+High.*</th>", html, re.DOTALL)
            assert re.search("<table.+<th.+Time.*</th>", html, re.DOTALL)
            assert re.search("<table.+<th.+Date.*</th>", html, re.DOTALL)

    