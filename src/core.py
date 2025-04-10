import logging  # noqa: D100
import talib
from calc import entry_price, exit_total, take_profit
from chart import heikin_ashi
import pandas as pd

logger = logging.getLogger("main.py")

Thursday = 4


def wma_signals(
    df: pd.DataFrame,
    source_column: str = "ha_low",
    signal_buy_column: str = "ha_bid_low",
    signal_exit_column: str = "ha_bid_high",
    wma_period: int = 20,
) -> None:
    """Generate trading signals based on a comparison of the Heikin-Ashi highs and lows to the wma.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
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
    df.loc[(df[signal_buy_column] > df["wma"]) | (df[signal_exit_column] < df["wma"]), "signal"] = 1
    df["trigger"] = df["signal"].diff().fillna(0).astype(int)


def kernel(  # noqa: PLR0913
    df: pd.DataFrame,
    signal_buy_column: str = "ha_low",
    signal_exit_column: str = "ha_high",
    source_column: str = "bid_open",
    wma_period: int = 20,
    take_profit_value: float = 0,
    optimistic: bool = False,
) -> pd.DataFrame:
    """Process a DataFrame containing trading data.

    This function processes a DataFrame containing trading data and generate trading signals
    using Heikin-Ashi candlesticks and weighted moving average (wma).

    TODO: support pipelines other than wma_ha

    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame containing trading data.
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
    pd.DataFrame
        A DataFrame containing the trading signals and portfolio calculations.

    """
    # calculate the ATR for the trailing stop loss
    df = atr(df, wma_period)

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
    wma_signals(
        df, signal_exit_column=signal_exit_column, signal_buy_column=signal_buy_column, wma_period=wma_period, source_column=source_column
    )

    # apply trailing stop loss
    # df = apply_trailing_stop_loss(df)

    # calculate the portfolio:
    # When the trigger is 1, use the ask_open price (buy signal)
    # When the trigger is -1, it means the buy signal is no longer valid, and the bid_open price
    # at this point would be the same as the bid_close price at the previous point (where the signal
    # was 1)
    # since the closing price is trailing we can use the bid_open in the immediate
    # next row
    # res = portfolio(df, "ask_high", "bid_open")
    entry_price(df, optimistic)

    # recalculate the entry prices after a take profit
    if take_profit_value > 0:
        take_profit(df, take_profit_value, optimistic)

    # calculate the exit total
    exit_total(df)

    return df


def atr(df: pd.DataFrame, wma_period: int) -> pd.DataFrame:
    """Calculate the ATR and multiply it by .5 for the trailing stop loss.

    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame containing trading data.
    wma_period : int
        The period for the weighted moving average.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the ATR and the trailing stop loss.

    """
    df["atr"] = talib.ATR(
        df["high"].to_numpy(),
        df["low"].to_numpy(),
        df["close"].to_numpy(),
        timeperiod=wma_period,
    )

    return df


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
            "entry_price",
            "ask_high",
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
