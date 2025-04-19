"""Functions for processing and generating trading signals."""

from dataclasses import dataclass
import numpy as np
import talib
import pandas as pd

from core.chart import heikin_ashi
from core.calc import entry_price, exit_total, take_profit, atr, trailing_stop_loss

ENTRY_COLUMN = "ask_close"
EXIT_COLUMN = "bid_close"


@dataclass
class KernelConfig:
    """A dataclass containing the configuration for the kernel."""

    wma_period: int
    signal_buy_column: str = ""
    signal_exit_column: str = ""
    source_column: str = ""
    take_profit: float = 0
    stop_loss: float = 0

    def __str__(self):
        """Return a string representation of the SignalConfig object."""
        return f"so:{self.source_column}, sib:{self.signal_buy_column}, sie:{self.signal_exit_column}, sl:{self.stop_loss}, tp:{self.take_profit}"


def wma_signals(
    df: pd.DataFrame,
    source_column: str = "open",
    signal_buy_column: str = "bid_low",
    signal_exit_column: str = "bid_high",
    wma_period: int = 20,
) -> None:
    """Generate trading signals based on a comparison of the Heikin-Ashi highs and lows to the wma.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    first_time_frame_run : bool, optional
        Whether this is the first time frame run.
    source_column : str, optional
        The column name for the source data.
    signal_buy_column : str, optional
        The column name for the buy signal data.
    signal_exit_column : str, optional
        The column name for the exit signal data.
    wma_period : int, optional
        The period for the weighted moving average, by default 20

    Returns
    -------
    pd.Dataframe
        The DataFrame with the 'signal' column added.

    Notes
    -----
    The 'signal' column is added to the DataFrame and is set to 1 where the Heikin-Ashi high
    is greater than the wma, and 0 where the Heikin-Ashi low is less than the wma.

    """
    df["signal"] = 0
    df["wma"] = talib.WMA(df[source_column].to_numpy(), wma_period)

    # check if the buy column is greater than the wma
    # B > W  S < W  Result
    # T      T      X
    # T      F      Buy
    # F      T      Exit
    # F      F      X

    # check if the buy column is greater than the wma
    df.loc[df[signal_buy_column] > df["wma"], "signal"] = 1

    if signal_buy_column != signal_exit_column:
        # check if the exit column is less than the wma
        df.loc[df[signal_exit_column] < df["wma"], "signal"] = 0


def kernel(
    df: pd.DataFrame,
    config: KernelConfig,
) -> pd.DataFrame:
    """Process a DataFrame containing trading data.

    This function processes a DataFrame containing trading data and generate trading signals
    using candlesticks and weighted moving average (wma).

    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame containing trading data.
    include_incomplete:
        Whether to include the last candle in the output DataFrame.
    config : KernelConfig
        A dataclass containing the configuration for the kernel.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the processed trading data.

    """
    df = df.copy().iloc[:-1]

    # calculate the ATR for the trailing stop loss
    heikin_ashi(df)
    atr(df, config.wma_period)

    # signal using the close prices
    # signal and trigger interval could appears as this:
    # 0 0 1 1 1 0 0 - 1 above or 0 below the wma
    # 0 0 1 0 0 -1 0 - diff gives actual trigger
    # NOTE: usage of close prices differs online than in offline trading
    wma_signals(
        df,
        signal_buy_column=config.signal_buy_column,
        signal_exit_column=config.signal_exit_column,
        wma_period=config.wma_period,
        source_column=config.source_column,
    )

    # calculate the entry prices:
    df["trigger"], df["entry_price"], df["position_value"] = entry_price(
        df["signal"].to_numpy(dtype=np.int8),
        df[ENTRY_COLUMN].to_numpy(),
        df[EXIT_COLUMN].to_numpy(),
    )

    # recalculate the entry prices after a take profit
    # for internally managed take profits
    if config.take_profit > 0:
        take_profit(
            df,
            config.take_profit,
            entry_column=ENTRY_COLUMN,
            exit_column=EXIT_COLUMN,
        )

    if config.stop_loss > 0:
        trailing_stop_loss(
            df,
            config.stop_loss,
            entry_column=ENTRY_COLUMN,
            exit_column=EXIT_COLUMN,
        )

    # calculate the exit total
    ev, et, running_total, wins, losses, min_exit_total = exit_total(
        df["position_value"].to_numpy(),
        df["trigger"].to_numpy(),
        df["signal"].to_numpy(),
    )
    df["exit_value"] = ev
    df["exit_total"] = et
    df["running_total"] = running_total
    df["wins"] = wins
    df["losses"] = losses
    df["min_exit_total"] = min_exit_total

    return df
