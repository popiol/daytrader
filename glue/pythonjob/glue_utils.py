import pickle
import random
import math
import numpy as np
import datetime
import json

PRICE_CHANGE_N_BINS = 10
DB_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def logg(x):
    print("---- [{}] ".format(datetime.datetime.now()), x)

def create_event_key(comp_code, quote_dt):
    dt = quote_dt[:13].replace('-','').replace(' ','')
    dt2 = quote_dt.replace('-','').replace(' ','').replace(':','')
    return "events/date={}/{}_{}.json".format(dt, comp_code, dt2)

class Discretizer():
    def __init__(self, bucket=None, discretizer=None, low=None, high=None):
        if discretizer is None:
            obj_key = 'model/discretizer.pickle'
            f = bucket.Object(obj_key).get()
            discretizer = f['Body'].read()
            self.discretizer = pickle.loads(discretizer)
            obj_key = 'model/discretizer_high.pickle'
            f = bucket.Object(obj_key).get()
            discretizer = f['Body'].read()
            self.discretizer_high = pickle.loads(discretizer)
            obj_key = 'model/discretizer_low.pickle'
            f = bucket.Object(obj_key).get()
            discretizer = f['Body'].read()
            self.discretizer_low = pickle.loads(discretizer)
        else:
            self.discretizer = discretizer
            self.discretizer_high = high
            self.discretizer_low = low
        self.n_bins = self.discretizer.n_bins_[0]
        self.bins = self.discretizer.bin_edges_[0]
        self.n_bins_high = self.discretizer_high.n_bins_[0]
        self.bins_high = self.discretizer_high.bin_edges_[0]
        self.n_bins_low = self.discretizer_low.n_bins_[0]
        self.bins_low = self.discretizer_low.bin_edges_[0]

    def save(self, bucket):
        discretizer = pickle.dumps(self.discretizer)
        obj_key = "model/discretizer.pickle"
        bucket.put_object(Key=obj_key, Body=discretizer)
        discretizer = pickle.dumps(self.discretizer_high)
        obj_key = "model/discretizer_high.pickle"
        bucket.put_object(Key=obj_key, Body=discretizer)
        discretizer = pickle.dumps(self.discretizer_low)
        obj_key = "model/discretizer_low.pickle"
        bucket.put_object(Key=obj_key, Body=discretizer)

    def random_price_change(self, proba, type='price'):
        if type == 'price':
            n_bins = self.n_bins
            bins = self.bins
        elif type == 'high':
            n_bins = self.n_bins_high
            bins = self.bins_high
        elif type == 'low':
            n_bins = self.n_bins_low
            bins = self.bins_low
        proba = [x + .01 for x in proba]
        proba[1] += proba[0]
        proba[-2] += proba[-1]
        n = random.choices(range(1,n_bins-1), proba[1:-1])[0]
        start = bins[n]
        end = bins[n+1]
        start = max(start-(end-start)/2, -.9)
        end = min(end+(end-start)/2, 1.9)
        return random.uniform(start, end)

    def price_class(self, price_ch):
        return [1 if x <= price_ch <= self.bins[i+1] else 0 for i,x in enumerate(self.bins[:-1])]
    
    def high_class(self, price_ch):
        return [1 if x <= price_ch <= self.bins_high[i+1] else 0 for i,x in enumerate(self.bins_high[:-1])]

    def low_class(self, price_ch):
        return [1 if x <= price_ch <= self.bins_low[i+1] else 0 for i,x in enumerate(self.bins_low[:-1])]

