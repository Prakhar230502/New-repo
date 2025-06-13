import time
from kiteconnect import KiteConnect
import config
import openpyxl
from datetime import datetime
import database
import excel_functions


class Order:
    """Class to represent an order"""
    def __init__(self, tradingsymbol, exchange, quantity, price, side):
        self.tradingsymbol = tradingsymbol
        self.exchange = exchange
        self.quantity = quantity
        self.price = price
        self.side = side


order = Order("RELIANCE", "BSE", 1, 0, "BUY")


def get_order_side(kite, order_id):
    """Function to get the side of an order"""
    orders = kite.orders()
    for order in orders:
        if order["order_id"] == order_id:
            return order["transaction_type"]
    return None


def place_order(kite, order):
    """Function to place a buy order"""
    transaction_type = kite.TRANSACTION_TYPE_BUY
    if order.side == "BUY":
        transaction_type = kite.TRANSACTION_TYPE_BUY
    else:
        transaction_type = kite.TRANSACTION_TYPE_SELL
        
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            tradingsymbol=order.tradingsymbol,
            exchange=order.exchange,
            transaction_type=transaction_type,
            quantity=order.quantity,
            order_type=kite.ORDER_TYPE_LIMIT,  # Use LIMIT for specific price
            price=order.price,                  # Target price to buy
            product=kite.PRODUCT_CNC,          # CNC for delivery trades
            validity=kite.VALIDITY_DAY,        # Order validity
        )
        print(f"{transaction_type} order placed successfully. Order ID: {order_id}")
        return order_id
    
    except Exception as e:
        print(f"Failed to place order: {str(e)}")


def check_if_order_status_complete(kite, order_id):
    """Function to check the status of an order"""
    order_history = kite.order_history(order_id=order_id)
    if order_history:
        latest_status = order_history[-1]["status"]
        return latest_status == "COMPLETE"
    else:
        print(f"No history found for order {order_id}")
        return None
    

def get_current_price(kite, symbol: str, exchange: str, retries=3, delay=5):
    """Function to get the current price of the stock with retry mechanism"""
    for attempt in range(retries):
        try:
            quote = kite.ltp(f"{exchange}:{symbol}")
            return quote[f"{exchange}:{symbol}"]["last_price"]
        except Exception as e:
            print(f"Error fetching price for {symbol}: {str(e)}. Retrying in {delay} seconds...")
            time.sleep(delay)
    return None


def delete_open_orders(kite):
    """Function to delete all open orders"""
    try:
        orders = kite.orders()
        for order in orders:
            if order["status"] == "OPEN":
                kite.cancel_order(order_id=order["order_id"])
                print(f"Order {order['order_id']} cancelled")
    except Exception as e:
        print(f"Failed to delete open orders: {str(e)}")


def cancel_order(kite, order_id):
    """Function to delete a specific open order given the order id"""
    try:
        kite.cancel_order(order_id=order_id, variety=kite.VARIETY_REGULAR)
        print(f"Order {order_id} cancelled")
    except Exception as e:
        print(f"Failed to delete order {order_id}: {str(e)}")


def start_trading_for_one_symbol(kite, symbol: str, exchange: str, percent: int):
    """Function to start the trading process for one stock"""
    if database.get_data(symbol) is None:
        base_price = get_current_price(symbol, exchange)
        number_of_trades = 0
    else:
        base_price = database.get_data(symbol).last_price
        number_of_trades = database.get_data(symbol).number_of_trades
        
    # Continuously monitor the stock price and place buy or sell orders based on market movement
    while True:
        current_time = datetime.now().time()
        if current_time.hour >= 15 and current_time.minute > 30:
            print("Market closed. Exiting...")
            database.feed_database_in_excel()
            break
        current_price = get_current_price(symbol, exchange)
        if current_price is not None:
            time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{time_now}: Current price of {symbol}: {current_price}")
            if number_of_trades == 0:
                buy_order = Order(symbol, exchange, 1, current_price, "BUY")
                place_order(buy_order)
                print(f"Placing first buy order for {symbol} at {current_price}")
                number_of_trades += 1
                database.update_data(symbol, base_price, number_of_trades, 0)
            elif current_price <= base_price*(100-percent)/100 and number_of_trades < 5:
                base_price = base_price*(100-percent)/100
                print(f"Target buy price {current_price} reached. Placing buy order...")
                buy_order = Order(symbol, exchange, 1, current_price, "BUY") 
                place_order(buy_order)
                number_of_trades += 1
                database.update_data(symbol, base_price, number_of_trades, 0)
            elif current_price >= base_price*100/(100-percent) and number_of_trades > 1:
                database.update_data(symbol, base_price*100/(100-percent), number_of_trades - 1, current_price - base_price)
                base_price = base_price*100/(100-percent)
                print(f"Target sell price {current_price} reached. Placing sell order...")
                sell_order = Order(symbol, exchange, 1, current_price, "SELL") 
                place_order(sell_order)
                number_of_trades -= 1
            elif current_price >= base_price*100/(100-percent):
                base_price = base_price*100/(100-percent)
                print("Changing base price")
                database.update_data(symbol, base_price, number_of_trades, 0)

        else:
            print("Failed to fetch current price. Retrying...")
        
        print("Sleeping for 10 seconds...")
        time.sleep(10)


