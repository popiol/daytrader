import pickle
import random
import math
import numpy as np
import datetime
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import time
import sys

PRICE_CHANGE_N_BINS = 10
HIGH_CHANGE_N_BINS = 5
LOW_CHANGE_N_BINS = HIGH_CHANGE_N_BINS
ALL_CHANGE_N_BINS = PRICE_CHANGE_N_BINS + HIGH_CHANGE_N_BINS + LOW_CHANGE_N_BINS
DB_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
SIM_N_COMPS = 450
N_VANISHING_COMPS = 100
MIN_EVENTS_LEN = 100

def logg(x):
    print("---- [{}] ".format(datetime.datetime.now()), x)

def create_event_key(comp_code, quote_dt):
    dt = quote_dt[:13].replace('-','').replace(' ','')
    dt2 = quote_dt.replace('-','').replace(' ','').replace(':','')
    return "events/date={}/{}_{}.json".format(dt, comp_code, dt2)

def run_batch_job(job_name, queue_name, asynch=False, env={}):
    batch = boto3.client('batch')
    env = [{'name':x, 'value':env[x]} for x in env]
    res = batch.submit_job(
        jobName=job_name, 
        jobQueue=queue_name, 
        jobDefinition=job_name, 
        containerOverrides={'environment':env}
    )
    job_id = res['jobId']
    for _ in range(12):
        res = batch.describe_jobs(jobs=[job_id])
        job_status = res['jobs'][0]['status']
        if job_status in ['SUCCEEDED','FAILED'] or asynch: break
        time.sleep(60)
    return {'job_status': job_status}

def scan(table, filter, limit=None):
    items = []
    res = table.scan(FilterExpression=filter)
    while 'LastEvaluatedKey' in res and (limit is None or len(items) < limit):
        res = table.scan(
            FilterExpression=filter, 
            ExclusiveStartKey=res['LastEvaluatedKey'])
        items.extend(res['Items'])
    return items

def get_start_dt(event_table, start_dt=None):
    if start_dt is None:
        start_dt1 = datetime.datetime.now()
        start_dt1 -= datetime.timedelta(days=365)
        start_dt1 = start_dt1.strftime(DB_DATE_FORMAT)
        start_dt2 = datetime.datetime.strptime('2020-04-01', '%Y-%m-%d')
        start_dt2 = start_dt2.strftime(DB_DATE_FORMAT)
        start_dt = max(start_dt1, start_dt2)
    quote_dt = None
    res = event_table.scan(FilterExpression=Attr('quote_dt').gt(start_dt), ProjectionExpression="comp_code,quote_dt")
    for item in res['Items']:
        if quote_dt is None or item['quote_dt'] < quote_dt:
            quote_dt = item['quote_dt']
    while 'LastEvaluatedKey' in res:
        res = event_table.scan(FilterExpression=Attr('quote_dt').gt(start_dt) & Attr('quote_dt').lt(quote_dt), ExclusiveStartKey=res['LastEvaluatedKey'], ProjectionExpression="comp_code,quote_dt")
        for item in res['Items']:
            if item['quote_dt'] < quote_dt:
                quote_dt = item['quote_dt']
    return quote_dt

def list_companies(event_table):
    comp_codes = {}
    quote_dts = {}
    start_dt = get_start_dt(event_table)
    if start_dt is None:
        return comp_codes
    res = event_table.scan(FilterExpression=Attr('quote_dt').gte(start_dt), ProjectionExpression="comp_code,quote_dt")
    for item in res['Items']:
        comp_code = item['comp_code']
        quote_dt = item['quote_dt']
        comp_codes[comp_code] = 1
        quote_dts[quote_dt] = 1
    while 'LastEvaluatedKey' in res:
        res = event_table.scan(FilterExpression=Attr('quote_dt').gte(start_dt), ExclusiveStartKey=res['LastEvaluatedKey'], ProjectionExpression="comp_code,quote_dt")
        for item in res['Items']:
            comp_code = item['comp_code']
            quote_dt = item['quote_dt']
            comp_codes[comp_code] = 1
            quote_dts[quote_dt] = 1
    quote_dts = list(quote_dts)
    quote_dts.sort()
    return list(comp_codes), quote_dts

