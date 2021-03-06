import pytest
import myutils
import pythonjob.glue_utils as glue_utils
import boto3
import numpy as np

class TestHistSimulator():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        bucket_name = vars['bucket_name']
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        event_table_name = vars['id'] + '_events'
        db = boto3.resource('dynamodb')
        vars['simulator'] = glue_utils.HistSimulator(db, event_table_name)
        return vars

    def test_events(self, vars):
        simulator = vars['simulator']
        events = simulator.next()
        assert len(events) >= glue_utils.MIN_EVENTS_LEN
        comp_codes = {}
        for event in events:
            comp_code = event.event['comp_code']
            assert 1 <= len(comp_code) <= 5
            assert 'A' <= comp_code <= 'ZZZZZ'
            comp_codes[comp_code] = event
        assert len(comp_codes) >= glue_utils.MIN_EVENTS_LEN
        events = simulator.next()
        for event in events:
            comp_code = event.event['comp_code']
            if comp_code not in comp_codes:
                continue
            price1 = comp_codes[comp_code].event['price']
            price2 = event.event['price']
            price_ch = price2 / price1 - 1
            assert -1 < price_ch < 2
            high_price2 = event.event['high_price']
            high_price_ch = high_price2 / price1 - 1
            assert -1 < high_price_ch < 2
            low_price2 = event.event['low_price']
            low_price_ch = low_price2 / price1 - 1
            assert -1 < low_price_ch < 2
            