def get_filled_quantity(kite, order_id):
    """
    Returns the filled quantity for a given order_id using Kite Connect.
    """
    # kite = get_kite_client()  # Make sure this returns an authenticated KiteConnect instance
    orders = kite.orders()
    for order in orders:
        if order['order_id'] == order_id:
            return order['filled_quantity']
    return 0

def get_ticker_quantity(kite, ticker):
    """
    Returns the quantity of shares for a given ticker in holdings.
    """
    holdings = kite.holdings()
    for holding in holdings:
        if holding['tradingsymbol'] == ticker:
            return holding['quantity']
    return 0
  
def get_ticker_positions(kite, ticker):
    """
    Returns the positions for a given ticker.
    """
    positions = kite.positions()
    for position in positions['day']:
        if position['tradingsymbol'] == ticker:
            return position['quantity']
    return 0

def get_t1_positions(kite, ticker):
    """
    Returns the T1 positions for a given ticker.
    """
    positions = kite.positions()
    for position in positions['net']:
        if position['tradingsymbol'] == ticker:
            return position.get('t1_quantity', 0)
    return 0

def get_nifty_day_change(kite):
    """
    Returns the day change (points and percent) for NIFTY 50.
    """
    symbol = "NIFTY 50"
    exchange = "NSE"
    quote = kite.quote(f"{exchange}:{symbol}")
    last_price = quote[f"{exchange}:{symbol}"]["last_price"]
    prev_close = quote[f"{exchange}:{symbol}"]["ohlc"]["close"]  # Use ohlc['close'] for previous close
    change = last_price - prev_close
    change_percent = (change / prev_close) * 100
    return change_percent

def increase_quantity(multiplier: int):
    """
    Increases the quantity of shares in the database by a given multiplier.
    """
    data = database.get_all_data()
    for row in data:
        changed_quantity = row.number_of_trades * multiplier * config.shares_quantity.get(row.tradingsymbol, 1)
        # database.update_data(row.tradingsymbol, row.last_price, new_quantity, row.pnl)
        buy_order = Order(row.tradingsymbol, "NSE", changed_quantity, get_current_price(row.tradingsymbol, "NSE"), "BUY")
        order_id = place_order(buy_order)



if __name__ == '__main__':
    # print(get_filled_quantity("250526701318092"))
    # print(get_t1_positions("EIEL"))
    # start_trading_for_one_symbol("NMDC", "NSE", 0.25)
    # delete_open_orders()
    # print(cancel_order("250313800255989"))
    # start_trading_for_one_symbol("SHAILY", "BSE", 3)
    # place_order(Order("SHAILY", "BSE", 1, 1812, "SELL"))
    # print(get_nifty_day_change())
    # price = (get_current_price("NIFTY 50", "NSE"))
    # print(f"Price: {price}")
    # database.update_data("MSUMI", 52, 0, 0)
    # database.delete_data("MSUMI")
    # print(database.get_data("MSUMI"))
    # increase_quantity(1)
    # print(price)
    # order = Order("NBCC", "BSE", 1, price, "BUY")
    # place_order(order)
    # log_order_to_excel(order)
    # print(database.get_all_data())
    # for ric in config.large_cap_shares:
    #     price = (get_current_price(ric, "NSE"))
    #     place_order(Order(ric, "NSE", 1, price, "BUY"))
    # print(f"{ric}: {price}")
    print("All operations completed successfully.")
    
