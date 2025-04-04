import pandas as pd


def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate Heikin Ashi candlesticks for a given dataframe.

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


heikin_ashi
