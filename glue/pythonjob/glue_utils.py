import pickle
import random
import math
import numpy as np
import datetime
import json

PRICE_CHANGE_N_BINS = 10
HIGH_CHANGE_N_BINS = 5
LOW_CHANGE_N_BINS = HIGH_CHANGE_N_BINS
ALL_CHANGE_N_BINS = PRICE_CHANGE_N_BINS + HIGH_CHANGE_N_BINS + LOW_CHANGE_N_BINS
DB_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
SIM_N_COMPS = 500

def logg(x):
    print("---- [{}] ".format(datetime.datetime.now()), x)

def create_event_key(comp_code, quote_dt):
    dt = quote_dt[:13].replace('-','').replace(' ','')
    dt2 = quote_dt.replace('-','').replace(' ','').replace(':','')
    return "events/date={}/{}_{}.json".format(dt, comp_code, dt2)

class Discretizer():
    def __init__(self, bucket=None, discretizer=None):
        if discretizer is None:
            obj_key = 'model/discretizer.pickle'
            f = bucket.Object(obj_key).get()
            discretizer = f['Body'].read()
            self.discretizer = pickle.loads(discretizer)
        else:
            self.discretizer = discretizer
        self.n_bins = self.discretizer.n_bins_
        self.bins = self.discretizer.bin_edges_

    def save(self, bucket):
        discretizer = pickle.dumps(self.discretizer)
        obj_key = "model/discretizer.pickle"
        bucket.put_object(Key=obj_key, Body=discretizer)

    def random_price_change(self, proba_all):
        outputs = []
        for type in ['price','high','low']:
            if type == 'price':
                n_bins = self.n_bins[0]
                bins = self.bins[0]
                proba = proba_all[:n_bins]
            elif type == 'high':
                n_bins = self.n_bins[1]
                bins = self.bins[1]
                proba = proba_all[self.n_bins[0]:self.n_bins[0]+self.n_bins[1]]
            elif type == 'low':
                n_bins = self.n_bins[2]
                bins = self.bins[2]
                proba = proba_all[self.n_bins[0]+self.n_bins[1]:]
            proba = [x + .01 for x in proba]
            proba[1] += proba[0]
            proba[-2] += proba[-1]
            n = random.choices(range(1,n_bins-1), proba[1:-1])[0]
            start = bins[n]
            end = bins[n+1]
            start = max(start-(end-start)/2, -.9)
            end = min(end+(end-start)/2, 1.9)
            outputs.append(random.uniform(start, end))
        return tuple(outputs)

    def price_class(self, price_ch):
        return [1 if x <= price_ch <= self.bins[0][i+1] else 0 for i,x in enumerate(self.bins[0][:-1])]
    
    def high_class(self, price_ch):
        return [1 if x <= price_ch <= self.bins[1][i+1] else 0 for i,x in enumerate(self.bins[1][:-1])]

    def low_class(self, price_ch):
        return [1 if x <= price_ch <= self.bins[2][i+1] else 0 for i,x in enumerate(self.bins[2][:-1])]

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
        hour = int(event['quote_dt'][11:13])
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
        hour = float(self.event['quote_dt'][11:13])
        inputs.append(hour)
        return inputs

    def next(self, price, high_price, low_price, quote_dt):
        event = self.event.copy()
        prev_event = self.event
        event['price'] = price
        event['high_price'] = high_price
        event['low_price'] = low_price
        event['quote_dt'] = quote_dt
        scale = prev_event['scale']
        ch = price/prev_event['price']-1
        for th in [10,20,40,80]:
            event[f'ch>{th}'] = 1 if ch > th/100 or ch < 1/(th/100+1)-1 else 0
        if event['ch>80']:
            scale *= prev_event['price'] / price
        event['scale'] = scale
        price *= scale
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

    def predict_proba(self, test_x):
        return self.model.predict_proba([test_x])[0]

    def get_input_shape(self):
        return tuple([np.shape(self.model.coefs_[0])[0]])

