import boto3
import re
import importlib
import os
import sys
import pytest
import json
import myutils

class TestGetQuotes():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        fun_name = vars['id'] + '_get_quotes'
        vars['fun_name'] = fun_name
        res = myutils.run_lambda_fun(fun_name, vars)
        vars.update(res)
        return vars
        
    def test_failure(self, vars):
        fun_name = vars['fun_name']
        res = myutils.run_lambda_fun(fun_name, {}, sync=False)
        status = res['status']
        assert status == 202
    
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
        assert len(res['body']['files']) >= 10
    
    def test_file_keys(self, vars):
        res = vars['res']
        files = res['body']['files']
        for key in files:
            assert key.startswith('html/')
            assert key.endswith('.html')
            assert re.search(r"[0-9]{14}", key)
    
    def test_files(self, vars):
        bucket_name = vars['bucket_name']
        res = vars['res']
        files = res['body']['files']
        s3 = boto3.resource('s3')
        for key in files:
            obj = s3.Object(bucket_name, key)
            html = obj.get()['Body'].read().decode('utf-8')
            assert re.search(r"<table.+<th.+Name.*</th>", html, re.DOTALL)
            assert re.search(r"<table.+<th.+Latest Price.*</th>", html, re.DOTALL)
            assert re.search(r"<table.+<th.+Low.*</th>", html, re.DOTALL)
            assert re.search(r"<table.+<th.+High.*</th>", html, re.DOTALL)
            assert re.search(r"<table.+<th.+Time.*</th>", html, re.DOTALL)
            assert re.search(r"<table.+<th.+Date.*</th>", html, re.DOTALL)

    