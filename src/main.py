"""Main module."""

from datetime import datetime
import sys
from time import sleep
import pandas as pd
import numpy as np
import talib
from chart import heikin_ashi
import v20  # type: ignore

from exchange import (
    close_order,
    get_open_trades,
    getOandaOHLC,
    getOandaBalance,
    place_order,
)

import logging

logger = logging.getLogger("main.py")

Thursday = 4


def wma_signals(
    df: pd.DataFrame,
    sourceColumn: str = "ha_low",
    signalColumn: str = "ha_bid_low",
    wma_period: int = 20,
) -> None:
    """Generate trading signals based on a comparison of the Heikin-Ashi highs and lows to the wma.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    sourceColumn : str, optional
        The column name for the source data, by default "ha_low".
    signalColumn : str, optional
        The column name for the signal data, by default "ha_bid_low".
    wma_period : int, optional
        The period for the weighted moving average, by default 20.

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
    df["wma"] = talib.WMA(df[sourceColumn].to_numpy(), wma_period)

    # check if the buy column is greater than the wma
    df.loc[df[signalColumn] > df["wma"], "signal"] = 1
    df["trigger"] = df["signal"].diff().fillna(0).astype(int)


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


def take_profit(df: pd.DataFrame, take_profit: float) -> None:
    """Apply a take profit strategy to the trading data.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    take_profit : float
        The take profit value as a multiplier of the atr.

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
    entry_price(df)


def entry_price(df: pd.DataFrame) -> None:
    """Calculate the entry price for a given trading signal.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.

    Notes
    -----
    The 'internal_bit_mask' column is set to the bit-wise OR of the 'signal' and 'trigger'
    columns. The 'entry_price' column is set to the 'ask_high' column when the 'trigger'
    column is 1, and the 'value' column is set to the difference between the 'bid_open'
    and 'entry_price' columns times the 'internal_bit_mask' column.

    """
    df["internal_bit_mask"] = df["signal"] | abs(df["trigger"])
    df["entry_price"] = np.where(df["trigger"] == 1, df["ask_high"], np.nan)
    df["entry_price"] = df["entry_price"].ffill() * df["internal_bit_mask"]
    df["position_value"] = (df["bid_open"] - df["entry_price"]) * df[
        "internal_bit_mask"
    ]


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
            "entry_price",
            "ask_high",
            "bid_open",
            "position_value",
            "exit_value",
            "running_total",
            "exit_total",
            "atr",
        ]
    ].copy()
    df_ticks.reset_index(inplace=True)
    logger.info("current status")
    logger.info(df_ticks.tail(18).round(4).to_csv())
    df_orders = df_ticks.copy()
    df_orders = df_orders[df_orders["trigger"] != 0]
    logger.debug("last 6 trades")
    logger.debug(df_orders.tail(6).round(4).to_csv())


def backtest(instrument: str, token: str):  # noqa: PLR0915
    """Run a backtest of the trading strategy.

    Parameters
    ----------
    instrument : str
        The instrument to trade.
    token : str
        The Oanda API token.

    Notes
    -----
    The backtest will run for a large number of combinations of source and signal
    columns. The best combination will be saved to best_df and the results will be
    printed to the log file.

    """
    logging.basicConfig(level=logging.DEBUG, filename="backtest.log")
    logger.info("starting backtest")
    start_time = datetime.now()
    ctx = v20.Context("api-fxpractice.oanda.com", token=token)
    count = 40
    granularity = "M5"
    wma_period = 20
    take_profit_value = 0

    df = getOandaOHLC(ctx, instrument, count=count, granularity=granularity)
    logger.info(
        "count: %s granularity: %s wma_period: %s", count, granularity, wma_period
    )
    max_exit_total = -99.0
    max_min_exit_total = -99.0
    best_max_signalColumnName = ""
    best_max_sourceColumnName = ""
    best_max_min_signalColumnName = ""
    best_max_min_sourceColumnName = ""
    best_df = pd.DataFrame()
    not_worst_df = pd.DataFrame()
    signalColumnNames = [
        "open",
        "high",
        "low",
        "ha_open",
        "ha_low",
        "ha_high",
        "ha_bid_open",
        "ha_bid_low",
        "ha_bid_high",
        "ha_ask_open",
        "ha_ask_low",
        "ha_ask_high",
        "bid_open",
        "bid_high",
        "bid_low",
        "ask_open",
        "ask_high",
        "ask_low",
    ]
    sourceColumnNames = [
        "open",
        # "high",
        # "low",
        "ha_open",
        # "ha_low",
        # "ha_high",
        "ha_bid_open",
        # "ha_bid_low",
        # "ha_bid_high",
        "ha_ask_open",
        # "ha_ask_low",
        # "ha_ask_high",
        "bid_open",
        # "bid_high",
        # "bid_low",
        "ask_open",
        # "ask_high",
        # "ask_low",
    ]
    total_combinations = len(sourceColumnNames) * len(sourceColumnNames)
    logger.info(f"total_combinations: {total_combinations}")
    for sourceColumnName in sourceColumnNames:
        for signalColumnName in signalColumnNames:
            df = kernel(
                df,
                sourceColumn=sourceColumnName,
                signalColumn=signalColumnName,
                wma_period=wma_period,
                take_profit_value=take_profit_value,
            )
            df["exit_total"] = df["exit_total"].fillna(0)

            exit_total = df["exit_total"].iloc[-1]
            min_exit_total = df["exit_total"].min()
            if min_exit_total > max_min_exit_total:
                logger.info(
                    "!!new min found q:%s si:%s so:%s",
                    min_exit_total,
                    signalColumnName,
                    sourceColumnName,
                )
                max_min_exit_total = min_exit_total
                best_max_min_sourceColumnName = sourceColumnName
                best_max_min_signalColumnName = signalColumnName
                not_worst_df = df.copy()

            if exit_total > max_exit_total:
                logger.info(
                    "!!new max found q:%s si:%s so:%s",
                    exit_total,
                    signalColumnName,
                    sourceColumnName,
                )
                max_exit_total = exit_total
                best_max_sourceColumnName = sourceColumnName
                best_max_signalColumnName = signalColumnName
                best_df = df.copy()
            elif exit_total > 0:
                logger.info(
                    "  found q:%s si:%s so:%s",
                    exit_total,
                    signalColumnName,
                    sourceColumnName,
                )

    report(best_df)

    logger.info("best combination")
    logger.info(f"best_signalColumnName: {best_max_signalColumnName}")
    logger.info(f"best_sourceColumnName: {best_max_sourceColumnName}")
    logger.info(f"max_exit_total: {max_exit_total}")

    report(not_worst_df)

    logger.info("not worst combination")
    logger.info(f"not_worst_signalColumnName: {best_max_min_signalColumnName}")
    logger.info(f"not_worst_sourceColumnName: {best_max_min_sourceColumnName}")
    logger.info(f"max_min_exit_total: {max_min_exit_total}")

    endTime = datetime.now()
    logger.info(f"run interval: {endTime - start_time}")
    logger.info("start time: %s", start_time.strftime("%Y-%m-%d %H:%M:%S"))


