import pytest
import myutils
import glue.pythonjob.glue_utils as glue_utils
import boto3
import numpy as np
import sys

class TestTrainInit():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        print("debug 1", file=sys.stderr)
        job_name = vars['id'] + '_train_init'
        res = glue_utils.run_batch_job(job_name, vars['ec2_template_ml_id'], vars['id'])
        print("debug 2", file=sys.stderr)
        print(res, file=sys.stderr)
        vars.update(res)
        return vars

    def test_status(self, vars):
        job_status = vars['job_status']
        assert job_status == 'SUCCEEDED'
