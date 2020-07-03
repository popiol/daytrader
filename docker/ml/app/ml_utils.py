import boto3
import os
import tensorflow.keras as keras
import pickle

bucket_name = os.environ['BUCKET_NAME']
s3 = boto3.resource("s3")
bucket = s3.Bucket(bucket_name)

def s3_download(bucket, obj_key):
    filename = obj_key.split('/')[-1]    
    f_in = bucket.Object(obj_key).get()
    with open(filename,'w') as f_out:
        f_out.write(f_in['Body'].read())

s3_download(bucket, 'scripts/glue_utils.py')

import glue_utils

class Agent():
    def __init__(self, agent_name, bucket):
        try:
            obj_key = f'model/{agent_name}_model.pickle'
            f = bucket.Object(obj_key).get()
            model = f['Body'].read()
            self.model = pickle.loads(model)
        except:
            pricech_model = glue_utils.PriceChModel(bucket)
            in_shape = pricech_model.get_input_shape()
            in_shape[0] += 1
            inputs = keras.layers.Input(shape=in_shape)
            hidden1 = keras.layers.Dense(100, activation="relu")(inputs)
            buy_action = keras.layers.Dense(1, activation="sigmoid")(hidden1)
            buy_price = keras.layers.Dense(1, activation="sigmoid")(hidden1)
            sell_price = keras.layers.Dense(1, activation="sigmoid")(hidden1)
            self.model = keras.Model(inputs=inputs, outputs=[buy_action, buy_price, sell_price])
        self.portfolio = {}
        self.orders = {}
        self.bucket = bucket
        self.cash = 1000
        self.agent_name = agent_name

    def save(self):
        model = pickle.dumps(self.model)
        obj_key = f'model/{self.agent_name}_model.pickle'
        self.bucket.put_object(Key=obj_key, Body=model)

    def rename(self, agent_name):
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
        if comp_code in self.orders:
            if self.orders[comp_code]['buy'] and self.orders[comp_code]['price'] > float(event.event['low_price']):
                self.portfolio[comp_code] = self.orders[comp_code]
                self.portfolio[comp_code]['n_ticks'] = 1
                self.cash -= self.portfolio[comp_code]['n_shares'] * self.orders[comp_code]['price']
                print("Buy", self.portfolio[comp_code]['n_shares'], "shares of", comp_code, "for", self.orders[comp_code]['price'])
                print("Cash:", self.cash)
            elif not self.orders[comp_code]['buy'] and self.orders[comp_code]['price'] < float(event.event['high_price']):
                del self.portfolio[comp_code]
                self.cash += self.portfolio[comp_code]['n_shares'] * self.orders[comp_code]['price']
                print("Sell", self.portfolio[comp_code]['n_shares'], "shares of", comp_code, "for", self.orders[comp_code]['price'])
                print("Cash:", self.cash)
        
    def add_sell_order(self, event, sell_price_ch):
        comp_code = event.event['comp_code']
        price = event.event['price']
        orders = {}
        if comp_code in self.portfolio and abs(sell_price_ch) > .1:
            self.portfolio[comp_code]['price'] = price
            sell_price = price * (1+sell_price_ch)
            orders[comp_code] = {'buy':False, 'price':sell_price}
        return orders

    def next(self, events, get_outputs):
        inputs = []
        outputs = []
        best_comp_code = None
        orders = {}
        for event in events:
            comp_code = event.event['comp_code']
            self.handle_orders(event)
            buy_action, buy_price, sell_price = get_outputs(event)
            if (best_comp_code is None or buy_action > best_buy) and comp_code not in self.portfolio and abs(buy_price) < .1:
                best_comp_code = comp_code
                best_buy = buy_action
                best_price = event.event['price'] * (1+buy_price)
            inputs.append(self.get_inputs(event))
            outputs.append([buy_action, buy_price, sell_price])
            orders.update(self.add_sell_order(event, sell_price))
        self.orders = orders
        if self.cash > 200:
            n = math.floor(self.cash / best_price)
            if n > 0:
                self.orders[comp_code] = {'buy':True, 'price':best_price, 'n_shares':n}
        for comp_code in self.portfolio:
            self.portfolio[comp_code]['n_ticks'] += 1
        return inputs, outputs

    def get_train_init_outputs(self, event):
        comp_code = event.event['comp_code']
        price = event.get_price()
        price8 = event.event['price8']
        price4 = event.event['price4']
        price32 = event.event['price32']
        triangle = (price8 - price4 - 2*abs(price8 - price4)) / price
        triangle = triangle / (abs(triangle) + 1)
        buy = 1 if triangle > 0 and price32 / price > -.01 else 0
        buy_action = (triangle + 3) / 4 if buy else (triangle + 1) / 4
        buy_price = 0
        n_ticks = self.get_n_ticks(comp_code)
        sell_price = max((8 - n_ticks) * .04, 0)
        return buy_action, buy_price, sell_price

    def train_init(self, events):
        inputs, outputs = self.next(events, self.get_train_init_outputs)
        self.model.fit(inputs, outputs)

    def train(self, events):
        pass

    def test(self, events):
        pass
