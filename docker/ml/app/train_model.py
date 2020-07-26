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
max_w = settings.map['max_w'] if 'max_w' in settings.map else 1
max_c = settings.map['max_c'] if 'max_c' in settings.map else .1
max_s = settings.map['max_s'] if 'max_s' in settings.map else 2
print("Max_w:", max_w, max_c, max_s)

simulator = glue_utils.Simulator(ml_utils.bucket)
if naive2:
    dev = ml_utils.Agent('current', ml_utils.bucket)
    for _ in range(440):
        events = simulator.next()
        dev.train_init(events)
    dev.save_as('dev')
else:
    hist = []
    for _ in range(40):
        hist.append(simulator.next())
    best_score = None
    for _ in range(10):
        dev = ml_utils.Agent('current', ml_utils.bucket)
        dev.set_max_w(max_w, max_c, max_s)
        events = simulator.next()
        dev.train(events)
        dev.reset()
        for events in hist:
            dev.test(events)
        if best_score is None or dev.score > best_score:
            best_dev = dev
            best_score = dev.score
            max_w, max_c, max_s = dev.get_max_w()
        print("Capital:", dev.get_capital())
        print("Score:", dev.score)
    print("---- Best score", best_score, "----")
    best_dev.save_as('dev')

dev = ml_utils.Agent('dev', ml_utils.bucket)
current = ml_utils.Agent('current', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(dev, current, quick=True)
print("Dev score:", score1, ", Current score:", score2)
if score1 > score2:
    dev.save_as('current')

if naive2 and score1 > score2:
    naive = min(.9, naive + .1)
elif not naive2 and score1 < score2:
    naive = min(.9, naive + .05)
elif naive2 and score1 < score2:
    naive = max(.1, naive - .05)
elif not naive2 and score1 > score2:
    naive = max(.1, naive - .1)
settings.map['naive'] = naive
if score1 > score2:
    settings.map['max_w'] = max_w
    settings.map['max_c'] = max_c
    settings.map['max_s'] = max_s
settings.save()

glue_utils.logg("Finish")
print()
