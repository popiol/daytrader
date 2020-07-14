import pytest
import myutils
import pythonjob.glue_utils as glue_utils
import boto3
import numpy as np
import sys
import traceback

class TestTrainInit():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        myutils.copy_from_prod(vars['bucket_name'], 'model/discretizer.pickle')
        myutils.copy_from_prod(vars['bucket_name'], 'model/pricech_model.pickle')
        job_name = vars['id'] + '_test_train_init'
        res = glue_utils.run_batch_job(job_name, vars['id'])
        #job_name = vars['id'] + '_train_init'
        #res = myutils.run_glue_job(job_name)
        vars.update(res)
        return vars

    def test_status(self, vars):
        job_status = vars['job_status']
        assert job_status == 'SUCCEEDED'

    def test_agent_exists(self, vars):
        bucket_name = vars['bucket_name']
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        obj_key = f'model/dev_model.zip'
        bucket.Object(obj_key).get()
