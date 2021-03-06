import sys
import boto3
import os
import tensorflow as tf
from tensorflow import keras
import pickle
import math
import numpy as np
import shutil
import random

bucket_name = os.environ['bucket_name']
event_table_name = os.environ['event_table_name']
aws_region = os.environ['aws_region']
temporary = int(os.environ['temporary'])
s3 = boto3.resource("s3")
bucket = s3.Bucket(bucket_name)
db = boto3.resource('dynamodb', region_name=aws_region)
event_table = db.Table(event_table_name)

def s3_download(bucket, obj_key):
    filename = obj_key.split('/')[-1]
    f_in = bucket.Object(obj_key).get()
    with open(filename,'wb') as f_out:
        f_out.write(f_in['Body'].read())

s3_download(bucket, 'scripts/glue_utils.py')

import glue_utils

class Agent():
    def __init__(self, agent_name, bucket, verbose=False, recreate=False):
        try:
            if recreate:
                raise Exception()
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
        self.optimizer = keras.optimizers.Nadam()
        self.bucket = bucket
        self.agent_name = agent_name
        self.provision = .001
        self.reset()
        self.verbose = verbose
        self.max_w = 1
        self.max_c = .1
        self.max_s = 2
        
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

    def handle_orders(self, event, orders):
        comp_code = event.event['comp_code']
        quote_dt = event.event['quote_dt']
        hour = int(quote_dt[11:13])
        transaction_made = False
        if 9 <= hour <= 15 and comp_code in self.orders:
            if self.orders[comp_code]['buy'] and self.orders[comp_code]['price'] > float(event.event['price']):
                self.portfolio[comp_code] = self.orders[comp_code]
                self.portfolio[comp_code]['n_ticks'] = 1
                self.cash -= self.portfolio[comp_code]['n_shares'] * self.orders[comp_code]['price'] * (1 + self.provision)
                transaction_made = True
                self.n_bought += 1
                if self.verbose:
                    print(event.event['quote_dt'])
                    print("Buy", self.portfolio[comp_code]['n_shares'], "shares of", comp_code, "for", self.orders[comp_code]['price'])
                    print("Cash:", self.cash, ", Capital:", self.get_capital())
            elif not self.orders[comp_code]['buy'] and self.orders[comp_code]['price'] < float(event.event['price']):
                del self.portfolio[comp_code]
                self.cash += self.orders[comp_code]['n_shares'] * self.orders[comp_code]['price'] * (1 - self.provision)
                transaction_made = True
                self.n_sold += 1
                if self.verbose:
                    print(event.event['quote_dt'])
                    print("Sell", self.orders[comp_code]['n_shares'], "shares of", comp_code, "for", self.orders[comp_code]['price'])
                    print("Cash:", self.cash, ", Capital:", self.get_capital())
        if transaction_made and comp_code in orders:
            del orders[comp_code]
        
    def add_sell_order(self, event, sell_price_ch, orders):
        comp_code = event.event['comp_code']
        price = event.event['price']
        if comp_code in self.portfolio and comp_code not in orders and abs(sell_price_ch) < .1 and self.portfolio[comp_code]['n_ticks'] > 1:
            self.portfolio[comp_code]['price'] = price
            sell_price = round(price * (1+sell_price_ch), 2)
            if self.verbose:
                print("Sell price:", comp_code, price, sell_price)
            orders[comp_code] = {'buy':False, 'price':sell_price, 'n_shares':self.portfolio[comp_code]['n_shares']}

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
        prev_events = {}
        for event in events:
            comp_code = event.event['comp_code']
            prev_events[comp_code] = event
            if self.prev_events is not None and comp_code in self.prev_events:
                price_ch = event.get_price() / self.prev_events[comp_code].get_price() - 1
                if price_ch > 0:
                    self.price_up.append(price_ch)
                elif price_ch < 0:
                    self.price_down.append(price_ch)
            if 'old_comp_code' in event.event and event.event['old_comp_code'] in self.portfolio:
                old_comp_code = event.event['old_comp_code']
                self.portfolio[comp_code] = self.portfolio[old_comp_code]
                del self.portfolio[old_comp_code]
            self.handle_orders(event, orders)
            buy_action, buy_price, sell_price = outputs[comp_code]
            buy_price /= 50
            sell_price /= 50
            if (best_event is None or buy_action > best_buy) and comp_code not in self.portfolio and abs(buy_price) < .1:
                best_event = event
                best_buy = buy_action
                best_price = round(event.event['price'] * (1+buy_price), 2)
            outputs1 = [buy_action, buy_price, sell_price]
            outputs1 = [(x+1)/2 for x in outputs1]
            outputs2.append(outputs1)
            self.add_sell_order(event, sell_price, orders)
        self.prev_events = prev_events
        if self.verbose and best_event is not None:
            print("Best buy:", best_event.event['comp_code'], best_buy, best_event.event['price'], best_price)
        self.orders = orders
        n_buys = sum(1 if self.orders[x]['buy'] else 0 for x in self.orders)
        if self.cash > 200 and best_event is not None and n_buys == 0:
            capital = self.get_capital()
            n = math.floor(capital / best_price * best_buy * (1 - self.provision))
            n = min(n, math.floor(self.cash / best_price * (1 - self.provision)))
            if n > 0:
                comp_code = best_event.event['comp_code']
                self.orders[comp_code] = {'buy':True, 'price':best_price, 'n_shares':n}
        for comp_code in self.portfolio:
            self.portfolio[comp_code]['n_ticks'] += 1
        self.n_ticks += 1
        return inputs, outputs2

    def fit(self, x, y):
        x = np.array(x)
        y = list(zip(*y))
        y = [np.array(x) for x in y]
        with open('/dev/null', 'w') as f:
            sys.stdout = f
            #self.model.fit(x, y)
            self.model.train_on_batch(x, y)
            sys.stdout = sys.__stdout__

    def train_init(self, events):
        events2 = {}
        inputs = []
        outputs = []
        for event in events:
            comp_code = event.event['comp_code']
            events2[comp_code] = event
        self.event_hist.append(events2)
        if len(self.event_hist) > 10:
            del self.event_hist[0]
        for event in events:
            comp_code = event.event['comp_code']
            if comp_code not in self.event_hist[0]:
                continue
            first_event = self.event_hist[0][comp_code]
            min_gain1 = None
            max_gain = None
            for prev_event in self.event_hist[1:]:
                if comp_code not in prev_event:
                    continue
                gain = prev_event[comp_code].get_price() / first_event.get_price() - 1
                if min_gain1 is None:
                    min_gain1 = gain
                else:
                    if max_gain is None or gain > max_gain:
                        max_gain = gain
                        min_gain2 = min_gain1
                    if gain < min_gain1:
                        min_gain1 = gain
            if max_gain is not None:
                inputs1 = self.get_inputs(first_event)
                inputs.append(inputs1)
                buy_action = max_gain + min_gain1 * .5
                buy_action = 4000000 * buy_action / (1 + 8000000 * abs(buy_action))
                buy_price = max(-1, min(0, min_gain2 * 50))
                sell_price = min(1, max(0, max_gain * 50))
                output1 = [buy_action, buy_price, sell_price]
                output1 = [(x+1)/2 for x in output1]
                outputs.append(output1)
        if inputs:
            self.fit(inputs, outputs)

    def reset(self):
        self.score = 0
        self.min_weekly = None
        self.weekly_ticks = 0
        self.n_ticks = 0
        self.week_start_val = None
        self.portfolio = {}
        self.orders = {}
        self.cash = 1000
        self.event_hist = []
        self.n_bought = 0
        self.n_sold = 0
        self.price_up = []
        self.price_down = []
        self.prev_events = None
        
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
        self.score += score + min(1,len(self.portfolio)) / 10000 + self.n_sold / self.n_ticks / 2000

    def set_max_w(self, max_w, max_c, max_s):
        self.max_w = max_w
        self.max_c = max_c
        self.max_s = max_s

    def get_max_w(self):
        return self.max_w, self.max_c, self.max_s

    def get_train_outputs(self, events, inputs):
        outputs = self.get_test_outputs(events, inputs)
        self.grad = []
        grad_base = None
        for event_i, event in enumerate(events):
            comp_code = event.event['comp_code']
            input1 = inputs[event_i]
            if grad_base is None:
                grad_base = [[random.uniform(-self.max_w, self.max_w) for y in inputs[0]] + [random.uniform(-self.max_c, self.max_c)] for x in outputs[comp_code]]
                sign = [random.uniform(-self.max_s, self.max_s) for x in outputs[comp_code]]
            grad = [sum((input1[xi] if xi < len(input1) else 1) * x for xi, x in enumerate(grad_base[oi])) for oi in range(len(grad_base))]
            outputs[comp_code] = [min(1, max(-1, s * (x + y))) for x, y, s in zip(outputs[comp_code], grad, sign)]
            self.grad.append(grad)
        self.sign = sign
        max_w = np.average(np.absolute([x[:-1] for x in grad_base]))
        max_c = np.average(np.absolute([x[-1] for x in grad_base]))
        max_s = np.average(np.absolute(sign))
        self.max_w = (9 * self.max_w + 2*max_w) / 10
        self.max_c = (9 * self.max_c + 2*max_c) / 10
        self.max_s = (9 * self.max_s + 2*max_s) / 10
        return outputs

    def train(self, events):
        inputs, outputs = self.next(events, self.get_train_outputs)
        self.fit(inputs, outputs)
        
