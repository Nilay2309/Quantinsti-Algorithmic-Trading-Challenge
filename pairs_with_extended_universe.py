  
"""
    Title: Pairs Trading Startegy
    Description: This is a sample Pairs Trading strategy
    Style tags: Mean-reversion, Stat-Arb
    Asset class: Equities, Futures, ETFs, Currencies and Commodities
    Dataset: NYSE Minute
"""
import numpy as np
from blueshift_library.utils.utils import z_score, hedge_ratio, cancel_all_open_orders


# Zipline
from zipline.api import(    symbol,
                            order_target_percent,
                            schedule_function,
                            date_rules,
                            time_rules,
                            set_commission,
                            set_slippage,
                       )
from zipline.api import get_datetime
from zipline.finance import commission, slippage

def initialize(context):
    """
        function to define things to do at the start of the strategy
    """
    context.universe = [symbol('JPM'), symbol('GS'), symbol('PEP'), symbol('KO')]
    context.leverage = 2.0
    context.signal = 0
    context.last_signal = 0
    context.prev_zscore = [0.0, 0.0]

    # Trade entry and exit when the z_score is +/- entry_z_score and exit_z_score respectively
    context.entry_z_score = 1.5
    context.exit_z_score = 0.5

    # Lookback window
    context.lookback = 200

    # used for zscore calculation
    context.z_window = 100

    # Call strategy function on the first trading day of each week at 10 AM
    #schedule_function(pair_trading_strategy,
                    # date_rules.every_day(),
     #                time_rules.every_minute())
    context.trade_freq = 1
    context.bar_count = 0

    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    set_slippage(slippage.FixedSlippage(0.00))

def handle_data(context, data):
    """
        A function to define things to do at every bar
    """
    context.bar_count = context.bar_count + 1
    if context.bar_count < context.trade_freq:
        return

    # time to trade, call the strategy function
    context.bar_count = 0
    pair_trading_strategy(context, data)

def pair_trading_strategy(context,data):
    """
        function to define Pairs Trading strategy logic.
    """

    try:
        # Get the historic data for the stocks pair
        prices = data.history(  assets = context.universe,
                                fields = "price",
                                bar_count = context.lookback,
                                frequency = "1m"
                             )
    except:
        return

    # Take log of the prices
    prices = np.log(prices)

    # Store the price data in y and x
    
    for i in range(0, len(context.universe), 2):


        y = prices[context.universe[i+1]]
        x = prices[context.universe[i]]

    # Calculate the hedge ratio and z_score
        _, context.hedge_ratio, resids = hedge_ratio(y, x)
        zscore = z_score(resids, lookback=context.z_window)
    # Compute the trading signal
        context.signal = trading_signal(context, data, zscore, i/2)
        print(zscore, context.signal, " {}" .format(get_datetime()))

    # Place the order to trade the pair
    #place_order(context)
        if context.signal == 999:
            continue

        weight = context.signal*context.leverage/len(context.universe)
        print (weight)

        cancel_all_open_orders(context)

        order_target_percent(context.universe[i], -1*weight)
        order_target_percent(context.universe[i+1], weight)

        


def trading_signal(context, data, zscore, i):
    """
        determine the trade based on current z-score.
    """
    #print (context.z_score[0], context.z_score[1], " {}" .format(get_datetime()) )

    if zscore > 2.5  and zscore < context.prev_zscore[i]:
        context.prev_zscore[i] = zscore
        return -1
    elif zscore < -2.5  and zscore > context.prev_zscore[i]:
        context.prev_zscore[i] = zscore
        return 1
    #elif z_score > 2.0:
     #   return -1
    #elif z_score < -2.0:
     #   return 1
    elif zscore < 0.5 and zscore > -0.5:
        context.prev_zscore[i] = zscore
        return 0
    #elif context.z_score > -0.5 and context.z_score < 0:
     #   return 0
    context.prev_zscore[i] = zscore
    return 999
    

def place_order(context):
    """
        A function to place order.
    """
    """
    if context.signal == 0.75 and context.last_signal == 1:
        context.signal = 1

    if context.signal == -0.75 and context.last_signal == -1:
        context.signal = -1
    """
    #print (context.signal)

    # no change in positioning
    
    for i in range(len(context.signal)):


        if context.signal[i] == 999:
            return

    #context.last_signal = context.signal
    
    
        

        weight = context.signal[i]*context.leverage/(2*len(context.signal))

    # cancel all outstanding orders
        cancel_all_open_orders(context)
    # send fresh orders
        order_target_percent(context.universe[2*i], -1*weight)
        order_target_percent(context.universe[2*i+1], weight)