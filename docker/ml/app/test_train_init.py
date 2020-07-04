import ml_utils
import glue_utils
import numpy as np

simulator = glue_utils.Simulator(ml_utils.bucket)
agent = ml_utils.Agent('dev', ml_utils.bucket)
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
assert min(cash_ch) > -1
agent.save()
agent2 = ml_utils.Agent('dev2', ml_utils.bucket)
