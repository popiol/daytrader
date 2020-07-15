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
from boto3.dynamodb.conditions import Key, Attr
import pythonjob.glue_utils as glue_utils

class TestEvents():

    ATTRIBUTES = [
        'quote_dt','comp_code','price','low_price','high_price','price2','price1024',
        'ch>10','ch>80','scale','start','end','low2','low1024','high2','high1024'
    ]
    
    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        job_name = vars['id'] + '_events'
        myutils.run_glue_job(job_name)
        res = myutils.run_glue_job(job_name)
        vars.update(res)
        return vars

    @pytest.fixture(scope='class')
    def dbitems(self, vars):
        event_table_name = vars['id'] + '_events'
        log_table_name = vars['id'] + '_event_process_log'
        db = boto3.resource('dynamodb')
        event_table = db.Table(event_table_name)
        log_table = db.Table(log_table_name)
        res = log_table.query(KeyConditionExpression=Key('process_dt').gte(vars['timestamp']))
        source_files = [x['obj_key'] for x in res['Items']]
        res = event_table.scan(FilterExpression=Attr('source_file').is_in(source_files))
        vars['events'] = res['Items']
        return vars

    def test_status(self, vars):
        job_status = vars['job_status']
        assert job_status == 'SUCCEEDED'
    
    def test_n_files(self, dbitems):
        assert len(dbitems['events']) > 0
    
    def test_file_keys(self, dbitems):
        for event in dbitems['events']:
            assert 'vals' in event
            assert len(event['vals']) > 10
            assert 'price' in event['vals']
    