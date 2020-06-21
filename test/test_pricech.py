import pytest
import myutils
import glue.pythonjob.glue_utils as glue_utils
import boto3
import numpy as np

class TestPriceCh():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        job_name = vars['id'] + '_pricech_model'
        myutils.run_glue_job(job_name)
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
        objs = bucket.objects.all()
        for obj in objs:
            if obj.key.startswith('events/'):
                obj_key = obj.key
                break
        model = glue_utils.PriceChModel(bucket)
        event = glue_utils.Event(bucket=bucket, obj_key=obj_key)
        y = model.predict_proba([event.get_inputs()])
        assert np.shape(y) == (1, glue_utils.PRICE_CHANGE_N_BINS*2)
        for x in y[0]:
            assert 0 <= x <= 1
