#https://github.com/binance/binance-spot-api-docs/blob/master/faqs/trailing-stop-faq.md  refer this 
import sys
import tkinter as tk
from tkinter import ttk
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.enums import *
import decimal
import time
import datetime
import subprocess
from decimal import Decimal
import json


# Import API keys from credentials.py file
from credentials import BINANCE_API_KEY, BINANCE_SECRET_KEY
from credentials import base_currency, quote_currency
binance_spot_api = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_SECRET_KEY)
# Initialize Binance client
client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
tradingpair = base_currency + quote_currency


# Initialize Tkinter window
root = tk.Tk()
root.title("Trading Bot")

# Create a label to display error messages # This is used to display the current event status in GUI.
error_label = tk.Label(root, text="Error Display", font=('Arial', 12), fg='red')
error_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

#Important Variables
#order_type = ORDER_TYPE_LIMIT #ORDER_TYPE_MARKET #ORDER_TYPE_LIMIT
# Calculate take profit and stop loss prices
#BTCTUSD 1min chart Short SELL STOP 0.10% TP 0.21% RR 2.22%  ;Long STOP 0.03% TP 0.10%
TP_PERCENT = tk.DoubleVar() #1 # 0.75% Take Profit, 1 means 1%,0.75 means 0.75 percent
SL_PERCENT = tk.DoubleVar() #2 # 0.40% Stop Loss,2 means 2 percent ,0.2 means 0.2 percent


# Function to update percentages
def update_percentages(*args):
    tp_checked = tp_checkbox_var.get()
    sl_checked = sl_checkbox_var.get()

    TP_PERCENT.set(float(tp_percent_entry.get()) if tp_checked else 0)
    SL_PERCENT.set(float(sl_percent_entry.get()) if sl_checked else 0)

    print(f"TP_PERCENT: {TP_PERCENT.get()}%")
    print(f"SL_PERCENT: {SL_PERCENT.get()}%")
    
#create a frame to hold the checkbox
frame = tk.Frame(root)
frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

# Create the checkboxes for TP_PERCENT and SL_PERCENT
tp_checkbox_var = tk.IntVar()
tp_checkbox = tk.Checkbutton(frame, text="Take Profit (%)", variable=tp_checkbox_var, command=update_percentages)
tp_checkbox.grid(row=0, column=0, padx=5, pady=5, sticky="w")

tp_percent_entry = tk.Entry(frame, textvariable=TP_PERCENT, width=10)
tp_percent_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

sl_checkbox_var = tk.IntVar()
sl_checkbox = tk.Checkbutton(frame, text="Stop Loss (%)", variable=sl_checkbox_var, command=update_percentages)
sl_checkbox.grid(row=0, column=2, padx=5, pady=5, sticky="w")

sl_percent_entry = tk.Entry(frame, textvariable=SL_PERCENT, width=10)
sl_percent_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")


# Bind the text box entry to the update_percentages function
tp_percent_entry.bind("<Return>", update_percentages)
sl_percent_entry.bind("<Return>", update_percentages)

#frame.pack(side=tk.TOP, anchor=tk.NE, padx=10, pady=10)



def update_order_type():
    if checkbox_var.get() == 1:
        print("Limit Order Type Selected")
        order_type = ORDER_TYPE_LIMIT
    else:
        print("Market Order Type is Seleceted")
        order_type = ORDER_TYPE_MARKET

# create the checkbox widget
checkbox_var = tk.IntVar()
checkbox = tk.Checkbutton(frame, text="ORDER \n Limit( ✅ ) : Market(✖)", variable=checkbox_var, height=4, width=20, command=update_order_type)

# add the checkbox to the frame
checkbox.grid(row=0, column=4, padx=5, pady=5, sticky="e")

order_type = ORDER_TYPE_MARKET # set default value

#frame.pack()





def get_local_timestamp():
    dt = datetime.datetime.now()
    timestamp = dt.strftime('%Y%m%d%H%M%S%f')
    return timestamp


