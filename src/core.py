import logging  # noqa: D100
import talib
from calc import entry_price, exit_total, take_profit, atr
from chart import heikin_ashi
import pandas as pd

logger = logging.getLogger("main.py")

Thursday = 4


def wma_signals(  # noqa: PLR0913
    df: pd.DataFrame,
    first_time_frame_run: bool = True,
    source_column: str = "ha_low",
    signal_buy_column: str = "ha_bid_low",
    signal_exit_column: str = "ha_bid_high",
    wma_period: int = 20,
) -> bool:
    """Generate trading signals based on a comparison of the Heikin-Ashi highs and lows to the wma.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    first_time_frame_run : bool, optional
        Whether this is the first time frame run.
    source_column : str, optional
        The column name for the source data, by default "ha_low".
    signal_buy_column : str, optional
        The column name for the buy signal data, by default "ha_bid_low".
    signal_exit_column : str, optional
        The column name for the exit signal data, by default "ha_bid_high".
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

    notify_abort = False

    # check if the buy column is greater than the wma
    if not first_time_frame_run:
        df.loc[df[signal_buy_column] > df["wma"], "signal"] = 1
        df["trigger"] = df["signal"].diff().fillna(0).astype(int)

        df.loc[(df[signal_exit_column] < df["wma"]) & (df["trigger"] != 1), "signal"] = 0
        df["trigger"] = df["signal"].diff().fillna(0).astype(int)

        last_row = df.iloc[-1]
        if last_row[signal_buy_column] > last_row["wma"] and last_row[signal_exit_column] < last_row["wma"]:
            notify_abort = True

    else:
        df.loc[df[signal_buy_column] > df["wma"], "signal"] = 1
        df.loc[df[signal_exit_column] < df["wma"], "signal"] = 0
        df["trigger"] = df["signal"].diff().fillna(0).astype(int)

    return notify_abort


def kernel(  # noqa: PLR0913
    df: pd.DataFrame,
    first_time_frame_run: bool = True,
    signal_buy_column: str = "ha_low",
    signal_exit_column: str = "ha_high",
    source_column: str = "bid_open",
    wma_period: int = 20,
    take_profit_value: float = 0,
    optimistic: bool = False,
) -> bool:
    """Process a DataFrame containing trading data.

    This function processes a DataFrame containing trading data and generate trading signals
    using Heikin-Ashi candlesticks and weighted moving average (wma).

    TODO: support other pipelines

    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame containing trading data.
    first_time_frame_run : bool, optional
        Whether this is the first time frame run.
    signal_buy_column : str, optional
        The column name for the buy signal data, by default "ha_low".
    signal_exit_column : str, optional
        The column name for the exit signal data, by default "ha_high".
    source_column : str, optional
        The column name for the source data, by default "bid_open".
    wma_period : int, optional
        The period for the weighted moving average, by default 20.
    take_profit_value : float, optional
        The take profit value as a multiplier of the atr, by default 0.
    optimistic : bool, optional
        Whether to use the ask_open or ask_high as the entry price, by default False.
    

    Returns
    -------
    bool
        True if the trade should be aborted, False otherwise.

    """
    # calculate the ATR for the trailing stop loss
    atr(df, wma_period)

    # signal using the close prices
    # signal and trigger interval could appears as this:
    # 0 0 1 1 1 0 0 - 1 above or 0 below the wma
    # 0 0 1 0 0 -1 0 - diff gives actual trigger
    # offline:
    # that means that the price to open the trade at would be the open price
    # if we check that the open price is above the wma then we buy
    # the price to close the trade at would be the close price below the wma
    # online:
    # that means that the price to open the trade at would be the close price
    # if we check that the close price is above the wma then we buy
    # the price to close the trade at would be the open price below the wma
    heikin_ashi(df)
    notify_abort = wma_signals(
        df,
        signal_exit_column=signal_exit_column,
        signal_buy_column=signal_buy_column,
        wma_period=wma_period,
        source_column=source_column,
        first_time_frame_run=first_time_frame_run,
    )

    # calculate the entry prices:
    entry_price(df, optimistic)

    # recalculate the entry prices after a take profit
    if take_profit_value > 0:
        take_profit(df, take_profit_value, optimistic)

    # calculate the exit total
    exit_total(df)

    return notify_abort


def report(
    df: pd.DataFrame,
):
    """Print a report of the trading results.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.

    """
    df_ticks = df[
        [
            "signal",
            "trigger",
            "atr",
            "wma",
            "open",
            "entry_price",
            "ask_open",
            "bid_open",
            "position_value",
            "exit_value",
            "running_total",
            "exit_total",
        ]
    ].copy()
    df_ticks.reset_index(inplace=True)
    logger.info("current status")
    logger.info(df_ticks.tail(18).round(4).to_csv())
    df_orders = df_ticks.copy()
    df_orders = df_orders[df_orders["trigger"] != 0]
    logger.debug("last 6 trades")
    logger.debug(df_orders.tail(6).round(4).to_csv())
