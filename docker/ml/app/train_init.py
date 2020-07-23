import ml_utils
import glue_utils
import numpy as np
import warnings

warnings.filterwarnings("ignore")

simulator = glue_utils.Simulator(ml_utils.bucket)
initial = ml_utils.Agent('initial', ml_utils.bucket)
for _ in range(1000):
    events = simulator.next()
    print(events[0].event['quote_dt'])
    initial.train_init(events)
initial.save()
print("Capital:", initial.get_capital())

simulator.print_sample_quotes()

current = ml_utils.Agent('current', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(initial, current)
print("Initial score:", score1, ", Current score:", score2)
if score1 > score2:
    initial.save_as('current')