class Event():
    def __init__(self, event=None, bucket=None, comp_code=None, quote_dt=None, obj_key=None):
        if event is None:
            if obj_key is None:
                obj_key = create_event_key(comp_code, quote_dt)
            f = bucket.Object(obj_key).get()
            event = f['Body'].read().decode('utf-8')
            event = json.loads(event)
        for key in event.keys():
            if key.startswith('price') or key.startswith('high') or key.startswith('low') or key.startswith('jump'):
                event[key] = float(event[key])
        if 'scale' not in event:
            event['scale'] = 1
        for exp in range(1,11):
            period = 2 ** exp
            key = f'price{period}'
            if key not in event:
                event[key] = event['price']
            key = f'high{period}'
            if key not in event:
                event[key] = event['high_price']
            key = f'low{period}'
            if key not in event:
                event[key] = event['low_price']
            key = f'jumpup{period}'
            if key not in event:
                event[key] = event['price'] - event['low_price']
            key = f'jumpdown{period}'
            if key not in event:
                event[key] = event['price'] - event['high_price']
        hour = int(event['quote_dt'][11:13])
        if 'start' not in event:
            event['start'] = 1 if hour <= 9 else 0
        if 'end' not in event:
            event['end'] = 1 if hour >= 16 else 0
        for th in [10,20,40,80]:
            key = f'ch>{th}'
            if key not in event:
                event[key] = 0
            
        self.event = event

    def get_price(self):
        return float(self.event['price']) * float(self.event['scale'])

    def get_high_price(self):
        return float(self.event['high_price']) * float(self.event['scale'])

    def get_low_price(self):
        return float(self.event['low_price']) * float(self.event['scale'])

    def get_inputs(self):
        attrs = ['low_price','high_price','start','end','ch>10','ch>20','ch>40','ch>80']
        period_attrs = ['price','high','low','jumpup','jumpdown']
        for exp in range(1,11):
            period = 2 ** exp
            for attr in period_attrs:
                attrs.append(f'{attr}{period}')
        price = float(self.event['price'])
        inputs = [float(self.event[x]) / price for x in attrs]
        return inputs

    def next(self, price, high_price, low_price, quote_dt):
        event = self.event.copy()
        prev_event = self.event
        scale = prev_event['scale']
        for exp in range(1,11):
            period = 2 ** exp
            key = f'price{period}'
            event[key] = price / period + prev_event[key] * (1-1/period)
            key = f'high{period}'
            event[key] = max(high_price, high_price / period + prev_event[key] * (1-1/period))
            key = f'low{period}'
            event[key] = min(low_price, low_price / period + prev_event[key] * (1-1/period))
            key = f'jumpup{period}'
            key_low = f'low{period}'
            jumpup = price - prev_event[key_low]
            event[key] = max(jumpup, prev_event[key] * (1-1/period))
            key = f'jumpdown{period}'
            key_high = f'high{period}'
            jumpdown = price - prev_event[key_high]
            event[key] = min(jumpdown, prev_event[key] * (1-1/period))
        hour = int(quote_dt[11:13])
        event['start'] = 1 if hour <= 9 else 0
        event['end'] = 1 if hour >= 16 else 0
        ch = price/prev_event['price']-1
        for th in [10,20,40,80]:
            event[f'ch>{th}'] = 1 if ch > th/100 or ch < 1/(th/100+1)-1 else 0
        if event['ch>80']:
            scale *= prev_event['price'] / price
        event['scale'] = scale
        return Event(event)

    def save(self, bucket, obj_key):
        event = json.dumps(self.event)
        bucket.put_object(Key=obj_key, Body=bytearray(event, 'utf-8'))

class PriceChModel():
    def __init__(self, bucket=None, model=None):
        if model is None:
            obj_key = 'model/pricech_model.pickle'
            f = bucket.Object(obj_key).get()
            model = f['Body'].read()
            self.model = pickle.loads(model)
        else:
            self.model = model

    def save(self, bucket):
        model = pickle.dumps(self.model)
        obj_key = "model/pricech_model.pickle"
        bucket.put_object(Key=obj_key, Body=model)

    def predict(self, test_x):
        return self.model.predict(test_x)

    def predict_proba(self, test_x):
        return self.model.predict_proba(test_x)
