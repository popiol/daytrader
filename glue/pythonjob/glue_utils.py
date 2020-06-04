import pickle
import random
import math

PRICE_CHANGE_N_BINS = 10

def create_event_key(comp_code, quote_dt):
    dt = quote_dt[:13].replace('-','').replace(' ','')
    dt2 = quote_dt.replace('-','').replace(' ','').replace(':','')
    return "events/date={}/{}_{}.json".format(dt, comp_code, dt2)

def get_discretizer(bucket):
    obj_key = 'model/discretizer.pickle'
    f = bucket.Object(obj_key).get()
    discretizer = f['Body'].read().decode('utf-8')
    return pickle.loads(discretizer)

def random_price_change(discretizer, proba):
    proba[1] += proba[0]
    proba[-2] += proba[-1]
    n = random.choices(range(1,discretizer.n_bins_[0]-1), proba[1:-1])
    start = discretizer.bin_edges_[0][n]
    end = discretizer.bin_edges_[0][n+1]
    start = max(start-(end-start)/2, -.9)
    end = end+(end-start)/2
    return random.uniform(start, end)
