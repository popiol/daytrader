import pytest
import myutils
import glue.pythonjob.glue_utils as glue_utils
import boto3
import numpy as np
import sys
import traceback

class TestTrainInit():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        print("debug 1", file=sys.stderr)
        job_name = vars['id'] + '_test_train_init'
        try:
            res = glue_utils.run_batch_job(job_name, vars['id'], vars['ec2_template_ml_id'])
            print(res, file=sys.stderr)
        except:
            print(traceback.format_exc().splitlines()[-2:], file=sys.stderr)
        print("debug 2", file=sys.stderr)
        vars.update(res)
        return vars

    def test_status(self, vars):
        job_status = vars['job_status']
        assert job_status == 'SUCCEEDED'
