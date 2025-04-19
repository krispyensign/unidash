"""Functions for calculating trading signals."""

from typing import Any
import pandas as pd
import numpy as np
from numpy.typing import NDArray
import talib
from numba import jit  # type: ignore


@jit(nopython=True)
def exit_total(
    position_value: NDArray[np.float64],
    trigger: NDArray[np.uint8],
    signal: NDArray[np.uint8],
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.uint8],
    NDArray[np.uint8],
    NDArray[np.float64],
]:
    """Calculate the cumulative total of all trades and the running total of the portfolio.

    Parameters
    ----------
    position_value : NDArray[np.float64]
        The position value array.
    trigger : NDArray[np.uint8]
        The trigger array.
    signal : NDArray[np.uint8]
        The signal array.

    Returns
    -------
    tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.uint8], NDArray[np.uint8], NDArray[np.float64]]
        The exit value, exit total, running total, wins, losses, and min exit total.

    Notes
    -----
    The 'exit_total' column is the cumulative total of all trades, and the 'running_total' column
    is the cumulative total of the portfolio, including the current trade.

    """
    exit_value: NDArray[np.float64] = position_value * (np.where(trigger == -1, 1, 0))
    exit_total: NDArray[np.float64] = exit_value.cumsum()
    running_total: NDArray[np.float64] = exit_total + (position_value * signal)
    wins: NDArray[np.uint8] = np.where(exit_value > 0, 1, 0).cumsum()
    losses: NDArray[np.uint8] = np.where(exit_value < 0, 1, 0).cumsum()
    min_exit_total = exit_total.min()

    return exit_value, exit_total, running_total, wins, losses, min_exit_total


def take_profit(
    df: pd.DataFrame, take_profit: float, entry_column: str, exit_column: str
) -> None:
    """Apply a take profit strategy to the trading data.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    take_profit : float
        The take profit value as a multiplier of the atr.
    entry_column : str
        The column name for the entry price.
    exit_column : str
        The column name for the exit price.

    Returns
    -------
    pd.Dataframe
        The DataFrame with the 'signal' and 'trigger' columns updated.

    Notes
    -----
    The 'signal' column is set to 0 where the 'value' column is greater than the 'atr'
    column times the take profit value. The 'trigger' column is set to the difference
    between the 'signal' and the previous value of the 'signal' column. The entry_price
    is then re-calculated.

    """
    df["take_profit"] = df["atr"] * take_profit
    df.loc[
        (df["position_value"] > df["take_profit"]) & (df["trigger"] != 1), "signal"
    ] = 0
    df["trigger"], df["entry_price"], df["position_value"] = entry_price(
        df["signal"].to_numpy(dtype=np.int8),
        df[entry_column].to_numpy(),
        df[exit_column].to_numpy(),
    )


def stop_loss(
    df: pd.DataFrame, stop_loss_value: float, entry_column: str, exit_column: str
) -> None:
    """Apply a stop loss strategy to the trading data.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    stop_loss_value : float
        The stop loss value as a multiplier of the atr.
    entry_column : str
        The column name for the entry price.
    exit_column : str
        The column name for the exit price.

    Returns
    -------
    pd.Dataframe
        The DataFrame with the 'signal' and 'trigger' columns updated.

    Notes
    -----
    The 'signal' column is set to 0 where the 'value' column is greater than the 'atr'
    column times the stop loss value. The 'trigger' column is set to the difference
    between the 'signal' and the previous value of the 'signal' column. The entry_price
    is then re-calculated.

    """
    df["stop_loss"] = df["atr"] * stop_loss_value
    df.loc[
        (df["position_value"] < df["stop_loss"]) & (df["trigger"] != 1), "signal"
    ] = 0
    df["trigger"], df["entry_price"], df["position_value"] = entry_price(
        df["signal"].to_numpy(dtype=np.int8),
        df[entry_column].to_numpy(),
        df[exit_column].to_numpy(),
    )


def trailing_stop_loss(
    df: pd.DataFrame,
    trailing_stop_loss_value: float,
    entry_column: str,
    exit_column: str,
) -> None:
    """Apply a trailing stop loss to the DataFrame.

    This function applies a trailing stop loss to the DataFrame based on the 'signal' column.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    trailing_stop_loss_value : float
        The trailing stop loss value as a multiplier of the atr.
    entry_column : str
        The column name for the entry price.
    exit_column : str
        The column name for the exit price.

    Returns
    -------
    pd.DataFrame
        The DataFrame with the 'trailing_stop_loss' column added.

    """
    # set the trailing stop loss
    df["trailing_stop_loss"] = (
        df[df["signal"] == 1]
        .groupby((df["signal"] == 1).cumsum())["bid_high"]
        .transform(lambda x: x.rolling(window=len(x)).max())
        - df["atr"] * trailing_stop_loss_value
    )

    # set the signal to 0 if the trailing stop loss is less than the bid close
    df.loc[
        (df["bid_close"] < df["trailing_stop_loss"]) & (df["trigger"] != 1),
        "signal",
    ] = 0

    df["trigger"], df["entry_price"], df["position_value"] = entry_price(
        df["signal"].to_numpy(dtype=np.int8),
        df[entry_column].to_numpy(),
        df[exit_column].to_numpy(),
    )


@jit(nopython=True)
def entry_price(
    signal: NDArray[np.int8],
    entry_column: NDArray[np.float64],
    exit_column: NDArray[np.float64],
) -> tuple[NDArray[np.int8], NDArray[np.float64], NDArray[np.float64]]:
    """Calculate the entry price for a given signal.

    Parameters
    ----------
    signal : NDArray[np.uint8]
        The signal array.
    entry_column : NDArray[np.float64]
        The entry column array.
    exit_column : NDArray[np.float64]
        The exit column array.

    Returns
    -------
    tuple[NDArray[np.uint8], NDArray[np.float64], NDArray[np.float64]]
        The trigger, entry price, and position value arrays.

    """
    trigger: NDArray[np.int8] = np.append(0, np.diff(signal))
    internal_bit_mask: NDArray[np.int8] = np.bitwise_or(signal, np.abs(trigger))
    price: NDArray[np.float64] = np.where(trigger == 1, entry_column, np.nan)
    price = ffill(price) * internal_bit_mask
    price = np.where(np.isnan(price), 0, price)
    position_value: NDArray[np.float64] = (exit_column - price) * internal_bit_mask

    return trigger, price, position_value


@jit(nopython=True)
def ffill(signal: NDArray[Any]) -> NDArray[Any]:
    """Fill missing values in a numpy array with the previous value."""
    for i in range(1, len(signal)):
        if np.isnan(signal[i]):
            for j in range(i - 1, 0, -1):
                if not np.isnan(signal[j]):
                    signal[i] = signal[j]
                    break
    return signal


def atr(df: pd.DataFrame, wma_period: int) -> None:
    """Calculate the Average True Range for a given DataFrame and add it to the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    wma_period : int
        The period for the weighted moving average.

    Returns
    -------
    pd.Dataframe
        The DataFrame with the 'atr' column added.

    Notes
    -----
    The 'atr' column is the Average True Range of the trading data, calculated using
    the TA-Lib library.

    """
    df["atr"] = talib.ATR(
        df["high"].to_numpy(),
        df["low"].to_numpy(),
        df["close"].to_numpy(),
        timeperiod=wma_period,
    )
