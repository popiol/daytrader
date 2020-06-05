import pytest
import myutils
import glue.pythonjob.glue_utils as glue_utils
import boto3

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
        discretizer = glue_utils.get_discretizer(bucket)
        n_bins = discretizer.n_bins_[0]
        assert n_bins == glue_utils.PRICE_CHANGE_N_BINS
        proba = [1] * n_bins
        price_ch = glue_utils.random_price_change(discretizer, proba)
        assert 2 > price_ch > -1
