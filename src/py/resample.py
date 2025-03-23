import pandas
from dataclasses import dataclass
import numpy as np


def resample(
    dataIn: pandas.DataFrame, timeFrame: str, token0IsBase: bool
) -> pandas.DataFrame:
    """
    Resamples a given DataFrame to a given time frame and sets a new column 'price' using 'amount0' and 'amount1'.

    Args:
        df (pandas.DataFrame): The DataFrame to be resampled.
        timeFrame (str): The time frame to resample to.
        token0IsBase (bool): If true, token0 is the base token. If false, token1 is the base token.

    Returns:
        pandas.DataFrame: The resampled DataFrame with a new column 'price'.
    """
    df = dataIn.copy()

    if token0IsBase:
        df["price"] = abs(df["amount1"] / df["amount0"])
    else:
        df["price"] = abs(df["amount0"] / df["amount1"])

    del df["amount0"]
    del df["amount1"]

    # resample to 5 minute intervals
    df = df["price"].resample(timeFrame).ohlc()
    df.fillna(method="ffill", inplace=True)

    return df


resample