def buy_btc(percentage_quantity,buy_price_entry,error_textbox):
    error_label.config(text=f'BUY ORDER Initiated:{tradingpair}', fg='green')
    # Get total TUSD balance
    total_usd_balance = float(client.get_asset_balance(asset=quote_currency)['free'])

    # Calculate quantity to buy
    quote_quantity = float(total_usd_balance * percentage_quantity)

    # Get current market price
    ticker = client.get_symbol_ticker(symbol=tradingpair)
    current_price = float(ticker['price'])
    quantity = round(float( quote_quantity / (current_price + 1) ),5) # This 10 added to get correct quantity this i am doing to get tradable quantity
    print(f"Total Balance available: {total_usd_balance} {quote_currency},Quantity to buy: {quantity} {base_currency},Current price : {current_price} {quote_currency}.")
    if quantity <= 0.0001:
        print("Error: Invalid quantity to Buy or insufficient Quantity. Please try again.\n")
        return
    # Place market buy order
    order_id = get_local_timestamp()
    try:
        if order_type == ORDER_TYPE_LIMIT:
            print("Limit Buy Order")
            order = client.create_order(
                symbol=tradingpair,
                side=SIDE_BUY,
                type=order_type,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=current_price - 2
            )
        else:
            print("Market Buy Order")
            order = client.create_order(
                symbol=tradingpair,
                side=SIDE_BUY,
                type=order_type,
                quantity=quantity
            )
        print(f"BUY Order created quantity :{quantity} {base_currency} @price:{current_price} {quote_currency}.")
    except BinanceAPIException as e:
        print(f"Error occurred while creating the order: {e}")

def place_oco_order(side,error_textbox):
    error_label.config(text=f'OCO ORDER Initiated: Both SL and TP will be placed {tradingpair} for the previous {side}', fg='blue')
    try:
        account_info = client.get_account()
        positions = account_info['balances']
        
        base_asset = base_currency.upper()
        quote_asset = quote_currency.upper()
        
        freeBaseCurrencyVal = 0.0
        freeQuoteCurrencyVal = 0.0
        
        for position in positions:
            asset = position['asset']
            free = float(position['free'])
            locked = float(position['locked'])
            
            if asset == base_asset:
                freeBaseCurrencyVal = free
            elif asset == quote_asset:
                freeQuoteCurrencyVal = free
    except BinanceAPIException as e:
        print(f"Error occurred while fetching spot position details: {e}")
    try:
        # Fetch the latest order
        orders = client.get_all_orders(symbol=tradingpair, limit=10)
        if len(orders) > 0:
            latest_order = orders[0]
            symbol = latest_order['symbol']
            executed_qty = float(latest_order['executedQty'])
            cummulative_quote_qty = float(latest_order['cummulativeQuoteQty'])
            status = latest_order['status']
            # Fetch the last traded price
            ticker = client.get_symbol_ticker(symbol=symbol)
            last_price = float(ticker['price'])
            print(f"Latest order status: {latest_order['status']}")
            print(f"Executed quantity: {executed_qty}")
            print(f"Cummulative quote quantity: {cummulative_quote_qty}")
            print(f"Last traded price: {last_price}")
        else:
            print("No orders found.")

    except BinanceAPIException as e:
        print(f"Error occurred while fetching order status: {e}")
    symbol_info = client.get_symbol_info(tradingpair)
    price_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
    
    min_price = float(price_filter['minPrice'])
    max_price = float(price_filter['maxPrice'])
    
    symbol_info = client.get_symbol_info(tradingpair)
    lot_size_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
    min_quantity = float(lot_size_filter['minQty'])
    max_quantity = float(lot_size_filter['maxQty'])
    # Calculate the take profit and stop limit prices based on the side
    if side == "BuyCoverSellOrder":
        take_profit_price = last_price * (1 + TP_PERCENT.get() / 100) # Output: 110.0 if price is 100 and 10% setting price =buyprice
        stop_limit_price = last_price * (1 - SL_PERCENT.get() / 100)  # Output: 90 if price is 100 and 10% setting
        quantity = executed_qty # Quantity = sellquantity
        side  = SIDE_SELL
        print("This is OCO SELL Side Order for Covering the previous BUY Order")
        if SL_PERCENT.get() != 0:
            print("The Risk Reward Ratio here is:", (TP_PERCENT.get() / SL_PERCENT.get()))
        else:
            print("The Risk Reward Ratio cannot be calculated because the stop-loss percentage is zero.")
            return None
