import ml_utils
import glue_utils
import numpy as np
import warnings

warnings.filterwarnings("ignore")

simulator = glue_utils.Simulator(ml_utils.bucket)
hist = []
for _ in range(100):
    hist.append(simulator.next())
initial = ml_utils.Agent('initial', ml_utils.bucket)
for events in hist:
    initial.test(events)
print("Capital:", initial.get_capital())
for events in hist:
    initial.train_init(events)
initial.save()
initial = ml_utils.Agent('initial', ml_utils.bucket, verbose=True)
for events in hist:
    initial.test(events)
print("Capital:", initial.get_capital())

#simulator.print_sample_quotes()

initial = ml_utils.Agent('initial', ml_utils.bucket)
current = ml_utils.Agent('current', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(initial, current, quick=True)
print("Initial score:", score1, ", Current score:", score2)
if score1 > score2:
    initial.save_as('current')
print()
