"""Functions for generating charts."""

import typing
import pandas as pd


def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """Generate Heikin Ashi candlesticks for a given dataframe.

    Heikin Ashi is a Japanese chart type that is used to identify trends and
    patterns in financial markets. It is similar to traditional candlestick charts,
    but it uses the average of the high, low, and closing prices to calculate
    the body of the candle.  This function also generates Heikin Ashi candlesticks
    for the bid and ask prices.

    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame containing OHLC data.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing Heikin Ashi candlesticks.  The candlesticks are
        added as new columns to the original DataFrame.  They are named
        'ha_close', 'ha_open', 'ha_high', and 'ha_low'. The 'ha_bid_close',
        'ha_ask_close', 'ha_bid_open', 'ha_ask_open', 'ha_bid_high', 'ha_ask_high',
        'ha_bid_low', and 'ha_ask_low' are also added.

    """
    df.reset_index(inplace=True)

    df["ha_close"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
    df["ha_bid_close"] = (
        df["bid_open"] + df["bid_high"] + df["bid_low"] + df["bid_close"]
    ) / 4
    df["ha_ask_close"] = (
        df["ask_open"] + df["ask_high"] + df["ask_low"] + df["ask_close"]
    ) / 4

    df.at[0, "ha_open"] = df.at[0, "open"]
    for i in range(1, len(df)):
        df.at[i, "ha_open"] = (df.at[i - 1, "ha_open"] + df.at[i - 1, "ha_close"]) / 2

    df.at[0, "ha_bid_open"] = df.at[0, "bid_open"]
    for i in range(1, len(df)):
        df.at[i, "ha_bid_open"] = (
            df.at[i - 1, "ha_bid_open"] + df.at[i - 1, "ha_bid_close"]
        ) / 2

    df.at[0, "ha_ask_open"] = df.at[0, "ask_open"]
    for i in range(1, len(df)):
        df.at[i, "ha_ask_open"] = (
            df.at[i - 1, "ha_ask_open"] + df.at[i - 1, "ha_ask_close"]
        ) / 2

    df["ha_high"] = df[["high", "ha_open", "ha_close"]].max(axis=1)
    df["ha_low"] = df[["low", "ha_open", "ha_close"]].min(axis=1)

    df["ha_bid_high"] = df[["bid_high", "ha_bid_open", "ha_bid_close"]].max(axis=1)
    df["ha_bid_low"] = df[["bid_low", "ha_bid_open", "ha_bid_close"]].min(axis=1)

    df["ha_ask_high"] = df[["ask_high", "ha_ask_open", "ha_ask_close"]].max(axis=1)
    df["ha_ask_low"] = df[["ask_low", "ha_ask_open", "ha_ask_close"]].min(axis=1)

    df.set_index("timestamp", inplace=True)

    return df


def ohlc(
    df: pd.DataFrame, timeFrame: str = "5Min", isSwapped: bool = False
) -> tuple[pd.DataFrame, typing.Any]:
    """Resample the input DataFrame into OHLC format for specified time intervals.

    This function takes a DataFrame containing raw trading data, calculates the
    price, bid price, and ask price based on the amounts, and then resamples
    these prices into Open-High-Low-Close (OHLC) format for the specified time
    intervals. The function handles both buy and sell scenarios to compute
    bid and ask prices.

    Parameters
    ----------
    df: pandas.DataFrame
        A DataFrame with columns 'amount0' and 'amount1' representing trading data.
    timeFrame : str, optional
        The time interval for resampling, by default '5Min'.
    isSwapped: bool, optional
        If True, swap the columns 'amount0' and 'amount1'.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing resampled OHLC data for price, bid price, and ask price.

    """
    if isSwapped:
        df.rename(columns={"amount0": "amount1", "amount1": "amount0"}, inplace=True)

    # if amount0 is negative, then it is a buy so calculate the ask price
    # i.e. buy ETH sell BOBO
    # i.e. ETH = 0.15307 BOBO = 1040599933.89 price per ETH = 6,798,196,471.483635 BOBO
    df["ask_price"] = abs(df["amount1"] / df["amount0"]).where(df["amount0"] < 0)

    # if amount0 is positive, then it is a sell so calculate the bid price
    # i.e. sell ETH buy BOBO
    # i.e. ETH = 0.19187 BOBO = 1280811348.79 price per ETH = 6,675,412,251.993537 BOBO
    df["bid_price"] = abs(df["amount1"] / df["amount0"]).where(df["amount0"] > 0)

    df.ffill(inplace=True)
    df["mid_price"] = (df["bid_price"] + df["ask_price"]) / 2

    del df["amount0"]
    del df["amount1"]

    # resample to 5 minute intervals
    df_p = df["mid_price"].resample(timeFrame).ohlc()
    df_p.ffill(inplace=True)

    df_b = df["bid_price"].resample(timeFrame).ohlc()
    df_b.ffill(inplace=True)

    df_a = df["ask_price"].resample(timeFrame).ohlc()
    df_a.ffill(inplace=True)

    df_ohlc = pd.DataFrame()

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

    df_json = df_ohlc.reset_index()

    return df_ohlc, df_json.to_json(orient="records")
