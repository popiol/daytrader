import pytest
import myutils
import pythonjob.glue_utils as glue_utils
import boto3
import numpy as np

class TestPriceCh():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        job_name = vars['id'] + '_events'
        myutils.run_glue_job(job_name, {'--repeat': '20'})
        job_name = vars['id'] + '_pricech_model'
        res = myutils.run_glue_job(job_name)
        vars.update(res)
        return vars

    def test_status(self, vars):
        job_status = vars['job_status']
        assert job_status == 'SUCCEEDED'
    
    def test_model(self, vars):
        bucket_name = vars['bucket_name']
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        event_table_name = vars['id'] + '_events'
        db = boto3.resource('dynamodb')
        event_table = db.Table(event_table_name)
        model = glue_utils.PriceChModel(bucket)
        res = event_table.scan()
        item = res['Items'][0]
        event = glue_utils.Event(event_table=event_table, comp_code=item['comp_code'], quote_dt=item['quote_dt'])
        assert model.get_input_shape() == np.shape(event.get_inputs())
        discretizer = glue_utils.Discretizer(bucket)
        y = model.predict_proba(event.get_inputs())
        assert len(y) == sum(discretizer.n_bins)
        for x in y:
            assert 0 <= x <= 1
        price_class = y[:discretizer.n_bins[0]]
        high_class = y[discretizer.n_bins[0]:discretizer.n_bins[0]+discretizer.n_bins[1]]
        low_class = y[discretizer.n_bins[0]+discretizer.n_bins[1]:]
        assert max(price_class) > 0
        assert min(price_class) < 1
        assert min(price_class) < max(price_class)
        assert max(high_class) > 0
        assert min(high_class) < 1
        assert min(high_class) < max(high_class)
        assert max(low_class) > 0
        assert min(low_class) < 1
        assert min(low_class) < max(low_class)
