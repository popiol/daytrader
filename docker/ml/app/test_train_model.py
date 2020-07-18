import ml_utils
import glue_utils
import numpy as np
import warnings

warnings.filterwarnings("ignore")

simulator = glue_utils.Simulator(ml_utils.bucket)
dev = ml_utils.Agent('current', ml_utils.bucket)
for _ in range(100):
    events = simulator.next()
    dev.train(events)
print("Capital:", dev.get_capital())

current = ml_utils.Agent('current', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(dev, current, quick=True)
print("Dev score:", score1, ", Current score:", score2)
if score1 > score2:
    dev.save()
