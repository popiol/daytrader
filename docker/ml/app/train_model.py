import ml_utils
import glue_utils
import numpy as np
import warnings
import os
import random

warnings.filterwarnings("ignore")

dev = ml_utils.Agent('current', ml_utils.bucket)
simulator = glue_utils.Simulator(ml_utils.bucket)
dev.reset()
for _ in range(100):
    events = simulator.next()
    dev.train(events)
print("Capital:", dev.get_capital())

current = ml_utils.Agent('current', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(dev, current, quick=True)
print("Dev score:", score1, ", Current score:", score2)
print("Capital:", dev.get_capital(), current.get_capital())
if score1 > score2:
    dev.save()
