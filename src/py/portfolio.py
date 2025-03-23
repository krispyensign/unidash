import pandas as pd


def portfolio(data: pd.DataFrame, capital0: int = 10000) -> pd.DataFrame:
    """
    Calculate the portfolio value based on a DataFrame of OHLC data.

    Args:
        data (pd.DataFrame): A DataFrame containing OHLC data.
    """

    # given a data frame with a signal that is 1 for buy and 0 for sell an a
    # position of 1 for buy, -1 for sell and 0 for no action
    # calculate the portfolio value

    pf = pd.DataFrame()

    pf["timestamp"] = data.index
    pf["close"] = data["close"]
    pf["position"] = data["position"]
    pf["portfolio"] = (data["position"] * data["close"]).cumsum() - capital0
    pf["timestamp"] = data["timestamp"]
    pf.set_index("timestamp", inplace=True)

    return pf


portfolio
