import pandas as pd
import numpy as np


def portfolio(data: pd.DataFrame) -> tuple[pd.DataFrame, bool, float, float]:
    """
    Calculate the portfolio value based on a DataFrame of OHLC data.

    Args:
        data (pd.DataFrame): A DataFrame containing OHLC data.

    Returns:
        tuple[pd.DataFrame, float, float]: A tuple containing the portfolio DataFrame,
        the value in terms of the quote token and the value in terms of the base token.
    """

    portfolio = data.copy()

    portfolio = portfolio[(portfolio["ask_close"] > 0) & (portfolio["bid_close"] > 0)]

    isHold = False
    firstI = 0
    portfolio["original_hold_price"] = 0
    original_hold_price = portfolio["original_hold_price"].to_numpy()
    for i in range(len(portfolio)):
        if not isHold and portfolio["signal"].iloc[i] == 1:
            isHold = True
            firstI = i
            original_hold_price[i] = portfolio["bid_close"].iloc[i]
        elif isHold and i > firstI and portfolio["signal"].iloc[i] == 1:
            original_hold_price[i] = original_hold_price[firstI]
        elif isHold and portfolio["signal"].iloc[i] == 0:
            isHold = False
    portfolio["original_hold_price"] = original_hold_price

    portfolio["original_hold_value"] = 0
    portfolio["original_hold_value"] = portfolio["bid_close"]*portfolio["signal"] - portfolio["original_hold_price"]
    portfolio["max_hold_value"] = portfolio["original_hold_value"].cummax()
        
    signal = portfolio["signal"].to_numpy()

    take_profit_amt = .5
    stop_loss_amt = -.25
    for i in range(len(portfolio)):
        if portfolio["signal"].iloc[i] == 0:
            continue
        if (portfolio["original_hold_value"].iloc[i] > take_profit_amt
            or portfolio["original_hold_value"].iloc[i] < stop_loss_amt):
            for j in range(i, len(portfolio)):
                if portfolio["signal"].iloc[j] == 1:
                    signal[j] = 0
                else:
                    break

    portfolio["signal"] = signal
    portfolio["position"] = portfolio["signal"].diff()

    # portfolio["current_signal"] = portfolio["position"].cumsum()
    portfolio["buy_signals"] = abs(portfolio["position"].where(portfolio["position"] == 1, 0))
    portfolio["sell_signals"] = abs(portfolio["position"].where(portfolio["position"] == -1, 0))
    portfolio["num_buy_signals"] = portfolio["buy_signals"].cumsum()
    portfolio["num_sell_signals"] = portfolio["sell_signals"].cumsum()

    # calculate the position based on the signal

    # if position is 1 then it is a buy signal, if its a buy signal then
    # use the ask_close price
    # calculate the buy spend
    portfolio["buy_spend"] = (portfolio["buy_signals"] * portfolio["ask_close"]).cumsum()
    # portfolio["long_credit"] = portfolio["buy_spend"] * .015

    # if the position is -1 then it is a sell signal, if its a sell signal then
    # use the bid_close price
    # calculate the sell spend
    portfolio["sell_spend"] = (portfolio["sell_signals"] * portfolio["bid_close"]).cumsum()
    portfolio["holdings"] = portfolio["signal"] * portfolio["bid_close"]

    portfolio["quote_net_asset"] = portfolio["holdings"] + portfolio["sell_spend"] \
        - portfolio["buy_spend"]
    portfolio["base_net_asset"] = portfolio["quote_net_asset"] / portfolio["bid_close"]
    portfolio["drawdown"] = (portfolio["quote_net_asset"] - portfolio["quote_net_asset"].cummax())

    # check if the net asset is less than 0 this would mean that we have a loss
    # and that this is a bad signal
    result = any(np.where(portfolio["quote_net_asset"] < 0, False, True))

    return (
        portfolio,
        result,
        portfolio["quote_net_asset"].iloc[-1],
        portfolio["base_net_asset"].iloc[-1],
    )


portfolio
