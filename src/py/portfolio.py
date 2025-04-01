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
    # initial_price = portfolio["bid_close"].iloc[0]
    initial_price = 0
    
    portfolio["current_signal"] = portfolio["position"].cumsum()
    portfolio["buy_signals"] = abs(portfolio["position"].where(portfolio["position"] == 1, 0))
    portfolio["sell_signals"] = abs(portfolio["position"].where(portfolio["position"] == -1, 0))
    portfolio["num_buy_signals"] = portfolio["buy_signals"].cumsum()
    portfolio["num_sell_signals"] = portfolio["sell_signals"].cumsum()

    # if position is 1 then it is a buy signal, if its a buy signal then
    # use the ask_close price
    # calculate the buy spend
    portfolio["buy_spend"] = (portfolio["buy_signals"] * portfolio["ask_close"]).cumsum()

    # if the position is -1 then it is a sell signal, if its a sell signal then
    # use the bid_close price
    # calculate the sell spend
    portfolio["sell_spend"] = (portfolio["sell_signals"] * portfolio["bid_close"]).cumsum()
    portfolio["holdings"] = portfolio["current_signal"] * portfolio["bid_close"]

    portfolio["quote_net_asset"] = portfolio["holdings"] + initial_price + portfolio["sell_spend"] - portfolio["buy_spend"]
    portfolio["base_net_asset"] = portfolio["quote_net_asset"] / portfolio["bid_close"]
    # portfolio["roi"] = (portfolio["quote_net_asset"] - initial_price) / initial_price

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
