import pandas


def ohlc(dataIn: pandas.DataFrame, timeFrame: str = "5Min") -> pandas.DataFrame:
    """
    Resample the input DataFrame into OHLC format for specified time intervals.

    This function takes a DataFrame containing raw trading data, calculates the
    price, bid price, and ask price based on the amounts, and then resamples
    these prices into Open-High-Low-Close (OHLC) format for the specified time
    intervals. The function handles both buy and sell scenarios to compute
    bid and ask prices.

    Parameters
    ----------
    dataIn : pandas.DataFrame
        A DataFrame with columns 'amount0' and 'amount1' representing trading data.
    timeFrame : str, optional
        The time interval for resampling, by default '5Min'.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing resampled OHLC data for price, bid price, and ask price.
    """

    df = dataIn.copy()

    df["price"] = abs(df["amount1"] / df["amount0"])

    # if amount 0 is negative and amount 1 is positive, then it is a sell and
    # then we can calculate the bid price
    df["bid_price"] = abs(df["amount1"] / df["amount0"]).where(df["amount0"] < 0)

    # if amount 0 is positive and amount 1 is negative, then it is a buy and
    # then we can calculate the ask price
    df["ask_price"] = abs(df["amount1"] / df["amount0"]).where(df["amount0"] > 0)

    del df["amount0"]
    del df["amount1"]

    # resample to 5 minute intervals
    df_p = df["price"].resample(timeFrame).ohlc()
    df_p.ffill(inplace=True)

    df_b = df["bid_price"].resample(timeFrame).ohlc()
    df_b.ffill(inplace=True)

    df_a = df["ask_price"].resample(timeFrame).ohlc()
    df_a.ffill(inplace=True)

    df_ohlc = pandas.DataFrame()

    df_ohlc["open"] = df_p["open"]
    df_ohlc["high"] = df_p["high"]
    df_ohlc["low"] = df_p["low"]
    df_ohlc["close"] = df_p["close"]

    df_ohlc["bid_open"] = df_b["open"]
    df_ohlc["bid_high"] = df_b["high"]
    df_ohlc["bid_low"] = df_b["low"]
    df_ohlc["bid_close"] = df_b["close"]

    df_ohlc["ask_open"] = df_a["open"]
    df_ohlc["ask_high"] = df_a["high"]
    df_ohlc["ask_low"] = df_a["low"]
    df_ohlc["ask_close"] = df_a["close"]

    return df_ohlc


ohlc