# This code is corrected and working fine do not change the logic When previous order was Sell and you want to place take profit and stop loss this is the code
    elif side == "SellCoverBuyOrder":
        take_profit_price = last_price * (1 - TP_PERCENT.get() / 100) # Output: 90 if price is 100 and 10% setting price =sellprice
        stop_limit_price = last_price * (1 + SL_PERCENT.get() / 100)  # Output: 110 if price is 100 and 10% setting
        quantity = freeQuoteCurrencyVal / stop_limit_price  #quantity =buyquantity sold 0.04074  at 26727.70196613 TUSD (Sell order)  Limit Take Profit 26000  Stop  Stop Limit price 28000 then Amount = 0.03889 quantity = 1088.92 To get quanity = Available TUSD / Stop limit price is what you need to put
        side  = SIDE_BUY
        print("This is OCO BUY Side Order for Covering the previous SELL Order")
        if SL_PERCENT.get() != 0:
            print("The Risk Reward Ratio here is:", (TP_PERCENT.get() / SL_PERCENT.get()))
        else:
            print("The Risk Reward Ratio cannot be calculated because the stop-loss percentage is zero.")
            return None
    else:
        print("Invalid side provided. Please specify either 'BuyCoverSellOrder' or 'SellCoverBuyOrder'.")
        return None

    if take_profit_price < min_price or take_profit_price > max_price:
        print("Take profit price is outside the allowed range.")
        return None

    if stop_limit_price < min_price or stop_limit_price > max_price:
        print("Stop limit price is outside the allowed range.")
        return None
    
    if quantity < min_quantity or quantity > max_quantity:
        print("Quantity is outside the allowed range.")
        return None

    symbol_info = client.get_symbol_info(tradingpair)
    price_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
    quantity_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)

    price_precision = int(price_filter['tickSize'].index('1') - 1)
    quantity_precision = int(quantity_filter['stepSize'].index('1') - 1)

    # Adjust the precision of price and quantity
    take_profit_price = round(take_profit_price, price_precision)
    stop_limit_price = round(stop_limit_price, price_precision)
    quantity = round(quantity, quantity_precision)

    # Place OCO order
    try:
        order = client.create_oco_order(
            symbol=tradingpair,
            side=side,
            quantity=quantity,
            price=take_profit_price, # TUSD in case of Buy order 
            stopPrice=stop_limit_price+1, # trigger price TUSD incase of Buy order
            stopLimitPrice=stop_limit_price, # Execution price TUSD incase of Buy order
            stopLimitTimeInForce=TIME_IN_FORCE_GTC,
        )
        print(f"OCO Order placed successfully from this price : {last_price}.")
        print(f"Take Profit Price: {take_profit_price}")
        print(f"Stop Limit Price: {stop_limit_price}")
        print(f"The Quantity is : {quantity} ")
        print("OCO Order ID:", order['orderListId'])
        print("OCO Order Status:", order['listOrderStatus'])
    except BinanceAPIException as e:
        print(f"Error occurred while placing the OCO order: {e}")
        print("Error code:", e.code)
        print("Error message:", e.message)

    return None

def place_trailing_stop_order(side, percentage_quantity, buy_price_entry, error_textbox, delta_percentage):
    # Get current market price
    ticker = client.get_symbol_ticker(symbol=tradingpair)
    current_price = float(ticker['price'])

    # Calculate the trailing stop price based on the side and delta percentage
    if side == "BuyCoverSellOrder":
        trailing_stop_price = current_price * (1 - delta_percentage / 100)
    elif side == "SellCoverBuyOrder":
        trailing_stop_price = current_price * (1 + delta_percentage / 100)
    else:
        print("Invalid side provided. Please specify either 'BuyCoverSellOrder' or 'SellCoverBuyOrder'.")
        return None

    # Calculate quantity to buy
    total_usd_balance = float(client.get_asset_balance(asset='TUSD')['free'])
    quote_quantity = total_usd_balance * percentage_quantity
    quantity = round(float(quote_quantity / (current_price - 10)), 4)

    # Place trailing stop order
    try:
        if side == "BuyCoverSellOrder":
            order = client.create_order(
                symbol=tradingpair,
                side=SIDE_BUY,
                type=ORDER_TYPE_STOP_LOSS_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=current_price,
                stopPrice=trailing_stop_price,
                trailingStopDelta=trailing_stop_price - current_price
            )
        elif side == "SellCoverBuyOrder":
            order = client.create_order(
                symbol=tradingpair,
                side=SIDE_SELL,
                type=ORDER_TYPE_STOP_LOSS_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=current_price,
                stopPrice=trailing_stop_price,
                trailingStopDelta=trailing_stop_price - current_price
            )
        else:
            print("Invalid side provided. Please specify either 'BuyCoverSellOrder' or 'SellCoverBuyOrder'.")
            return None

        print("Trailing Stop Order placed successfully.")
        print(f"Trailing Stop Price: {trailing_stop_price}")
        return order
    except BinanceAPIException as e:
        print(f"Error occurred while placing the Trailing Stop order: {e}")

    return None



