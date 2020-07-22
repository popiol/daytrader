import ml_utils
import glue_utils
import numpy as np
import warnings
import os
import random

warnings.filterwarnings("ignore")

simulator = glue_utils.Simulator(ml_utils.bucket)
hist = []
for _ in range(10):
    hist.append(simulator.next())
best_score = None
for _ in range(10):
    dev = ml_utils.Agent('current', ml_utils.bucket)
    events = simulator.next()
    dev.train(events)
    dev.reset()
    for events in hist:
        dev.test(events)
    if best_score is None or dev.score > best_score:
        best_dev = dev
        best_score = dev.score
    print("Capital:", dev.get_capital())

dev = best_dev
current = ml_utils.Agent('current', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(dev, current, quick=True)
print("Dev score:", score1, ", Current score:", score2)
print("Capital:", dev.get_capital(), current.get_capital())
if score1 > score2:
    dev.save()
