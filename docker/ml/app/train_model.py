import ml_utils
import glue_utils
import numpy as np
import warnings
import os

warnings.filterwarnings("ignore")

if "quick" in os.environ:
    quick = int(os.environ['quick'])

simulator = glue_utils.Simulator(ml_utils.bucket)
dev = ml_utils.Agent('current', ml_utils.bucket)
maxit = 100 if quick else 1000
for _ in range(maxit):
    events = simulator.next()
    dev.train(events)
print("Capital:", dev.get_capital())

current = ml_utils.Agent('current', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(dev, current, quick=quick)
print("Dev score:", score1, ", Current score:", score2)
if score1 > score2:
    dev.save()
