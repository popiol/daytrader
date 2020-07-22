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
        #best_inp = inputs
        #best_out = outputs
        #best_grad = grad
    print("Capital:", dev.get_capital())
    print("Score:", dev.score)

print("---- Best score", best_score, "----")
best_dev.save_as('dev')
for _ in range(10):
    outputs = []
    for outputs1, grad in zip(best_out, best_grad):
        outputs.append([min(1, max(-1, x + y)) for x, y in zip(outputs1, grad)])
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

dev = ml_utils.Agent('dev', ml_utils.bucket)
current = ml_utils.Agent('current', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(dev, current, quick=True)
print("Dev score:", score1, ", Current score:", score2)
print("Capital:", dev.get_capital(), current.get_capital())
if score1 > score2:
    dev.save()
