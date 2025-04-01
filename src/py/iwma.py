import pandas as pd
import numpy as np


def iwma(df: pd.DataFrame, period: int = 20, column: str = "ha_open") -> pd.DataFrame:
    """
    Calculate the inverted weighted moving average (WMA) of a column of a given DataFrame.
    The inverted weighted moving average is calculated by reversing the order of the weights
    and applying the WMA.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the input column to which the WMA will be applied.
    period : int, optional
        The period in days. The default is 20.
    point : str, optional
        The column to which the IWMA will be applied. The default is 'ha_open'.

    Returns
    -------
    pd.Dataframe
        The DataFrame with the 'IWMA' column added.

    Raises
    ------
    ValueError
        If wma_period is not greater than 0.
    ValueError
        If df is empty.
    ValueError
        If df does not contain the provided column.
    """

    if period <= 0:
        raise ValueError("wma_period must be greater than 0")
    if df.empty:
        raise ValueError("df cannot be empty")
    if df.get(column, None) is None:
        raise ValueError(f"df must contain the provided column {column}")

    df["IWMA"] = df.rolling(f"{period}D")[column].apply(
        lambda x: np.average(x, weights=np.arange(1, len(x) + 1))
    )

    return df


iwma