# Define function for selling BTC
def sell_btc(percentage_quantity,buy_price_entry, error_textbox):
    error_label.config(text=f'SELL ORDER Initiated:{tradingpair}', fg='red')
    total_tradingpair = float(client.get_asset_balance(asset=base_currency)['free'])
    print(f"Total {tradingpair} balance available for trading: {total_tradingpair}{base_currency}.")
    if total_tradingpair < 0.0001:
        error_label.config(text=f'Insufficient balance of {tradingpair}', fg='red')
        return
    try:
        # Calculate the quantity to sell (specified percentage of total holding)
        quantity = float (total_tradingpair * ( percentage_quantity ))
        quantity = round(quantity, 5)
        print(f"Quantity to sell:{quantity}{base_currency}.")
        
        # Calculate the sell price (3 points above the current market price)
        ticker = client.get_symbol_ticker(symbol=tradingpair)
        sell_price = float(ticker['price']) + 2
        print("Sell price:", sell_price)
        
        # Place sell order
        order_id = get_local_timestamp()
        print(f"Selling {quantity} {tradingpair} at {sell_price}")
        try:
            if order_type == ORDER_TYPE_LIMIT:
                order = client.create_order(
                    symbol=tradingpair,
                    side=SIDE_SELL,
                    type=order_type,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=quantity,
                    price=sell_price
                )
            else:
                order = client.create_order(
                    symbol=tradingpair,
                    side=SIDE_SELL,
                    type=order_type,
                    quantity=quantity
                )
            print(f"BTC Sell Order created.quantity :{quantity} price:{sell_price}")
        except BinanceAPIException as e:
            print(f"Error occurred while creating the order: {e}")
    except (BinanceAPIException, BinanceOrderException) as e:
        error_label.config(text=str(e), fg='red')
        print(e)

def sell_btc_with_tp_sl(percentage_quantity, error_textbox):
    total_tradingpair = float(client.get_asset_balance(asset=base_currency)['free'])
    print(f"Total {tradingpair} balance available for trading: {total_tradingpair}")
    if total_tradingpair < 0.0001:
        error_label.config(text=f'Insufficient balance of {tradingpair}', fg='red')
        return
    try:
        # Calculate the quantity to sell (specified percentage of total holding)
        quantity = float (total_tradingpair * ( percentage_quantity ))
        quantity = round(quantity, 5)
        print("Quantity to sell:", quantity)

        # Calculate the sell price (3 points above the current market price)
        ticker = client.get_symbol_ticker(symbol=tradingpair)
        sell_price = float(ticker['price']) + 1
        print("Sell price:", sell_price)

        # Calculate the take profit and stop loss prices
        take_profit_price = round(float(sell_price * (1 - TP_PERCENT/100)), 2)
        stop_loss_price = round(float(sell_price * (1 + SL_PERCENT/100)), 2)
        print("Take Profit Price:", take_profit_price)
        print("Stop Loss Price:", stop_loss_price)

        # Place sell order
        order_id = get_local_timestamp()
        print(f"Selling {quantity} {tradingpair} at {sell_price}")
        try:
            order = client.create_order(
                symbol=tradingpair,
                side=SIDE_SELL,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=sell_price
            )
            print(f"BTC Sell Order created.")

            # Place take profit order
            tp_order = client.create_order(
                symbol=tradingpair,
                side=SIDE_BUY,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=take_profit_price
            )
            print(f"Take Profit Order created.")

            # Place stop loss order
            sl_order = client.create_order(
                symbol=tradingpair,
                side=SIDE_BUY,
                type=ORDER_TYPE_STOP_LOSS_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                stopPrice=stop_loss_price
            )
            print(f"Stop Loss Order created.")
        except BinanceAPIException as e:
            print(f"Error occurred while creating the order: {e}")
    except (BinanceAPIException, BinanceOrderException) as e:
        error_label.config(text=str(e), fg='red')
        print(e)


