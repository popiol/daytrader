import ml_utils
import glue_utils
import numpy as np
import warnings

warnings.filterwarnings("ignore")

simulator = glue_utils.HistSimulator(ml_utils.bucket, ml_utils.event_table)
current = ml_utils.Agent('current', ml_utils.bucket, verbose=True)
current.reset()
max_it = 100000
quote_dt = None
for it in range(max_it):
    events = simulator.next()
    if events is None:
        print("Stopping after", it, "iterations, quote_dt:", quote_dt)
        break
    quote_dt = events[0].event['quote_dt']
    current.test(events)
print("Capital:", current.get_capital())
print("Bought/Sold:", current.n_bought, "/", current.n_sold)
print("Score:", current.score)