def kernel(
    df: pd.DataFrame,
    signalColumn: str = "ha_bid_open",
    sourceColumn: str = "ha_ask_open",
    wma_period: int = 20,
    take_profit_value: float = 0,
) -> pd.DataFrame:
    """Process a DataFrame containing trading data.

    This function processes a DataFrame containing trading data and generate trading signals
    using Heikin-Ashi candlesticks and weighted moving average (wma).

    TODO: support pipelines other than wma_ha

    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame containing trading data.
    signalColumn : str, optional
        The column name for the signal data, by default "ha_low".
    sourceColumn : str, optional
        The column name for the source data, by default "ha_bid_low".
    wma_period : int, optional
        The period for the weighted moving average, by default 20.
    take_profit_value : float, optional
        The take profit value as a multiplier of the atr, by default 0

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
        df, sourceColumn=sourceColumn, signalColumn=signalColumn, wma_period=wma_period
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
    entry_price(df)

    # recalculate the entry prices after a take profit
    if take_profit_value > 0:
        take_profit(df, take_profit_value)

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


def bot(  # noqa: C901, PLR0915
    token: str, account_id: str, instrument: str, amount: float | None = None
) -> None:
    """Bot that trades on Oanda.

    This function trades on Oanda using the Oanda API. It places market orders based on the
    trading signals generated by the kernel function.  It closes the trade when the trigger is -1.

    Parameters
    ----------
    token : str
        The Oanda API token.
    account_id : str
        The Oanda account ID.
    instrument : str
        The instrument to trade.
    amount : float | None
        The amount to trade. If None, the bot will calculate the amount based
        on the current balance.

    """
    logging.basicConfig(level=logging.DEBUG, filename="bot.log")
    logger.info("starting bot")
    start_time = datetime.now()
    logger.info("time now: %s", start_time.strftime("%Y-%m-%d %H:%M:%S"))
    ctx = v20.Context("api-fxpractice.oanda.com", token=token)
    trade_id = -1
    while True:
        df: pd.DataFrame
        startTime = datetime.now()
        try:
            trade_id = get_open_trades(ctx, account_id)
            df = getOandaOHLC(ctx, instrument, count=40, granularity="M5")
            logger.debug(df.head(1).round(3).to_csv())
            logger.debug(df.tail(1).round(3).to_csv())
        except Exception as err:  # noqa: E722
            logger.error(err)
            trade_id = -1
            sleep(5)
            continue

        df = kernel(df)

        trigger = df["trigger"].iloc[-1]
        signal = df["signal"].iloc[-1]
        atr = df["atr"].iloc[-1]
        take_profit = atr + df["ask_open"].iloc[-1]
        if trigger == 1 and trade_id == -1:
            try:
                if amount is None:
                    balance = getOandaBalance(ctx, account_id)
                    amount = (balance // 2 + 1) * 50
                trade_id = place_order(ctx, account_id, instrument, amount, take_profit)
                continue
            except Exception as err:
                trade_id = -1
                logger.error(err)
                sleep(5)

        if trigger != 1 and signal == 0 and trade_id != -1:
            try:
                close_order(ctx, account_id, trade_id)
            except Exception as err:
                logger.error(err)

        endTime = datetime.now()
        # print the results
        report(df)
        logger.info(f"run interval: {endTime - startTime}")
        logger.info("start time: %s", start_time.strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("last run time: %s", endTime.strftime("%Y-%m-%d %H:%M:%S"))
        sleep(5)


if __name__ == "__main__":
    if "backtest" in sys.argv[1]:
        backtest(instrument=sys.argv[3], token=sys.argv[2])
    elif "bot" in sys.argv[1]:
        bot(sys.argv[2], sys.argv[3], sys.argv[4], 1000)
    else:
        print(sys.argv)
        print("""
            WMA HEIKEN ASHI
              Usage: 
                python main.py backtest <some csv file>
                python main.py bot <token> <account_id> <instrument>
              """)
