import pandas as pd
import numpy as np


def signal(ha_df: pd.DataFrame, wma_period: int = 20, inverted: bool = False, point: str = "ha_ask_open") -> pd.DataFrame:
    # Generate signals
    """
    Generate trading signals based on Heikin-Ashi candlesticks and a Weighted Moving Average (WMA).

    This function calculates buy and sell signals by comparing the closing prices of Heikin-Ashi
    candlesticks to the WMA. A signal of 1 indicates a buy signal. The position is determined by
    the difference between consecutive signals, where a position of 1 indicates a buy signal and
    -1 indicates a sell signal, and 0 indicates no action.

    The midpoint of the Heikin-Ashi candlestick is used for the WMA calculation.

    Parameters
    ----------
    ha_df : pd.DataFrame
        A DataFrame containing Heikin-Ashi candlesticks with columns 'ha_open', 'ha_high', 'ha_low', 'ha_close',
        and 'WMA'.
    wma_period : int, optional
        The period to use for the WMA calculation. Defaults to 20.

    Returns
    -------
    pd.DataFrame
        The updated DataFrame with 'signal' and 'position' columns.
    """
    # validate assumptions
    if wma_period <= 0:
        raise ValueError("wma_period must be greater than 0")
    if ha_df.empty:
        raise ValueError("ha_df cannot be empty")
    if "WMA" not in ha_df.columns:
        raise ValueError("ha_df must contain a 'WMA' column")

    # initialize the signal column
    ha_df["signal"] = 0

    # if the close price is greater than the WMA, it indicates a buy signal
    if inverted:
        ha_df["signal"][wma_period:] = np.where(
            ha_df[point][wma_period:] < ha_df["WMA"][wma_period:], 1, 0 
        )
    else:
        ha_df["signal"][wma_period:] = np.where(
            ha_df[point][wma_period:] > ha_df["WMA"][wma_period:], 1, 0
        )

    # set the first signal to 0 to indicate no action
    ha_df.loc[0, "position"] = 0

    # calculate the position based on the difference between consecutive signals
    # this generates the hold and exit signal
    ha_df["position"] = ha_df["signal"].diff()

    return ha_df


signal
