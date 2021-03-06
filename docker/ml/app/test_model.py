import ml_utils
import glue_utils
import numpy as np
import warnings

warnings.filterwarnings("ignore")

current = ml_utils.Agent('current', ml_utils.bucket)
prod = ml_utils.Agent('prod', ml_utils.bucket)
score1, score2 = ml_utils.compare_agents(current, prod)
print("Current score:", score1, ", Prod score:", score2)
better = True if score1 > score2 else False
score1, score2 = ml_utils.compare_agents(current, prod, hist=True)
print("Current score:", score1, ", Prod score:", score2)
if better and score1 > score2:
    current.save_as('prod')
