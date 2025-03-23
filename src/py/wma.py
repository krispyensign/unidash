import pandas as pd
import numpy as np


def wma(df: pd.DataFrame, wma_period: int = 20) -> pd.DataFrame:
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
        If ha_df does not contain a 'ha_close' column.
    """

    if wma_period <= 0:
        raise ValueError("wma_period must be greater than 0")
    if df.empty:
        raise ValueError("ha_df cannot be empty")
    if df.get("ha_close", None) is None:
        raise ValueError("ha_df must contain a 'ha_close' column")

    kernel = np.arange(wma_period, 0, -1)
    kernel = np.concatenate([np.zeros(wma_period - 1), kernel / kernel.sum()])
    df["WMA"] = np.convolve(df["ha_close"], kernel, "same")
    df.fillna(method="ffill", inplace=True)

    return df


wma
