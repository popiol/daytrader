import boto3
import os
import tensorflow.keras as keras
import pickle
import math
import numpy as np
import shutil
import sys

bucket_name = os.environ['bucket_name']
event_table_name = os.environ['event_table_name']
temporary = int(os.environ['temporary'])
s3 = boto3.resource("s3")
bucket = s3.Bucket(bucket_name)
db = boto3.resource('dynamodb')
event_table = db.Table(event_table_name)

def s3_download(bucket, obj_key):
    filename = obj_key.split('/')[-1]
    f_in = bucket.Object(obj_key).get()
    with open(filename,'wb') as f_out:
        f_out.write(f_in['Body'].read())

s3_download(bucket, 'scripts/glue_utils.py')

import glue_utils

class Agent():
    def __init__(self, agent_name, bucket):
        try:
            dirname = 'model.dump'
            filename = 'model.zip'
            obj_key = f'model/{agent_name}_model.zip'
            bucket.download_file(obj_key, filename)
            shutil.unpack_archive(filename, dirname)
            self.model = keras.models.load_model(dirname)
            self.loaded = True
        except:
            pricech_model = glue_utils.PriceChModel(bucket)
            in_shape = pricech_model.get_input_shape()[0]
            in_shape = tuple([in_shape+1])
            inputs = keras.layers.Input(shape=in_shape)
            hidden1 = keras.layers.Dense(100, activation="relu")(inputs)
            buy_action = keras.layers.Dense(1, activation="sigmoid")(hidden1)
            buy_price = keras.layers.Dense(1, activation="sigmoid")(hidden1)
            sell_price = keras.layers.Dense(1, activation="sigmoid")(hidden1)
            self.model = keras.Model(inputs=inputs, outputs=[buy_action, buy_price, sell_price])
            self.model.compile(optimizer='nadam', loss='huber_loss')
            self.loaded = False
        self.bucket = bucket
        self.agent_name = agent_name
        self.provision = .001
        self.reset()
        
    def save(self):
        dirname = 'model.dump'
        filename = 'model'
        self.model.save(dirname)
        shutil.make_archive(filename, 'zip', dirname)
        filename += '.zip'
        obj_key = f'model/{self.agent_name}_model.zip'
        self.bucket.upload_file(filename, obj_key)

    def save_as(self, agent_name):
        self.agent_name = agent_name
        self.save()
        return self

    def get_n_ticks(self, comp_code):
        return self.portfolio[comp_code]['n_ticks'] if comp_code in self.portfolio else 0

    def get_inputs(self, event):
        inputs = event.get_inputs()
        comp_code = event.event['comp_code']
        n_ticks = self.get_n_ticks(comp_code)
        inputs.append(n_ticks)
        return inputs

    def handle_orders(self, event):
        comp_code = event.event['comp_code']
        quote_dt = event.event['quote_dt']
        hour = int(quote_dt[11:13])
        if 9 <= hour <= 15 and comp_code in self.orders:
            if self.orders[comp_code]['buy'] and self.orders[comp_code]['price'] > float(event.event['price']):
                self.portfolio[comp_code] = self.orders[comp_code]
                self.portfolio[comp_code]['n_ticks'] = 1
                self.cash -= self.portfolio[comp_code]['n_shares'] * self.orders[comp_code]['price'] * (1 + self.provision)
                #print(event.event['quote_dt'])
                #print("Buy", self.portfolio[comp_code]['n_shares'], "shares of", comp_code, "for", self.orders[comp_code]['price'])
                #print("Cash:", self.cash, ", Capital:", self.get_capital())
            elif not self.orders[comp_code]['buy'] and self.orders[comp_code]['price'] < float(event.event['price']):
                del self.portfolio[comp_code]
                self.cash += self.orders[comp_code]['n_shares'] * self.orders[comp_code]['price'] * (1 - self.provision)
                #print(event.event['quote_dt'])
                #print("Sell", self.orders[comp_code]['n_shares'], "shares of", comp_code, "for", self.orders[comp_code]['price'])
                #print("Cash:", self.cash, ", Capital:", self.get_capital())
        
    def add_sell_order(self, event, sell_price_ch):
        comp_code = event.event['comp_code']
        price = event.event['price']
        orders = {}
        if comp_code in self.portfolio and abs(sell_price_ch) < .1:
            self.portfolio[comp_code]['price'] = price
            sell_price = price * (1+sell_price_ch)
            orders[comp_code] = {'buy':False, 'price':sell_price, 'n_shares':self.portfolio[comp_code]['n_shares']}
        return orders

    def get_capital(self):
        capital = sum(self.portfolio[x]['n_shares'] * self.portfolio[x]['price'] for x in self.portfolio)
        capital += self.cash
        return capital

    def next(self, events, get_outputs):
        inputs = []
        outputs2 = []
        best_event = None
        orders = {}
        for event in events:
            inputs.append(self.get_inputs(event))
        outputs = get_outputs(events, inputs)
        for event in events:
            comp_code = event.event['comp_code']
            self.handle_orders(event)
            buy_action, buy_price, sell_price = outputs[comp_code]
            if (best_event is None or buy_action > best_buy) and comp_code not in self.portfolio and abs(buy_price) < .1:
                best_event = event
                best_buy = buy_action
                best_price = event.event['price'] * (1+buy_price)
            outputs1 = [buy_action, buy_price, sell_price]
            outputs1 = [(x+1)/2 for x in outputs1]
            outputs2.append(outputs1)
            orders.update(self.add_sell_order(event, sell_price))
        self.orders = orders
        if self.cash > 200 and best_event is not None:
            capital = self.get_capital()
            n = math.floor(capital / best_price * best_buy * (1 - self.provision))
            n = min(n, math.floor(self.cash / best_price * (1 - self.provision)))
            if n > 0:
                comp_code = best_event.event['comp_code']
                self.orders[comp_code] = {'buy':True, 'price':best_price, 'n_shares':n}
        for comp_code in self.portfolio:
            self.portfolio[comp_code]['n_ticks'] += 1
        return inputs, outputs2

    def get_train_init_outputs(self, events, inputs):
        outputs = {}
        for event in events:
            comp_code = event.event['comp_code']
            price = event.get_price()
            price8 = event.event['price8']
            price4 = event.event['price4']
            price32 = event.event['price32']
            triangle = (price4 - price - abs(price8 - price4)) / price
            triangle = triangle / (abs(triangle) + 1)
            buy = 1 if triangle > 0 and price32 / price > -.01 else 0
            buy_action = math.pow(triangle*8, .44) if buy else triangle / 2 - .5
            buy_price = 0
            n_ticks = self.get_n_ticks(comp_code)
            sell_price = max((8 - n_ticks) * .04, 0)
            outputs[comp_code] = (buy_action, buy_price, sell_price)
        return outputs

    def fit(self, x, y):
        with open('/dev/null', 'w') as f:
            sys.stdout = f
            self.model.fit(x, y)
            sys.stdout = sys.__stdout__

    def train_init(self, events):
        inputs, outputs = self.next(events, self.get_train_init_outputs)
        outputs = list(zip(*outputs))
        outputs = [np.array(x) for x in outputs]
        self.fit(np.array(inputs), outputs)

    def train(self, events):
        pass

    def reset(self):
        self.score = 0
        self.min_weekly = None
        self.weekly_ticks = 0
        self.week_start_val = None
        self.portfolio = {}
        self.orders = {}
        self.cash = 1000

    def get_test_outputs(self, events, inputs):
        outputs = self.model.predict(inputs)
        outputs = list(zip(*outputs))
        outputs = [[y[0]*2-1 for y in x] for x in outputs]
        outputs = {event.event['comp_code']: out for event, out in zip(events, outputs)}
        return outputs

    def test(self, events):
        week_n_ticks = 40
        prev_capital = self.get_capital()
        self.next(events, self.get_test_outputs)
        capital = self.get_capital()
        score = capital / prev_capital - 1
        if self.weekly_ticks == 0:
            if self.week_start_val is not None:
                weekly_val = capital / self.week_start_val - 1
                if self.min_weekly is None or weekly_val < self.min_weekly:
                    self.min_weekly = weekly_val
                score += self.min_weekly / week_n_ticks
            self.week_start_val = capital
        self.weekly_ticks = (self.weekly_ticks+1) % week_n_ticks
        self.score += score
        
def compare_agents(agent1, agent2, hist=False):
    scores1 = []
    scores2 = []
    offset_range = [0] if hist else [-1,0,1] 
    for offset in offset_range:
        if hist:
            simulator = glue_utils.HistSimulator(bucket)
        else:
            simulator = glue_utils.Simulator(bucket, offset)
        agent1.reset()
        agent2.reset()
        max_it = 100000 if hist else 1000
        for _ in range(max_it):
            events = simulator.next()
            if events is None:
                break
            agent1.test(events)
            agent2.test(events)
        scores1.append(agent1.score)
        scores2.append(agent2.score)
    score1 = np.average(scores1) + min(scores1)
    score2 = np.average(scores2) + min(scores2)
    return score1, score2