def compare_agents(agent1, agent2, hist=False, quick=False):
    scores1 = []
    scores2 = []
    offset_range = [0] if hist else [-1,0,1]
    for offset in offset_range:
        if hist:
            simulator = glue_utils.HistSimulator(db, event_table_name)
        else:
            simulator = glue_utils.Simulator(bucket, offset)
        agent1.reset()
        agent2.reset()
        max_it = 100000 if hist else 500
        if quick:
            max_it = 200
        quote_dt = None
        for it in range(max_it):
            events = simulator.next()
            if events is None:
                print("Stopping after", it, "iterations, quote_dt:", quote_dt)
                break
            quote_dt = events[0].event['quote_dt']
            agent1.test(events)
            agent2.test(events)
        scores1.append(agent1.score)
        scores2.append(agent2.score)
        print("Capital:", agent1.get_capital(), agent2.get_capital())
        print("Bought/Sold:", agent1.n_bought, "/", agent1.n_sold, "-", agent2.n_bought, "/", agent2.n_sold)
        if not quick:
            print("Price up/down:", np.average(agent1.price_up), "/", np.average(agent1.price_down))
            simulator.print_sample_quotes()
    score1 = np.average(scores1) + min(scores1) / 3
    score2 = np.average(scores2) + min(scores2) / 3
    return score1, score2
