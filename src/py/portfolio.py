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

    # if position is 1 then it is a buy signal, if its a buy signal then
    # use the ask_close price
    # if the position is -1 then it is a sell signal, if its a sell signal then
    # use the bid_close price
    portfolio["buy signals"] = abs(data["position"].where(data["position"] == 1, 0))
    portfolio["sell signals"] = abs(data["position"].where(data["position"] == -1, 0))
    portfolio["num buy signals"] = portfolio["buy signals"].cumsum()
    portfolio["num sell signals"] = portfolio["sell signals"].cumsum()
    portfolio["buy spend"] = (portfolio["buy signals"] * data["ask_close"]).cumsum()
    portfolio["sell spend"] = (portfolio["sell signals"] * data["bid_close"]).cumsum()

    portfolio["quote net asset"] = portfolio["sell spend"] - portfolio["buy spend"]
    portfolio["base net asset"] = portfolio["quote net asset"] / data["bid_close"]
    portfolio["bid_close"] = data["bid_close"]
    portfolio["ask_close"] = data["ask_close"]

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