def list_events(event_table):
    comp_codes = []
    quote_dts = []
    start_dt = get_start_dt(event_table)
    if start_dt is None:
        return comp_codes
    res = event_table.scan(FilterExpression=Attr('quote_dt').gte(start_dt), ProjectionExpression="comp_code,quote_dt")
    for item in res['Items']:
        comp_code = item['comp_code']
        quote_dt = item['quote_dt']
        comp_codes.append(comp_code)
        quote_dts.append(quote_dt)
    while 'LastEvaluatedKey' in res:
        res = event_table.scan(FilterExpression=Attr('quote_dt').gte(start_dt), ExclusiveStartKey=res['LastEvaluatedKey'], ProjectionExpression="comp_code,quote_dt")
        for item in res['Items']:
            comp_code = item['comp_code']
            quote_dt = item['quote_dt']
            comp_codes.append(comp_code)
            quote_dts.append(quote_dt)
    keys = np.argsort(quote_dts)
    quote_dts = [quote_dts[i] for i in keys]
    comp_codes = [comp_codes[i] for i in keys]
    return comp_codes, quote_dts

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

    def random_price_change(self, proba_all, offset=0):
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
            val = random.uniform(start, end)
            val = (val + .0001 * (offset-1)) * 1.9
            outputs.append(val)
        return outputs

    def price_class(self, price_ch):
        return [1 if x <= price_ch <= self.bins[0][i+1] else 0 for i,x in enumerate(self.bins[0][:-1])]
    
    def high_class(self, price_ch):
        return [1 if x <= price_ch <= self.bins[1][i+1] else 0 for i,x in enumerate(self.bins[1][:-1])]

    def low_class(self, price_ch):
        return [1 if x <= price_ch <= self.bins[2][i+1] else 0 for i,x in enumerate(self.bins[2][:-1])]

class Event():
    def __init__(self, event=None, bucket=None, event_table=None, comp_code=None, quote_dt=None):
        self.source_file = ""
        persist = False
        if event is None:
            res = event_table.query(
                KeyConditionExpression = Key('comp_code').eq(comp_code) & Key('quote_dt').eq(quote_dt)
            )
            if res['Items']:
                self.source_file = res['Items'][0]['source_file']
            if not res['Items'] or 'vals' not in res['Items'][0] or len(res['Items'][0]['vals']) < 10:
                obj_key = create_event_key(comp_code, quote_dt)
                f = bucket.Object(obj_key).get()
                event = f['Body'].read().decode('utf-8')
                event = json.loads(event)
                persist = True
            else:
                event = res['Items'][0]['vals']
                event['comp_code'] = comp_code
                event['quote_dt'] = quote_dt
        for key in event.keys():
            if key.startswith('price') or key.startswith('high') or key.startswith('low') or key.startswith('jump') or key == 'scale':
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
        self.event_table = event_table
        if persist and self.event_table is not None:
            self.persist(self.event_table)

    def persist_types(self, x):
        if isinstance(x, float):
            return Decimal(str(x))
        return x

    def persist(self, event_table):
        vals = {x: self.persist_types(self.event[x]) for x in self.event if x not in ['comp_code','quote_dt']}
        event_table.put_item(
            Item = {
                'comp_code': self.event['comp_code'],
                'quote_dt': self.event['quote_dt'],
                'source_file': self.source_file,
                'vals': vals
            }
        )

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
    def __init__(self, bucket, offset=0):
        comp_codes = []
        n_comps = SIM_N_COMPS
        self.last_comp_code_i = -1
        for _ in range(n_comps):
            comp_code = self.generate_comp_code()
            comp_codes.append(comp_code)
        self.comp_codes = comp_codes
        quote_dt = '2020-01-01 09:30:00'
        self.quote_dt = quote_dt
        events = {}
        for comp_code in comp_codes:
            price = self.generate_price()
            vanishing = 1 if len(events) >= SIM_N_COMPS - N_VANISHING_COMPS else 0
            event = {'comp_code':comp_code,'quote_dt':quote_dt,'price':price,'high_price':price,'low_price':price,'vanishing':vanishing}
            events[comp_code] = Event(event)
        self.events = events
        self.model = PriceChModel(bucket)
        self.discretizer = Discretizer(bucket)
        self.samples = {}
        for comp_code in comp_codes[:10]:
            self.samples[comp_code] = [self.events[comp_code].get_price()]
        self.offset = offset
        for _ in range(500):
            self.next()

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

    def generate_price(self):
        price = 0
        while price <= .1 or price > 2500:
            price = math.pow(max(0,random.gauss(.5,.2)),6)*1000
        return round(price, 2)

    def next(self):
        hour = int(self.quote_dt[8:10])
        n_steps = random.choices([1,2], [3.3 + abs(hour-13), 3])[0]
        for _ in range(n_steps):
            quote_dt = datetime.datetime.strptime(self.quote_dt, DB_DATE_FORMAT)
            quote_dt += datetime.timedelta(hours=1)
            if quote_dt.hour > 16:
                quote_dt += datetime.timedelta(hours=17)
            if quote_dt.weekday() > 4:
                quote_dt += datetime.timedelta(days=2)
            renamed = {}
            if quote_dt.hour == 10:
                for i, comp_code in enumerate(self.comp_codes):
                    rename = random.choices([0,1], [250*len(self.comp_codes),5])[0]
                    if rename:
                        old_comp_code = comp_code
                        comp_code = self.generate_comp_code()
                        self.comp_codes[i] = comp_code
                        price = self.generate_price()
                        vanishing = self.events[old_comp_code].event['vanishing']
                        self.events[comp_code] = Event({'comp_code':comp_code,'quote_dt':self.quote_dt,'price':price,'high_price':price,'low_price':price,'vanishing':vanishing})
                        renamed[comp_code] = old_comp_code
                        #print(f"Rename {old_comp_code} to {comp_code}")
            hour = quote_dt.hour
            quote_dt = quote_dt.strftime(DB_DATE_FORMAT)
            events = {}
            base_ch = None
            for comp_code in self.comp_codes:
                inputs = self.events[comp_code].get_inputs()
                proba = self.model.predict_proba(inputs)
                price_ch, high_price_ch, low_price_ch = self.discretizer.random_price_change(proba, self.offset)
                if base_ch is None:
                    base_ch = price_ch / 5
                else:
                    price_ch += base_ch
                price = self.events[comp_code].event['price'] * (price_ch + 1)
                high_price = self.events[comp_code].event['price'] * (high_price_ch + 1)
                low_price = self.events[comp_code].event['price'] * (low_price_ch + 1)
                high_price = max(high_price, price)
                low_price = min(low_price, price)
                price = round(price, 2)
                high_price = round(high_price, 2)
                low_price = round(low_price, 2)
                events[comp_code] = self.events[comp_code].next(price, high_price, low_price, quote_dt)
                if comp_code in renamed:
                    events[comp_code].event['old_comp_code'] = renamed[comp_code]
            self.events = events
            self.quote_dt = quote_dt
        batch = []
        for event in self.events.values():
            vanishing = event.event['vanishing']
            add = random.randrange(2) if vanishing else 1
            if add:
                batch.append(event)
        if hour == 16:
            for comp_code in self.samples:
                if comp_code in self.events:
                    self.samples[comp_code].append(self.events[comp_code].get_price())
        return batch

    def print_sample_quotes(self):
        for comp_code in self.samples:
            print(comp_code)
            print(self.samples[comp_code])

