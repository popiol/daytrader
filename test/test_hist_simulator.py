import pytest
import myutils
import glue.pythonjob.glue_utils as glue_utils
import boto3
import numpy as np

class TestHistSimulator():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        bucket_name = vars['bucket_name']
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        vars['simulator'] = glue_utils.HistSimulator(bucket)
        return vars

    def test_events(self, vars):
        simulator = vars['simulator']
        events = simulator.next()
        assert len(events) > .2 * glue_utils.SIM_N_COMPS
        comp_codes = {}
        for event in events:
            comp_code = event.event['comp_code']
            assert 1 <= len(comp_code) <= 4
            assert 'A' <= comp_code <= 'ZZZZ'
            comp_codes[comp_code] = event
        assert len(comp_codes) > .2 * glue_utils.SIM_N_COMPS
        events = simulator.next()
        n_same = sum(1 if x.event['comp_code'] in comp_codes else 0 for x in events)
        assert n_same > .2 * glue_utils.SIM_N_COMPS
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
            
