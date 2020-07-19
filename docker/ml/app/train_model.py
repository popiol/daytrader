import ml_utils
import glue_utils
import numpy as np
import warnings
import os
import random

warnings.filterwarnings("ignore")

settings = glue_utils.Settings(ml_utils.bucket)
naive = settings.map['naive'] if 'naive' in settings.map else .5
naive2 = random.choices([1, 0], [naive, 1-naive])[0]
print("Naive:", naive, "-", "true" if naive2 else "false")
dev = ml_utils.Agent('current', ml_utils.bucket)
simulator = glue_utils.Simulator(ml_utils.bucket)
dev.reset()
for _ in range(10):
    events = simulator.next()
    dev.train(events, naive=naive2)
print("Capital:", dev.get_capital())

current = ml_utils.Agent('current', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(dev, current, quick=True)
print("Dev score:", score1, ", Current score:", score2)
print("Capital:", dev.get_capital(), current.get_capital())
if score1 > score2:
    dev.save()

if naive2 and score1 > score2:
    naive = min(.9, naive + .1)
elif not naive2 and score1 < score2:
    naive = min(.9, naive + .05)
elif naive2 and score1 < score2:
    naive = max(.1, naive - .05)
elif not naive2 and score1 > score2:
    naive = max(.1, naive - .1)
settings.map['naive'] = naive
settings.save()
