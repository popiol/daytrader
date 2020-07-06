import ml_utils
import glue_utils
import numpy as np

for _ in range(100):
    simulator = glue_utils.Simulator(ml_utils.bucket)
    agent = ml_utils.Agent('initial', ml_utils.bucket)
    for _ in range(2500):
        events = simulator.next()
        agent.train_init(events)
    agent.save()
    print("Capital:", agent.get_capital())