def get_asset_balance(client, asset):
    """Get the balance of a specific asset in the Binance Spot account."""
    account = client.get_account()
    balances = account['balances']
    for balance in balances:
        if balance['asset'] == asset:
            return balance['free']
    return 0.0

def fetch_filled_order_details():
    trades = client.get_my_trades(symbol='BTCTUSD') # Get all trades for the symbol
    
    order_ids = [] # List to store unique order IDs
    recent_order_ids = [] # List to store recent unique order IDs
    for trade in reversed(trades): # Loop through trades in reverse order
        order_id = trade['orderId']
        if order_id not in order_ids:
            order_ids.append(order_id)
            recent_order_ids.append(order_id)
            if len(recent_order_ids) == 5:
                break
    
    order_details = ""
    for order_id in recent_order_ids:
        prices = []
        qtys = []
        quote_qtys = []
        commissions = []
        order_type = ""
        order_subtype = ""
        for trade in trades:
            if trade['orderId'] == order_id:
                prices.append(float(trade['price']))
                qtys.append(float(trade['qty']))
                quote_qtys.append(float(trade['quoteQty']))
                commissions.append(float(trade['commission']))
                if order_type == "":
                    if trade['isBuyer']:
                        order_type = "Buy"
                    else:
                        order_type = "Sell"
                    if trade['isMaker']:
                        order_subtype = "Limit"
                    else:
                        order_subtype = "Market"
                
        avg_price = sum(prices) / len(prices)
        total_qty = sum(qtys)
        total_quote_qty = sum(quote_qtys)
        total_commission = sum(commissions)
        
        order_details += f"Order ID: {order_id}\n"
        order_details += f"Type of Order: {order_type} ({order_subtype})\n"
        order_details += f"Average Price: {avg_price}\n"
        order_details += f"Total Quantity: {total_qty}\n"
        order_details += f"Total Quote Quantity: {total_quote_qty}\n"
        order_details += f"Total Commission: {total_commission}\n\n"
        
    return order_details,order_id,order_type,order_subtype, avg_price,total_qty,total_quote_qty,total_commission

# Define function to update BTCUSDT price every 5 seconds
def update_btc_price(error_textbox):
    try:
        # Get the ticker price
        current_price = decimal.Decimal(client.get_symbol_ticker(symbol=tradingpair)['price'])

        # Set the color of the price box based on whether the current price is higher or lower than the previous price
        if current_price > update_btc_price.previous_price:
            color = 'green'
        else:
            color = 'brown'
        update_btc_price.previous_price = current_price

        # Update label text with current BTCUSDT price and color
        btc_price_label.config(text=f"{tradingpair} Price : {current_price:.2f}", bg=color)

        # Clear any previous error message
        error_label.config(text="")

        # Delete all previous contents of error_textbox
        error_textbox.delete('1.0', 'end')
        #This code prints Free Locked Base and Quote currency details
        asset_balance_response_base = binance_spot_api.get_asset_balance(base_currency)
        if asset_balance_response_base is not None:
            print(f"Free{base_currency}:{asset_balance_response_base.get('free', 0)};Locked:{asset_balance_response_base.get('locked',0)};")
        else:
            print("Failed to get asset balance for base currency.")
        asset_balance_response_quote = binance_spot_api.get_asset_balance(quote_currency)
        if asset_balance_response_quote is not None:
            print(f"Free{quote_currency}:{asset_balance_response_quote.get('free', 0)};Locked:{asset_balance_response_quote.get('locked', 0)}; \n ")
        else:
            print("Failed to get asset balance for quote currency.")
        trades = client.get_my_trades(symbol=tradingpair, limit=1)
        # Print the details of the last trade
        if len(trades) > 0:
            trade = trades[0]
            #print(f"Symbol: {trade['symbol']}, Price: {trade['price']}, Quantity: {trade['qty']}, Side (False is Short): {trade['isBuyer']}")
            error_textbox.tag_configure("tagg", foreground="blue", background="white")
            error_textbox.insert('end',f"Symbol:{trade['symbol']},TradePrice:{float(trade['price'])},Quant:{float(trade['qty'])},Side(FalseShort):{trade['isBuyer']}\n","tagg")
        else:
            print("No trades found for symbol", symbol)
        #This code prints Free Locked Base and Quote currency details
        if asset_balance_response_base is not None:
            error_textbox.insert('end', f"Free {base_currency}: {asset_balance_response_base.get('free', 0)}, Locked: {asset_balance_response_base.get('locked', 0)}\n")
        else:
            error_textbox.insert('end', "Failed to get asset balance for base currency.\n")
        if asset_balance_response_quote is not None:
            free_quote = Decimal(asset_balance_response_quote.get('free', 0))
            equivalent_base_val = free_quote / Decimal(current_price)
            # Configure the tag for the desired color and background
            error_textbox.tag_configure("custom_tag", foreground="blue", background="yellow")
            # Insert the text with the specified tag
            error_textbox.insert('end', f"Free {quote_currency}: {free_quote}, Locked: {asset_balance_response_quote.get('locked', 0)}, Equival BaseVal:{equivalent_base_val:.5f}\n", "custom_tag")

        else:
            error_textbox.insert('end', "Failed to get asset balance for quote currency.\n")
        # Get the overall available account wallet balance
        # Get the overall available account wallet balance
    except BinanceAPIException as e:
        # Display error message if there is an API exception
        error_label.config(text=str(e))

    # Call this function again after 5 seconds
    root.after(15000, update_btc_price,error_textbox)

