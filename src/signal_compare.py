import pandas as pd
import numpy as np


def signal_compare(
    df: pd.DataFrame,
    column0: str,
    column1: str,
) -> pd.DataFrame:
    """
    Compare signals in a DataFrame using a specified strategy.

    This function generates buy and hold signals based on the comparison
    of two specified columns in the DataFrame against each other. It
    initializes a signal column and calculates positions based on the difference
    between consecutive signals.

    It performs a comparison between the first and second columns and generates
    a buy signals if the first column is greater than the second column and a
    sell signal if the first column is less than the second column and a hold
    signal otherwise.

    An example usage might be to generate buy and hold signals based on a
    moving average strategy using the 'WMA' column in the DataFrame and a candle
    column like 'ha_ask_open', generated from the Heiken-Ashi method.

    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame containing the data for signal comparison.
    column0 : str, optional
        The first column to compare.
    column1 : str, optional
        The second column to compare.

    Returns
    -------
    pd.DataFrame
        The DataFrame with added 'signal' and 'position' columns indicating
        the generated signals and positions based on the strategy.

    Raises
    ------
    ValueError
        If the DataFrame is empty.
    ValueError
        If the first column is not found in the DataFrame.
    ValueError
        If the second column is not found in the DataFrame.
    """

    # validate assumptions
    if df.empty:
        raise ValueError("DataFrame cannot be empty")
    if column0 not in df.columns:
        raise ValueError("First column not found in DataFrame")
    if column1 not in df.columns:
        raise ValueError("Second column not found in DataFrame")

    # initialize the signal column
    df["signal"] = 0

    # if column0 is greater than column1, it indicates a buy signal
    df["signal"] = np.where(df[column0] > df[column1], 1, 0)

    # set the first signal to 0 to indicate no action
    df.loc[0, "position"] = 0

    # calculate the position based on the difference between consecutive signals
    # this generates the hold and exit signal
    df["position"] = df["signal"].diff()

    return df


signal_compare
