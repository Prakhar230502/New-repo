from kiteconnect import KiteConnect
import browser_test
import kite_functions
import time
from datetime import datetime, time as dt_time
import config
import excel_functions

base_price = {}
number_of_trades = {}
open_order = {}
bool_for_symbol = {}


"""Function to start the multiple trading process"""
def multiple_trading(kite, user_id: str, symbols: dict, exchange: str, percent: int):
    now = datetime.now()
    start_time = dt_time(9, 15)
    if now.time() < start_time:
        wait_seconds = (datetime.combine(now.date(), start_time) - now).total_seconds()
        print(f"{user_id}: Waiting until 9:15 am to start trading... Sleeping for {int(wait_seconds)} seconds.")
        time.sleep(wait_seconds + 10)
    print(f"{user_id}: Starting multiple trading process for {user_id}")
    buy_trades = 0
    sell_trades = 0
    base_change = 0
    excel_symbols = excel_functions.read_symbols(user_id)
    for symbol in excel_symbols:
        if symbol not in symbols.keys():
            print(f"{user_id}: Symbol {symbol} not found in the config. Skipping...")
            continue
        if excel_functions.get_last_price_for_symbol(user_id, symbol) is None:
            base_price[symbol] = kite_functions.get_current_price(kite, symbol, exchange)
            number_of_trades[symbol] = 0
        else:
            base_price[symbol] = excel_functions.get_last_price_for_symbol(user_id, symbol)
            number_of_trades[symbol] = excel_functions.get_lots_for_symbol(user_id, symbol)

            
    """Function to start the trading process"""
    # Continuously monitor the stock price and place buy or sell orders based on market movement
    while True:
        current_time = datetime.now().time()
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if current_time.hour >= 15 and current_time.minute > 28:
            print(f"{user_id}: Market closed. Exiting...")
            print(user_id + " trading orders:")   
            print(f"{user_id}: {time_now}: Total buy trades: {buy_trades}")
            print(f"{user_id}: {time_now}: Total sell trades: {sell_trades}")
            print(f"{user_id}: {time_now}: Total base changes: {base_change}")
            excel_functions.append_trading_orders(user_id, buy_trades, sell_trades, base_change)
            break
        if buy_trades >= 50: 
            print(f"{user_id}: {time_now}: Total buy trades reached 50. No more buying will be done.")
        print(f"{user_id}: {time_now}: Checking price...")

        for key, value in open_order.items():
            time.sleep(2)
            order_status = kite_functions.check_if_order_status_complete(kite, value)
            if order_status:
                print(f"{user_id}: {time_now}: Order for {key} completed. Deleting order id {value}")
                if kite_functions.get_order_side(kite, value) == "SELL":
                    excel_functions.upsert_symbol_row(user_id, key, number_of_trades[key], base_price[key])
                    sell_trades += 1
                else:
                    buy_trades += 1
            else:
                kite_functions.cancel_order(kite, value)
                filled_quantity = kite_functions.get_filled_quantity(kite, value)
                if kite_functions.get_order_side(kite, value) == "BUY":
                    if filled_quantity > 0 and filled_quantity < symbols[key]:
                        square_off_sell_order = kite_functions.Order(key, exchange, filled_quantity, kite_functions.get_current_price(kite, key, "NSE"), "SELL")
                        kite_functions.place_order(kite, square_off_sell_order)
                        print(f"{user_id}: {time_now}: Placing square off sell order for {key} at {kite_functions.get_current_price(kite, key, 'NSE')}")

                    number_of_trades[key] -= 1
                    if number_of_trades[key] == 0:
                        base_price[key] = kite_functions.get_current_price(kite, key, exchange)
                    else:
                        base_price[key] = base_price[key]*100/(100-percent)
                else:
                    if filled_quantity > 0 and filled_quantity < symbols[key]:
                        square_off_buy_order = kite_functions.Order(key, exchange, filled_quantity, kite_functions.get_current_price(kite, key, "NSE"), "BUY")
                        kite_functions.place_order(kite, square_off_buy_order)
                        print(f"{user_id}: {time_now}: Placing square off buy order for {key} at {kite_functions.get_current_price(kite, key, 'NSE')}")

                    number_of_trades[key] += 1
                    base_price[key] = base_price[key]*(100-percent)/100
                excel_functions.upsert_symbol_row(user_id, key, number_of_trades[key], base_price[key])
                print(f"{user_id}: {time_now}: Order for {key} cancelled. Changing base price to {base_price[key]}")
        open_order.clear()
        for symbol in excel_symbols:
            time.sleep(0.15)
            current_price = kite_functions.get_current_price(kite, symbol, exchange)
            order_id = None
            if current_price is not None:
                time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Place the first buy order if no trades have been made yet
                if number_of_trades[symbol] == 0:
                    time.sleep(1)
                    buy_order = kite_functions.Order(symbol, exchange, symbols[symbol], current_price, "BUY")
                    print(f"{user_id}: {time_now}: Placing first buy order for {symbol} at {current_price}")
                    order_id = kite_functions.place_order(kite, buy_order)
                    if order_id is not None:
                        number_of_trades[symbol] += 1
                        excel_functions.upsert_symbol_row(user_id, symbol, number_of_trades[symbol], base_price[symbol])
                # If current price is less than the base price by 3% and number of trades are less than 5, place a buy order
                elif current_price <= base_price[symbol]*(100-percent)/100 and number_of_trades[symbol] < 5 and buy_trades < 50 and kite_functions.get_nifty_day_change(kite) > -4: 
                    print(f"{user_id}: {time_now}: Target buy price {current_price} for {symbol} reached. Placing buy order... Current number of trades = {number_of_trades[symbol]+1}")
                    buy_order = kite_functions.Order(symbol, exchange, symbols[symbol], current_price, "BUY") 
                    order_id = kite_functions.place_order(kite, buy_order)
                    if order_id is not None:
                        base_price[symbol] = base_price[symbol]*(100-percent)/100
                        number_of_trades[symbol] += 1
                        excel_functions.upsert_symbol_row(user_id, symbol, number_of_trades[symbol], base_price[symbol])
                # If current price is greater than the base price by 3% and number of trades are greater than 1, place a sell order
                elif current_price >= base_price[symbol]*100/(100-percent) and number_of_trades[symbol] > 1:
                    print(f"{user_id}: {time_now}: Target sell price {current_price} for {symbol} reached. Placing sell order... Current number of trades = {number_of_trades[symbol]-1}")
                    sell_order = kite_functions.Order(symbol, exchange, symbols[symbol], current_price, "SELL") 
                    order_id = kite_functions.place_order(kite, sell_order)
                    if order_id is not None:
                        base_price[symbol] = base_price[symbol]*100/(100-percent)
                        number_of_trades[symbol] =  number_of_trades[symbol] - 1
                        excel_functions.upsert_symbol_row(user_id, symbol, number_of_trades[symbol] - 1, base_price[symbol]*100/(100-percent))
                # If current price is greater than the base price by 3% and number of trades are equal to 1, update the base price
                elif current_price >= base_price[symbol]*100/(100-percent):
                    base_change = base_change + 1
                    base_price[symbol] = base_price[symbol]*100/(100-percent)
                    excel_functions.upsert_symbol_row(user_id, symbol, number_of_trades[symbol], base_price[symbol])
                    print(f"{user_id}: {time_now}: Changing base price for {symbol} to {base_price[symbol]}")

                if order_id is not None:
                    open_order[symbol] = order_id
            else:
                print(f"{user_id}: {time_now}: Failed to fetch current price for {symbol}. Retrying...")
            
        time.sleep(10)

def start_multiple_trading(user_id: str, symbols: dict, exchange: str, percent: int):
    """
    Function to start the multiple trading process for a given set of symbols and exchange.
    """
    kite = KiteConnect(api_key=config.config_keys[user_id]["api_key"])
    kite.set_access_token(excel_functions.get_access_token(user_id))
    browser_test.generate_automated_access_token(user_id)
    time.sleep(2)
    multiple_trading(kite, user_id, symbols, exchange, percent)


if __name__ == '__main__':

    symbols = config.shares_quantity
    start_multiple_trading("UZ4820", symbols, "NSE", 3)
    # symbols = ["SHAILY"]
    # symbols = ["NBCC"]
    # buy_order = kite_functions.Order("NBCC", "NSE", config.shares_quantity["NBCC"], kite_functions.get_current_price("NBCC", "NSE"), "BUY") 
    # order_id = kite_functions.place_order(buy_order)
    # for symbol in symbols: 
    #     print(f"{symbol} quantity: {2000/kite_functions.get_current_price(symbol, 'NSE')}")
    # database.delete_all_data()
    # print(database.get_all_data())
    # database.delete_data("RELIANCE")
    # database.delete_data("INFY")
    # print(config.shares_quantity["MSUMI"])
    