from account import *
import time
import database as db
import pandas as pd

def get_time():  # เวลาปัจจุบัน
    named_tuple = time.localtime() # get struct_time
    Time = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
    return Time

def get_price(pair):
    price = float(exchange.fetch_ticker(pair)['last'])
    return price

def get_ask_price(pair):
    ask_price = float(exchange.fetch_ticker(pair)['ask'])
    return ask_price

def get_bid_price(pair):
    bid_price = float(exchange.fetch_ticker(pair)['bid'])
    return bid_price

def get_remain_open(id):
    for i in exchange.private_get_orders()['result']:
        if i['id'] == id:
            remain = i['remainingSize']
    return remain

def get_pending_buy(pair):
    pending_buy = []
    for i in exchange.fetch_open_orders(pair):
        if i['side'] == 'buy':
            pending_buy.append(i['info'])
    return pending_buy

def get_pending_sell(pair):
    pending_sell = []
    for i in exchange.fetch_open_orders(pair):
        if i['side'] == 'sell':
            pending_sell.append(i['info'])
    return pending_sell

def create_buy_order(pair, buy_size, buy_price, order_type="limit", post_only=True):
    # Order Parameter
    types = order_type
    side = 'buy'
    size = buy_size
    price = buy_price
    exchange.create_order(pair, types, side, size, price, {'postOnly': post_only})

    
def create_sell_order(pair, sell_size, sell_price, order_type="limit", post_only=True):
    # Order Parameter
    types = order_type
    side = 'sell'
    size = sell_size
    price = sell_price
    exchange.create_order(pair, types, side, size, price, {'postOnly': post_only})
    
def cancel_order(order_id):
    if exchange.cancel_order(order_id):
        print("Order ID : {} Successfully Canceled".format(order_id))

def get_minimum_size(pair):
    minimum_size = float(exchange.fetch_ticker(pair)['info']['minProvideSize'])
    return minimum_size

def get_step_size(pair):
    step_size = float(exchange.fetch_ticker(pair)['info']['sizeIncrement'])
    return step_size

def get_step_price(pair):
    step_price = float(exchange.fetch_ticker(pair)['info']['priceIncrement'])
    return step_price

def get_min_trade_value(pair, price):
    min_trade_value = float(exchange.fetch_ticker(pair)['info']['sizeIncrement']) * price
    return min_trade_value

def get_wallet_details():
    wallet = exchange.privateGetWalletBalances()['result']
    return wallet

def get_total_port_value(qoute_currency, asset_name):
    wallet = exchange.privateGetWalletBalances()['result']
    token_lst = [[item['coin'],item['usdValue']] for item in wallet]
    total_port_value = 0
    
    for token in token_lst:
        if token[0] == qoute_currency or token[0] == asset_name:
            asset_value = round(float(token[1]),2)
            total_port_value += asset_value
    return total_port_value

def get_asset_value(asset_name):
    wallet = exchange.privateGetWalletBalances()['result']
    token_lst = [[item['coin'],item['usdValue']] for item in wallet]
    asset_value = 0
    
    for token in token_lst:
        if token[0] == asset_name:
            value = round(float(token[1]),2)
            asset_value += value
    return float(asset_value)

def get_cash(qoute_currency):
    wallet = exchange.privateGetWalletBalances()['result']
    
    for t in wallet:
        if t['coin'] == qoute_currency:
            cash = float(t['availableWithoutBorrow'] )
    return cash


def buy_execute(pair, asset_name, buy_size, buy_price):
    # check pending buy order
    pending_buy = get_pending_buy(pair)
    
    if pending_buy == []:
        print('Buying {} Size = {}'.format(asset_name, buy_size))
        create_buy_order(pair, buy_size, buy_price, order_type="limit", post_only=True)
        time.sleep(5)
        pending_buy = get_pending_buy(pair)

        if pending_buy != []:
            pending_buy_id = get_pending_buy(pair)[0]['id']
            print('Buy Order Created Success, Order ID: {}'.format(pending_buy_id))
            price = get_price(pair)
            step = get_step_price(pair)
            remain = int(get_remain_open(pending_buy_id))
            while remain > 0 or abs(price - buy_price) < (3 * step) :
                print('Waiting For Buy Order To be Filled')
                print("------------------------------")
                time.sleep(10)
                remain = get_remain_open(pending_buy_id)
                if remain == 0:
                    print("Buy order Matched")
                    print("Updating Trade Log")
                    db.update_trade_log(pair)
                    print("------------------------------")

        else:
            print('Buy Order is not match, Resending...')
            pending_buy_id = get_pending_buy(pair)[0]['id']
            order_id = pending_buy_id
            cancel_order(order_id)  
    else:
        pending_buy_id = get_pending_buy(pair)[0]['id']
        print("Pending Buy Order Founded ID: {}".format(pending_buy_id))
        print('Waiting For Buy Order To be filled')
        time.sleep(10)
        
        if pending_buy == []:
            print("Buy order Matched or Cancelled")
            print("Updating Trade Log")
            db.update_trade_log(pair)
            print("------------------------------")
        else:    
            print("Canceling pending Order")
            order_id = pending_buy_id
            cancel_order(order_id)
            time.sleep(2)
            pending_buy = get_pending_buy()

        if pending_buy == []:
            print('Buy Order Matched or Cancelled')
        else:
            print('Buy Order is not Matched or Cancelled, Retrying')
    print("------------------------------")

def sell_execute(pair, asset_name, sell_size, sell_price):
    pending_sell = get_pending_sell(pair)

    if pending_sell == []:
        print('Selling {} Size = {}'.format(asset_name, sell_size))
        create_sell_order()
        time.sleep(3)
        pending_sell = get_pending_sell()

        if pending_sell != []:
            pending_sell_id = get_pending_sell()[0]['id']
            print('Sell Order Created Success, Order ID: {}'.format(pending_sell_id))
            price = get_price(pair)
            step = get_step_price(pair)
            remain = get_remain_open(pending_sell_id)
            while remain > 0 or abs(price - sell_price) < (3 * step) :
                print('Waiting For Sell Order To be filled')
                print("------------------------------")
                time.sleep(10)
                remain = get_remain_open(pending_sell_id)
                if remain == 0:
                    print("Sell order Matched")
                    print("Updating Trade Log")
                    db.update_trade_log(pair)
                    print("------------------------------")
            
        else:
            print('Sell Order is not match, Resending...')
            pending_sell_id = get_pending_sell()[0]['id']
            order_id = pending_sell_id
            cancel_order(order_id)

    else:
        pending_sell_id = get_pending_sell()[0]['id']
        print("Pending Sell Order Found")
        print('Waiting For Sell Order To be filled')
        time.sleep(10)
        
        if pending_sell == []:
            print("Sell order Matched or Cancelled")
            print("Updating Trade Log")
            db.update_trade_log(pair)
            print("------------------------------")
        else:
            print("Canceling pending Order")
            order_id = pending_sell_id
            cancel_order(order_id)
            time.sleep(3)
            pending_sell = get_pending_sell()

        if pending_sell == []:
            print('Sell Order Matched or Cancelled')
        else:
            print('Sell Order is not Matched or Cancelled, Retrying')
    print("------------------------------")

def get_last_trade_price(pair):
    pair = pair
    trade_history = pd.DataFrame(exchange.fetchMyTrades(pair, limit = 1),
                            columns=['id', 'timestamp', 'datetime', 'symbol', 'side', 'price', 'amount', 'cost', 'fee'])
    last_trade_price = trade_history['price']
    
    return float(last_trade_price)    