import ml_utils
import glue_utils
import numpy as np
import warnings

warnings.filterwarnings("ignore")

current = ml_utils.Agent('current', ml_utils.bucket)
prod = ml_utils.Agent('prod', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(current, prod, quick=True)
print("Current score:", score1, ", Prod score:", score2)
print("Price up/down:", np.average(current.price_up), "/", np.average(current.price_down))
if score1 > score2:
    score1, score2 = ml_utils.compare_agents(current, prod, hist=True, quick=True)
    print("Current score:", score1, ", Prod score:", score2)
    print("Price up/down:", np.average(current.price_up), "/", np.average(current.price_down))
    if score1 > score2:
        current.save_as('prod')
else:
    score1, score2 = ml_utils.compare_agents(current, prod, hist=True, quick=True)
    print("Current score:", score1, ", Prod score:", score2)
    print("Price up/down:", np.average(current.price_up), "/", np.average(current.price_down))