# Set the previous price to 0 so the initial color is green
update_btc_price.previous_price = decimal.Decimal(0)

# Create a box to display the BTCUSDT price
btc_price_label = tk.Label(root, text="", font=('Arial', 24), bd=10, relief='ridge')
btc_price_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='we')

#This is the middle white box that shows the data update 
error_textbox = tk.Text(root, height=10,width=80)
error_textbox.grid(row=4, column=0, columnspan=2, padx=5, pady=5,sticky="we")



# Add Exit button
def exit_app():
    root.destroy()

def restart_app():
    root.destroy()
    subprocess.run(['python', 'main.py'])
    #or below 
    #python = sys.executable
    #os.execl(python, python, *sys.argv)

def show_order_details():
    order_details,order_id,order_type,order_subtype, avg_price,total_qty,total_quote_qty,total_commission = fetch_filled_order_details()

    # Create a new window to display the order details
    order_window = tk.Toplevel(root)
    order_window.title("Order Details")
    order_window.geometry("400x200")

    # Create a text box to display the order details
    order_text = tk.Text(order_window, wrap="none")
    order_text.insert(tk.END, order_details)
    order_text.pack(side="left", fill="both", expand=True)

    # Add scrollbar to the text box
    scrollbar = tk.Scrollbar(order_window, orient="vertical", command=order_text.yview)
    scrollbar.pack(side="right", fill="y")
    order_text.configure(yscrollcommand=scrollbar.set)
    # Schedule the order_window to be destroyed after a minute
    root.after(60000, order_window.destroy)

def cancel_all_orders():
    try:
        orders = client.get_open_orders()
        for order in orders:
            client.cancel_order(symbol=order['symbol'], orderId=order['orderId'])
        print('All open orders cancelled successfully.')
    except BinanceAPIException as e:
        print('Error occurred while cancelling orders:', e)

# Any text can be passed here to display in the box        
def display_and_delete_text():
    error_textbox.tag_configure("tagg", foreground="blue", background="white")
    error_textbox.insert('end', "WELCOME This is the START\n", "tagg")
    error_textbox.after(15000, lambda: error_textbox.delete('1.0', 'end'))

# Call the function to display the text
display_and_delete_text()



# Add Restart and Exit buttons
exit_button = tk.Button(root, text="ExitGUI", command=exit_app, font=('Arial', 8),fg = "green", bg="orange")
exit_button.grid(row=5, column=0, pady=10)

restart_button = tk.Button(root, text="Restart", command=restart_app, font=('Arial', 8),fg="red", bg="white")
restart_button.grid(row=5, column=1, pady=10)


# Add Buy and Sell buttons
percencent1 = 0.02
buy_button = tk.Button(root, text="BUY " + tradingpair + "_" + str(percencent1 * 100) + "%", command=lambda: buy_btc(float(percencent1),0, error_textbox), font=('Arial', 10),bg="green")
buy_button.grid(row=6, column=0, padx=10, pady=10)  #buy_button.grid(row=6, column=0, columnspan=2, padx=(50, 10), pady=10)

percencent2 = 1
buy_button = tk.Button(root, text="BUY " + tradingpair + "_" + str(percencent2 * 100) + "%", command=lambda: buy_btc(float(percencent2), 0,error_textbox), font=('Arial', 10),bg="green")
buy_button.grid(row=6, column=1, padx=10, pady=10)

