# Binance_Spot_Trading
Simple code for Binance Spot Trading with GUI. Stop loss ,Take Profit ,Buy Sell Commands added .Trailing Stop etc
Simply run main.py file . GUI will open and display the current price of the tradingpair 
Feed your API and Key in the credentials.py file
In main.py percencent1 = 0.02 percencent2 = 1  percencents2 = 1 percencents1 = 0.02  shall be changed to set the desired buy or sell percentage for the trading
![image](https://github.com/programjio/Binance_Spot_Trading/assets/56245199/8847a34e-23a5-4f61-88f9-c85b99f066d9)
In the GUI set the desired TakeProfit Percentage ,Stop Loss percentage and ticket the box 
Also Check the Market order or Limit Order Box 
Examples :
To Sell 100% of available BTCTUSD Click SELL_BTCTUSD_100% button ,To Sell 2% click the SELL_BTCTUSD_2% button this will place BTCTUSD sell order
Now if you want to cover the previously placed sell order clock BUY_BTCTUSD_2.0% button to cover 2% or to cover 100% click the BUY_BTCTUSD_100% button
OCO Order button included , Example After you place SELL_BTCTUSD_2% Short Order (converting BTC to TUSD) --> Now you wish to put BUY order with 1% Take Profit and 0.5% stop loss 
In this case first set the Take Profit ,Stop Loss % in the GIU and the tick the Box 
For placing the SELL_BTCTUSD to cover OCO order click the OCOSEllCoverBuyOrder ( This means you have done Short earlier using SELL_BTCTUSD_ button for that OCO coveroder is placed.Note here order will be placed for 100% available quantity.
For placing OCO order for the previously did BUY order click the button OCOBUYCoverSellOrder
To Cancell All open Orders Click the Cancel All Open Orders Button
To Restrat the program click the Restart Button
## How to Trade using this code Refer this chart https://www.tradingview.com/script/jU78tzAr-LongBuyLongSellIndicator/
### This Chart Indicator has built in SL ,Take Profit lines ,Adjust the proper SL and TP values and perform the backtest using https://www.tradingview.com/script/0zX3PYZi-LongBuyLongSell-90-profit-Excellent-Win-Rate-Strategy-indicator/
Once the proper Stop loss and Take profit is identified set that value in GUI (*Examples Below *)
Now place the SEll order for the desired quanity once the SELL order is executed ,Simultaneouly add the OCO order this will place the Stoploss and take profit order.
Refer the below screenshots on how the Risk Reward ratio is maintined by the OCO orders .

Refer the below charts on how to set the Stoploss and Takeprofit in this case 0.10% as Stoploss and 0.23% as take profit is set
![image](https://github.com/programjio/Binance_Spot_Trading/assets/56245199/f5565fe4-f598-48ca-9bc1-be3ddaa610b0)
Risk Reward is 1:2 the same is set in the GUI.
![image](https://github.com/programjio/Binance_Spot_Trading/assets/56245199/d937fa7f-e5b0-4c42-bbc6-1af7b84ed9bb)
Now to place the SELL order Either click 100% or 2% button
![image](https://github.com/programjio/Binance_Spot_Trading/assets/56245199/d2960ef2-815d-4438-8077-5e9fdc7517ab)

Once the order is placed just to cover the Short order Manually use the BUY Buttons
![image](https://github.com/programjio/Binance_Spot_Trading/assets/56245199/7860ca99-bd69-40e1-8fd0-3f51fed1348d)

The above will not place stoploss or take profit order
To place the Take profit or stop loss follow this button (note here 100% quantity order will be placed)
![image](https://github.com/programjio/Binance_Spot_Trading/assets/56245199/eacaaae5-c404-4687-834c-2070e4d8dfd4)

To Know the recently placed 5 order details click this button
![image](https://github.com/programjio/Binance_Spot_Trading/assets/56245199/a45d33fc-4772-4a38-9876-fedac43c36f5)

