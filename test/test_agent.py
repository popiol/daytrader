import pytest
import myutils
import glue.pythonjob.glue_utils as glue_utils
import boto3
import numpy as np

class TestAgent():

    @pytest.fixture(scope='class')
    def vars(self):
        vars = myutils.get_vars()
        bucket_name = vars['bucket_name']
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        vars['simulator'] = glue_utils.Simulator(bucket)
        vars['agent'] = glue_utils.Agent(bucket)
        return vars

    def test_train_init(self, vars):
        simulator = vars['simulator']
        agent = vars['agent']
        n_orders = []
        portfolio_size = []
        cash = agent.cash
        cash_ch = []
        for _ in range(100):
            events = simulator.next()
            agent.train_init(events)
            n_orders.append(len(agent.orders))
            portfolio_size.append(len(agent.portfolio))
            cash_ch.append(agent.cash / cash - 1)
            cash = agent.cash
            assert cash > 0
        assert max(n_orders) > 0
        assert max(portfolio_size) > 0
        assert 1 > max(max(cash_ch), abs(min(cash_ch))) > 0
        assert min(cash_ch) > -.1    