class HistSimulator():
    def __init__(self, db, event_table_name):
        self.db = db
        self.event_table_name = event_table_name
        self.event_table = db.Table(event_table_name)
        self.quote_dt_i = 0
        self.samples = {}
        self.comp_codes, self.quote_dts = list_events(self.event_table)

    def next(self):
        events = {}
        while len(events) < 300 and self.quote_dt_i < len(self.quote_dts):
            keys = []
            for _ in range(500):
                if self.quote_dt_i >= len(self.quote_dts):
                    break
                self.quote_dt = self.quote_dts[self.quote_dt_i]
                comp_code = self.comp_codes[self.quote_dt_i]
                self.quote_dt_i += 1
                keys.append({'comp_code':comp_code, 'quote_dt':self.quote_dt})
            for batch_i in range(math.ceil(len(keys)/10)):
                res = self.db.batch_get_item(
                    RequestItems={
                        self.event_table_name: {
                            'Keys': keys[batch_i*10:(batch_i+1)*10]
                        }
                    }
                )
                for item in res['Responses'][self.event_table_name]:
                    comp_code = item['comp_code']
                    quote_dt = item['quote_dt']
                    event = item['vals']
                    event['comp_code'] = comp_code
                    event['quote_dt'] = quote_dt
                    events[comp_code] = Event(event)
        if not events:
            return None
        #print(self.quote_dt, len(events))
        batch = list(events.values())
        hour = int(self.quote_dt[8:10])
        if hour == 16:
            if self.samples:
                for comp_code in self.samples:
                    if comp_code in events:
                        self.samples[comp_code].append(events[comp_code].get_price())
            else:
                for comp_code in list(events)[:10]:
                    self.samples[comp_code] = [events[comp_code].get_price()]
        return batch

    def print_sample_quotes(self):
        for comp_code in self.samples:
            print(comp_code)
            print(self.samples[comp_code])

class Settings():
    def __init__(self, bucket):
        self.path = 'model/settings.json'
        try:
            f = bucket.Object(self.path).get()
            settings = f['Body'].read().decode('utf-8')
            settings = json.loads(settings)
        except:
            settings = {}
        self.map = settings
        self.bucket = bucket

    def save(self):
        settings = json.dumps(self.map)
        self.bucket.put_object(Key=self.path, Body=settings)
