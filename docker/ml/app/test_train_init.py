import ml_utils
import glue_utils
import numpy as np
import os
import warnings

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
simulator = glue_utils.Simulator(ml_utils.bucket)
agent = ml_utils.Agent('dev', ml_utils.bucket)
n_orders = []
portfolio_size = []
capital = agent.get_capital()
capital_ch = []
for _ in range(100):
    events = simulator.next()
    agent.train_init(events)
    n_orders.append(len(agent.orders))
    portfolio_size.append(len(agent.portfolio))
    capital_ch.append(agent.get_capital() / capital - 1)
    capital = agent.get_capital()
    assert agent.cash > 0
    assert capital > 0
assert max(n_orders) > 0
assert max(portfolio_size) > 0
assert 1 > max(max(capital_ch), abs(min(capital_ch))) > 0
assert min(capital_ch) > -1
agent.save()
agent2 = ml_utils.Agent('dev2', ml_utils.bucket)
