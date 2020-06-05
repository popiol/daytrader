import pickle
import random
import math

PRICE_CHANGE_N_BINS = 10
DB_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def create_event_key(comp_code, quote_dt):
    dt = quote_dt[:13].replace('-','').replace(' ','')
    dt2 = quote_dt.replace('-','').replace(' ','').replace(':','')
    return "events/date={}/{}_{}.json".format(dt, comp_code, dt2)

def get_discretizer(bucket):
    obj_key = 'model/discretizer.pickle'
    f = bucket.Object(obj_key).get()
    discretizer = f['Body'].read()
    return pickle.loads(discretizer)

def random_price_change(discretizer, proba):
    n = len(proba)
    n1 = math.floor(n/2+.01)
    n2 = math.ceil(n/2-.01)
    proba1 = proba[:n1]
    proba2 = proba[n2:]
    proba_mid = proba[n1:n2]
    sum1 = sum(proba1)
    sum2 = sum(proba2)
    proba1 = [x * 2 * sum2 / (sum1+sum2) for x in proba1]
    proba2 = [x * 2 * sum1 / (sum1+sum2) for x in proba2]
    proba = proba1 + proba_mid + proba2
    proba = [x + .01 for x in proba]
    proba[1] += proba[0]
    proba[-2] += proba[-1]
    n = random.choices(range(1,discretizer.n_bins_[0]-1), proba[1:-1])[0]
    start = discretizer.bin_edges_[0][n]
    end = discretizer.bin_edges_[0][n+1]
    start = max(start-(end-start)/2, -.9)
    end = min(end+(end-start)/2, 1.9)
    return random.uniform(start, end)
