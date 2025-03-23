import pandas as pd


def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate Heikin-Ashi candlesticks from a given DataFrame of OHLC prices.

    The Heikin-Ashi candlestick is a modified candlestick chart that is used to
    filter out the noise in the price movement and provide a clearer view of the
    price trend. The calculation method is as follows:

    - ha_close: average of open, high, low, and close prices
    - ha_open: average of the previous period's open and close prices
    - ha_high: maximum of high, open, and close prices
    - ha_low: minimum of low, open, and close prices

    The returned DataFrame has four additional columns: ha_open, ha_high, ha_low,
    and ha_close.

    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame with columns 'open', 'high', 'low', and 'close'

    Returns
    -------
    pd.DataFrame
        A DataFrame with the additional columns 'ha_open', 'ha_high', 'ha_low',
        and 'ha_close'
    """

    df.reset_index(inplace=True)
    df["ha_close"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
    df["ha_open"] = (df["open"].shift(1) + df["close"].shift(1)) / 2
    df["ha_high"] = df[["high", "open", "close"]].max(axis=1)
    df["ha_low"] = df[["low", "open", "close"]].min(axis=1)
    df.fillna(method="ffill", inplace=True)

    return df


heikin_ashi