class Simulator():
    def __init__(self, bucket):
        comp_codes = []
        n_comps = SIM_N_COMPS
        self.last_comp_code_i = -1
        for _ in range(n_comps):
            comp_code = self.generate_comp_code()
            comp_codes.append(comp_code)
        self.comp_codes = comp_codes
        quote_dt = '2020-01-01 08:30:00'
        self.quote_dt = quote_dt
        events = {}
        for comp_code in comp_codes:
            price = 0
            while price <= 0 or price > 2500:
                price = np.random.poisson(215)
            event = {'comp_code':comp_code,'quote_dt':quote_dt,'price':price,'high_price':price,'low_price':price}
            events[comp_code] = Event(event)
        self.events = events
        self.model = PriceChModel(bucket)
        self.discretizer = Discretizer(bucket)

    def generate_comp_code(self):
        self.last_comp_code_i += 1
        comp_code_i = self.last_comp_code_i
        nchar = 26
        start = 65
        c1 = chr(int(comp_code_i / (nchar*nchar)) + start)
        comp_code_i = comp_code_i % (nchar*nchar)
        c2 = chr(int(comp_code_i / nchar) + start)
        c3 = chr(comp_code_i % nchar + start)
        return c1+c2+c3

    def next(self):
        events = {}
        quote_dt = datetime.datetime.strptime(self.quote_dt, DB_DATE_FORMAT)
        quote_dt += datetime.timedelta(hours=1)
        if quote_dt.hour > 17:
            quote_dt += datetime.timedelta(hours=14)
        if quote_dt.weekday() > 4:
            quote_dt += datetime.timedelta(days=2)
        if quote_dt.hour == 8:
            for i, comp_code in enumerate(self.comp_codes):
                rename = random.choices([0,1], [250*len(self.comp_codes),5])
                if rename:
                    comp_code = self.generate_comp_code()
                    self.comp_codes[i] = comp_code
                    self.events[comp_code] = Event({'comp_code':comp_code,'quote_dt':self.quote_dt})
        hour = quote_dt.hour
        quote_dt = quote_dt.strftime(DB_DATE_FORMAT)
        if 9 <= hour <= 17:
            for comp_code in self.comp_codes:
                inputs = self.events[comp_code].get_inputs()
                proba = self.model.predict_proba(inputs)
                price_ch, high_price_ch, low_price_ch = self.discretizer.random_price_change(proba)
                price = self.events[comp_code].event['price'] * (price_ch + 1)
                high_price = self.events[comp_code].event['high_price'] * (high_price_ch + 1)
                low_price = self.events[comp_code].event['low_price'] * (low_price_ch + 1)
                high_price = max(high_price, price)
                low_price = min(low_price, price)
                events[comp_code] = self.events[comp_code].next(price, high_price, low_price, quote_dt)
        batch = list(self.events.values())
        self.events = events
        self.quote_dt = quote_dt
        return batch

class HistSimulator():
    def __init__(self, bucket):
        self.bucket = bucket
        objs = bucket.objects.all()
        min_dt = None
        for obj in objs:
            if obj.key.startswith('events/date='):
                dt = obj.key.split('/')[1].split('=')[1]
                if min_dt is None or dt < min_dt:
                    min_dt = dt
        self.quote_dt = min_dt
        files = []
        for obj in objs:
            if obj.key.startswith('events/date='):
                dt = obj.key.split('/')[1].split('=')[1]
                if dt == self.quote_dt:
                    min_dt = dt
                    files.append(obj.key)
        events = {}
        for obj_key in files:
            comp_code = obj_key.split('/')[-1].split('_')[0]
            events[comp_code] = Event(bucket=self.bucket, obj_key=obj_key)
        self.events = events

    def next(self):
        objs = self.bucket.objects.all()
        min_dt = None
        for obj in objs:
            if obj.key.startswith('events/date='):
                dt = obj.key.split('/')[1].split('=')[1]
                if dt > self.quote_dt and (min_dt is None or dt < min_dt):
                    min_dt = dt
        self.quote_dt = min_dt
        if self.quote_dt is None:
            return None
        files = []
        for obj in objs:
            if obj.key.startswith('events/date='):
                dt = obj.key.split('/')[1].split('=')[1]
                if dt == self.quote_dt:
                    min_dt = dt
                    files.append(obj.key)
        events = {}
        for obj_key in files:
            comp_code = obj_key.split('/')[-1].split('_')[0]
            events[comp_code] = Event(bucket=self.bucket, obj_key=obj_key)
        batch = []
        for comp_code in events:
            if comp_code in self.events:
                price = events[comp_code].get_price()
                high_price = events[comp_code].get_high_price()
                low_price = events[comp_code].get_low_price()
                quote_dt = events[comp_code].event['quote_dt']
                event = self.events[comp_code].next(price, high_price, low_price, quote_dt)
                self.events[comp_code] = event
            else:
                self.events[comp_code] = events[comp_code]
            batch.append(self.events[comp_code])
        return batch
