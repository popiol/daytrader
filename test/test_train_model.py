import pytest
import myutils
import pythonjob.glue_utils as glue_utils
import boto3
import numpy as np
import sys
import traceback

class TestTrainModel():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        myutils.copy_from_prod(vars['bucket_name'], 'model/discretizer.pickle')
        myutils.copy_from_prod(vars['bucket_name'], 'model/pricech_model.pickle')
        myutils.copy_from_prod(vars['bucket_name'], 'model/initial_model.zip')
        job_name = vars['id'] + '_train_model'
        res = glue_utils.run_batch_job(job_name, vars['id'])
        vars.update(res)
        return vars

    def test_status(self, vars):
        job_status = vars['job_status']
        assert job_status == 'SUCCEEDED'
