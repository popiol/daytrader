import ml_utils
import glue_utils
import numpy as np
import warnings

warnings.filterwarnings("ignore")

simulator = glue_utils.HistSimulator(ml_utils.bucket, ml_utils.event_table)
current = ml_utils.Agent('current', ml_utils.bucket, verbose=True)
current.reset()
max_it = 10
quote_dt = None
for it in range(max_it):
    glue_utils.logg(f"It: {it}")
    events = simulator.next()
    if events is None:
        glue_utils.logg(f"Stopping after {it} iterations, quote_dt: {quote_dt}")
        break
    quote_dt = events[0].event['quote_dt']
    glue_utils.logg(f"{quote_dt}, # events: {len(events)}")
    current.test(events)
print("Capital:", current.get_capital())
print("Bought/Sold:", current.n_bought, "/", current.n_sold)
print("Score:", current.score)
