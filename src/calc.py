import pandas as pd  # noqa: D100
import numpy as np


def exit_total(df: pd.DataFrame) -> None:
    """Calculate the cumulative total of all trades and the running total of the portfolio.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.

    Returns
    -------
    pd.Dataframe
        The DataFrame with the 'exit_total' and 'running_total' columns added.

    Notes
    -----
    The 'exit_total' column is the cumulative total of all trades, and the 'running_total' column
    is the cumulative total of the portfolio, including the current trade.

    """
    df["exit_value"] = df["position_value"] * np.where(df["trigger"] == -1, 1, 0)
    df["exit_total"] = df["exit_value"].cumsum()
    df["running_total"] = df["exit_total"] + (df["position_value"] * df["signal"])


def take_profit(df: pd.DataFrame, take_profit: float, optimistic: bool) -> None:
    """Apply a take profit strategy to the trading data.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    take_profit : float
        The take profit value as a multiplier of the atr.
    optimistic : bool
        Whether to use the ask_open or ask_high as the entry price.

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
    df.loc[(df["position_value"] > (df["atr"] * take_profit)), "signal"] = 0
    df["trigger"] = df["signal"].diff().fillna(0).astype(int)
    entry_price(df, optimistic)


def entry_price(df: pd.DataFrame, optimistic: bool) -> None:
    """Calculate the entry price for a given trading signal.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    optimistic : bool
        Whether to use the ask_open or ask_high as the entry price.

    Returns
    -------
    pd.Dataframe
        The DataFrame with the 'internal_bit_mask', 'entry_price', and 'position_value' columns updated.

    Notes
    -----
    The 'internal_bit_mask' column is set to the bit-wise OR of the 'signal' and 'trigger'
    columns. The 'entry_price' column is set to the 'ask_high' column when the 'trigger'
    column is 1, and the 'value' column is set to the difference between the 'bid_open'
    and 'entry_price' columns times the 'internal_bit_mask' column.

    """
    open_field = "ask_open" if optimistic else "ask_high"
    df["internal_bit_mask"] = df["signal"] | abs(df["trigger"])
    df["entry_price"] = np.where(df["trigger"] == 1, df[open_field], np.nan)
    df["entry_price"] = df["entry_price"].ffill() * df["internal_bit_mask"]
    df["position_value"] = (df["bid_open"] - df["entry_price"]) * df[
        "internal_bit_mask"
    ]
