import pandas as pd
import numpy as np


def wma(df: pd.DataFrame, wma_period: int = 20, point: str = "ha_bid_close", reverse=False) -> pd.DataFrame:
    """
    Calculate the weighted moving average (WMA) of the Heikin Ashi 'ha_close' column
    of a given DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the 'ha_close' column to which the WMA will be applied.
    wma_period : int, optional
        The period of the WMA. The default is 20.

    Returns
    -------
    pd.Dataframe
        The DataFrame with the 'WMA' column added.

    Raises
    ------
    ValueError
        If wma_period is not greater than 0.
    ValueError
        If ha_df is empty.
    ValueError
        If ha_df does not contain the provided column.
    """

    if wma_period <= 0:
        raise ValueError("wma_period must be greater than 0")
    if df.empty:
        raise ValueError("ha_df cannot be empty")
    if df.get(point, None) is None:
        raise ValueError(f"ha_df must contain the provided column {point}")


    if not reverse:
        df["WMA"] = df.rolling(f"{wma_period}D", on="timestamp")[point].apply(lambda x: np.average(x, weights=np.arange(len(x), 0, -1)))   
    else:
        df["WMA"] = df.rolling(f"{wma_period}D", on="timestamp")[point].apply(lambda x: np.average(x, weights=np.arange(1, len(x) + 1)))   


    return df


wma
