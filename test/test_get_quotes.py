import boto3
import re
import importlib
import os
import sys
import pytest

class TestGetQuotes():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = {}
        with open('config.tfvars','r') as f:
            for line in f:
                if '=' not in line:
                    continue
                key, val = line.split('=')
                key = key.strip()
                val = val.strip()
                if val[0] == '"' and val[-1] == '"':
                    vars[key] = val[1:-1]
        vars['bucket_name'] = "{}.{}-quotes".format(vars['aws_user'], vars['id'].replace('_','-'))
        return vars

    def test_local(self, vars):
        bucket_name = vars['bucket_name']
        sys.path.insert(0, os.getcwd())
        get_quotes = importlib.import_module("lambda.get_quotes.main")
        res = get_quotes.lambda_handler({"bucket_name": bucket_name}, {})
        assert res['statusCode'] == 200
        assert res['body']['bucket_name'] == bucket_name
        assert len(res['body']['files']) > 0
        files = res['body']['files']
        s3 = boto3.resource('s3')
        for key in files:
            print("file =", key)
            obj = s3.Object(bucket_name, key)
            html = obj.get()['Body'].read().decode('utf-8')
            assert re.match("<table.+<th.+Name.*</th>", html, re.DOTALL)
            assert re.match("<table.+<th.+Latest Price.*</th>", html, re.DOTALL)
            assert re.match("<table.+<th.+Low.*</th>", html, re.DOTALL)
            assert re.match("<table.+<th.+High.*</th>", html, re.DOTALL)
            assert re.match("<table.+<th.+Time.*</th>", html, re.DOTALL)
            assert re.match("<table.+<th.+Date.*</th>", html, re.DOTALL)
