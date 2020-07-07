import ml_utils
import glue_utils
import numpy as np
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

for _ in range(10):
    simulator = glue_utils.Simulator(ml_utils.bucket)
    agent = ml_utils.Agent('initial', ml_utils.bucket)
    for _ in range(1000):
        events = simulator.next()
        agent.train_init(events)
    agent.save()
    print("Capital:", agent.get_capital())

simulator.print_sample_quotes()
