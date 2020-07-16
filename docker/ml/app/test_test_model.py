import ml_utils
import glue_utils
import numpy as np
import warnings
import math

warnings.filterwarnings("ignore")
for hist in range(2):
    if hist:
        simulator = glue_utils.HistSimulator(ml_utils.bucket, ml_utils.event_table)
    else:
        simulator = glue_utils.Simulator(ml_utils.bucket)
    agent = ml_utils.Agent('dev', ml_utils.bucket)
    n_orders = []
    portfolio_size = []
    capital = agent.get_capital()
    capital_ch = []
    prev_day = None
    ndays = 0
    for _ in range(1000):
        if ndays > 10:
            break
        events = simulator.next()
        if not ml_utils.temporary:
            assert events is not None
        if events is None:
            break
        day = int(events[0].event['quote_dt'][8:10])
        if prev_day is not None and day != prev_day:
            ndays += 1
        prev_day = day
        agent.test(events)
        n_orders.append(len(agent.orders))
        portfolio_size.append(len(agent.portfolio))
        capital_ch.append(agent.get_capital() / capital - 1)
        capital = agent.get_capital()
        assert agent.cash > 0
        assert capital > 0
    print("Capital:", agent.get_capital())
    assert max(n_orders) > 0
    assert max(portfolio_size) > 0
    assert 1 > max(max(capital_ch), abs(min(capital_ch))) > 0
    assert min(capital_ch) > -1
    if hist:
        simulator.print_sample_quotes()
