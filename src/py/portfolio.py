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

    portfolio = pd.DataFrame()

    portfolio["timestamp"] = data["timestamp"]
    portfolio["position"] = data["position"]

    portfolio["bid_close"] = data["bid_close"]
    portfolio["ask_close"] = data["ask_close"]

    portfolio = portfolio[(portfolio["ask_close"] > 0) & (portfolio["bid_close"] > 0)]
    initial_amount = portfolio["bid_close"].iloc[0]

    # if position is 1 then it is a buy signal, if its a buy signal then
    # use the ask_close price
    # calculate the buy spend
    portfolio["buy signals"] = abs(portfolio["position"].where(portfolio["position"] == 1, 0))
    portfolio["num buy signals"] = portfolio["buy signals"].cumsum()
    portfolio["buy spend"] = (portfolio["buy signals"] * portfolio["ask_close"]).cumsum()

    # if the position is -1 then it is a sell signal, if its a sell signal then
    # use the bid_close price
    # calculate the sell spend
    portfolio["sell signals"] = abs(portfolio["position"].where(portfolio["position"] == -1, 0))
    portfolio["num sell signals"] = portfolio["sell signals"].cumsum()
    portfolio["sell spend"] = (portfolio["sell signals"] * portfolio["bid_close"]).cumsum()
    portfolio["holdings"] = portfolio["position"].cumsum() * data["bid_close"]

    portfolio["quote net asset"] = portfolio["holdings"] + initial_amount + portfolio["sell spend"] - portfolio["buy spend"]
    portfolio["base net asset"] = portfolio["quote net asset"] / portfolio["bid_close"]
    portfolio["roi"] = (portfolio["quote net asset"] - initial_amount) / initial_amount

    # check if the net asset is less than 0 this would mean that we have a loss
    # and that this is a bad signal
    result = any(np.where(portfolio["quote net asset"] < 0, False, True))

    portfolio.set_index("timestamp", inplace=True)

    return (
        portfolio,
        result,
        portfolio["quote net asset"].iloc[-1],
        portfolio["base net asset"].iloc[-1],
    )


portfolio
