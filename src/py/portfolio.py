import pandas as pd


def portfolio(data: pd.DataFrame, capital0: int = 10000, positions: int = 100):
    # cumsum column is created to check the holding of the position
    """
    Creates a portfolio given a DataFrame of prices and trading signals.

    Args:
        data (pd.DataFrame): DataFrame of prices with a "signal" column
            containing -1 or 1 indicating a short or long position.
        capital0 (int): Initial capital to start with. Defaults to 10,000.
        positions (int): The number of shares to buy or sell at each position.
            Defaults to 100.

    Returns:
        pd.DataFrame: A DataFrame with the portfolio's value over time,
            including columns for holdings, cash, total assets, and returns.
    """
    data["cumsum"] = data["signal"].cumsum()

    portfolio = pd.DataFrame()
    portfolio["holdings"] = data["cumsum"] * data["close"] * positions
    portfolio["cash"] = capital0 - (data["signal"] * data["close"] * positions).cumsum()
    portfolio["total asset"] = portfolio["holdings"] + portfolio["cash"]
    portfolio["return"] = portfolio["total asset"].pct_change()
    portfolio["signal"] = data["signal"]
    portfolio["timestamp"] = data["timestamp"]
    portfolio.set_index("date", inplace=True)

    return portfolio


portfolio
