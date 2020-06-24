import pytest
import myutils
import glue.pythonjob.glue_utils as glue_utils
import boto3
import numpy as np

class TestDiscretize():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        job_name = vars['id'] + '_discretize'
        myutils.run_glue_job(job_name)
        res = myutils.run_glue_job(job_name)
        vars.update(res)
        return vars

    def test_status(self, vars):
        job_status = vars['job_status']
        assert job_status == 'SUCCEEDED'
    
    def test_discretizer(self, vars):
        bucket_name = vars['bucket_name']
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        discretizer = glue_utils.Discretizer(bucket)
        assert discretizer.n_bins == glue_utils.PRICE_CHANGE_N_BINS
        assert discretizer.n_bins_high == glue_utils.PRICE_CHANGE_N_BINS/2
        assert discretizer.n_bins_low == glue_utils.PRICE_CHANGE_N_BINS/2
        proba = np.histogram(np.random.normal(size=100), bins=discretizer.n_bins)[0]
        price_ch = discretizer.random_price_change(proba)
        assert 2 > price_ch > -1
        proba = np.histogram(np.random.normal(size=100), bins=discretizer.n_bins_high)[0]
        price_ch = discretizer.random_price_change(proba, type="high")
        assert 2 > price_ch > -1
        proba = np.histogram(np.random.normal(size=100), bins=discretizer.n_bins_low)[0]
        price_ch = discretizer.random_price_change(proba, type="low")
        assert 2 > price_ch > -1
