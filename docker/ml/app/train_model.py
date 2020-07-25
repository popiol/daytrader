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
    for _ in range(1000):
        simulator.next()
    hist = []
    for _ in range(40):
        hist.append(simulator.next())
    best_score = None
    for _ in range(10):
        dev = ml_utils.Agent('current', ml_utils.bucket)
        dev.set_max_w(max_w, max_c, max_s)
        events = simulator.next()
        inputs, outputs, grad, sign = dev.train(events)
        dev.reset()
        for events in hist:
            dev.test(events)
        if best_score is None or dev.score > best_score:
            best_dev = dev
            best_score = dev.score
            best_inp = inputs
            best_out = outputs
            best_grad = grad
            best_sign = sign
            max_w, max_c, max_s = dev.get_max_w()
        print("Capital:", dev.get_capital())
        print("Score:", dev.score)

    print("---- Best score", best_score, "----")
    best_dev.save_as('dev')
    for _ in range(10):
        outputs = []
        for outputs1, grad in zip(best_out, best_grad):
            outputs.append([min(1, max(-1, 2*x-(x/s-y))) for x, y, s in zip(outputs1, grad, best_sign)])
        best_dev.fit(best_inp, outputs)
        best_dev.reset()
        for events in hist:
            best_dev.test(events)
        print("Capital:", best_dev.get_capital())
        print("Score:", best_dev.score)
        if best_dev.score > best_score:
            best_score = best_dev.score
            best_dev.save()
            best_out = outputs
        else:
            break

    #dev = ml_utils.Agent('dev', ml_utils.bucket, verbose=True)
    #for events in hist:
    #    dev.test(events)
    #print("Capital:", dev.get_capital())

dev = ml_utils.Agent('dev', ml_utils.bucket)
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
if score1 > score2:
    settings.map['max_w'] = max_w
    settings.map['max_c'] = max_c
    settings.map['max_s'] = max_s
settings.save()

print()