percencents2 = 1
sell_button = tk.Button(root, text="SELL " + tradingpair+ "_" + str(percencents2 * 100) + "%", command=lambda: sell_btc(float(percencents2),0,error_textbox), font=('Arial', 10),bg="red")
sell_button.grid(row=6, column=2, padx=10, pady=10)

percencents1 = 0.02
sell_button = tk.Button(root, text="SELL " + tradingpair + "_" + str(percencents1 * 100) + "%", command=lambda: sell_btc(float(percencents1),0, error_textbox), font=('Arial', 10),bg="red")
sell_button.grid(row=6, column=3, padx=10, pady=10)

 # Create a button to show the order details
show_order_button = tk.Button(root, text="Show Order Details", command=show_order_details,font=('Arial', 10), bg="gold")
show_order_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

cancel_button = tk.Button(root, text="Cancel All \n Open orders", command=cancel_all_orders,font=('Arial', 8), bg="yellow")
cancel_button.grid(row=7, column=0,columnspan=2, padx=10, pady=10)

#This i am doing for the sell with tp and sl in spot order
percencents1tp = 0.001
sell_button_tp_sl = tk.Button(root, text="SELL_withTP_SL " + tradingpair + "_" + str(percencents1tp * 100) + "%", command=lambda: sell_btc_with_tp_sl(float(percencents1tp), error_textbox), font=('Arial', 10),bg ="silver")
sell_button_tp_sl.grid(row=7, column=3, padx=10, pady=10)



# Create input fields for quantity and price
buy_quantity_entry = tk.Entry(root, width=10)
buy_quantity_entry.grid(row=8, column=1, padx=1, pady=1)
buy_quantity_entry.insert(0, "Buy Quantity")

buy_price_entry = tk.Entry(root, width=10)
buy_price_entry.grid(row=8, column=2, padx=1, pady=1) #buy_price_entry.pack(side="top", padx=1, pady=1)
buy_price_entry.insert(0, "Buy Price")
# Create buttons for buying and selling with user-defined quantity and price
buy_custom_button = tk.Button(root, text="BUY (Custom)", command=lambda: buy_btc(float(buy_quantity_entry.get()), float(buy_price_entry.get()), error_textbox), font=('Arial', 10),bg="green")
buy_custom_button.grid(row=8, column=0,columnspan=1, padx=1, pady=1, sticky="w")


sell_quantity_entry = tk.Entry(root, width=10)
sell_quantity_entry.grid(row=9, column=1, padx=1, pady=1)
sell_quantity_entry.insert(0, "Sell Quantity")

sell_price_entry = tk.Entry(root, width=10)
sell_price_entry.grid(row=9, column=2, padx=1, pady=1)
sell_price_entry.insert(0, "Sell Price")


sell_custom_button = tk.Button(root, text="SELL (Custom)", command=lambda: sell_btc(float(sell_quantity_entry.get()), float(sell_price_entry.get()), error_textbox), font=('Arial', 10),bg="red")
sell_custom_button.grid(row=9, column=0,columnspan=1, padx=1, pady=1, sticky="w")


#percencentoco = 0.25
oco_sell_button = tk.Button(root, text="OCO_BUYCoverSellOrder", command=lambda: place_oco_order("BuyCoverSellOrder",error_textbox), font=('Arial', 10),bg="green")
oco_sell_button.grid(row=7, column=0, padx=10, pady=10)

#percencentoco = 0.25
oco_buy_button = tk.Button(root, text="OCO_SELLCoverBuyOrder", command=lambda: place_oco_order("SellCoverBuyOrder",error_textbox), font=('Arial', 10),bg="red")
oco_buy_button.grid(row=7, column=1,columnspan=3, padx=10, pady=10) #oco_buy_button.pack(side="right", padx=10, pady=10)


# Call the update_btc_price function to start updating the BTCUSDT price every 5 seconds
update_btc_price(error_textbox)

# Start Tkinter main loop
root.mainloop()

'''
while True:
    order = client.get_order(symbol=tradingpair, orderId=order_id)
    if order['status'] == 'FILLED':
        print("Order Filled!")
        print("Filled Percent:", 1)
        print("Bought", order['executedQty'], tradingpair)
        break
    else:
        print("Order not yet filled. Checking again in 5 seconds...")
        time.sleep(5)
'''