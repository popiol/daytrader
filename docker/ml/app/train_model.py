import ml_utils
import glue_utils
import numpy as np
import warnings
import os
import random

warnings.filterwarnings("ignore")

quick = int(os.environ['quick']) if "quick" in os.environ else 0
settings = glue_utils.Settings(ml_utils.bucket)
naive = settings.map['naive'] if 'naive' in settings.map else .5
naive2 = random.choices([1, 0], [naive, 1-naive])[0]
naive2 = 1
print("Naive:", naive, "-", "true" if naive2 else "false")
simulator = glue_utils.Simulator(ml_utils.bucket)
dev = ml_utils.Agent('current', ml_utils.bucket)
maxit = 100 if quick else 1000
#for _ in range(maxit):
#    events = simulator.next()
#    dev.train(events, naive=naive2)
print("Capital:", dev.get_capital())

current = ml_utils.Agent('current', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(dev, current, quick=quick)
print("Dev score:", score1, ", Current score:", score2)
if score1 > score2:
    dev.save()

if (naive2 and score1 > score2) or (not naive2 and score1 < score2):
    naive = min(.9, naive + .1)
else:
    naive = max(.1, naive - .1)
settings.map['naive'] = naive
settings.save()
