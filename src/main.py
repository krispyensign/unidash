"""Main module."""

from datetime import datetime
import sys
from time import sleep
import pandas as pd
import v20  # type: ignore

from core import kernel, report
from exchange import (
    close_order,
    get_open_trades,
    getOandaOHLC,
    place_order,
)

import logging

logger = logging.getLogger("main.py")

THURSDAY = 4

GRANULARITY = "M1"
WMA_PERIOD = 20
TAKE_PROFIT_VALUE = 1
BACKTEST_COUNT = 120
OPTOMISTIC = True
REFRESH_RATE = 1 if OPTOMISTIC else 10
BOT_COUNT = BACKTEST_COUNT
BOT_SOURCE_COLUMN = "ask_open"
BOT_SIGNAL_BUY_COLUMN = "bid_high"
BOT_SIGNAL_EXIT_COLUMN = "bid_low"


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

    orig_df = getOandaOHLC(
        ctx, instrument, count=BACKTEST_COUNT, granularity=GRANULARITY
    )
    logger.info(
        "count: %s granularity: %s wma_period: %s",
        BACKTEST_COUNT,
        GRANULARITY,
        WMA_PERIOD,
    )
    max_exit_total = -99.0
    max_min_exit_total = -99.0
    best_max_signal_buy_column_name = ""
    best_max_signal_exit_column_name = ""
    best_max_source_column_name = ""
    best_min_max_signal_buy_column_name = ""
    best_min_max_signal_exit_column_name = ""
    best_min_max_source_column_name = ""
    best_df = pd.DataFrame()
    not_worst_df = pd.DataFrame()
    source_columns = [
        "open",
        "bid_open",
        "ask_open",
        "ha_open",
        "ha_bid_open",
        "ha_ask_open",
    ]
    signal_buy_columns = [
        "open",
        "high",
        "bid_open",
        "bid_high",
        "ask_open",
        "ask_high",
        "ha_open",
        "ha_high",
        "ha_bid_open",
        "ha_bid_high",
        "ha_ask_open",
        "ha_ask_high",
    ]
    signal_exit_columns = [
        "open",
        "low",
        "bid_open",
        "bid_low",
        "ask_open",
        "ask_low",
        "ha_open",
        "ha_low",
        "ha_bid_open",
        "ha_bid_low",
        "ha_ask_open",
        "ha_ask_low",
    ]
    total_combinations = (
        len(source_columns) * len(signal_buy_columns) * len(signal_exit_columns)
    )
    logger.info(f"total_combinations: {total_combinations}")
    for source_column_name in source_columns:
        for signal_buy_column_name in signal_buy_columns:
            for signal_exit_column_name in signal_exit_columns:
                df = kernel(
                    orig_df.copy(),
                    source_column=source_column_name,
                    signal_buy_column=signal_buy_column_name,
                    signal_exit_column=signal_exit_column_name,
                    wma_period=WMA_PERIOD,
                    take_profit_value=TAKE_PROFIT_VALUE,
                    optimistic=OPTOMISTIC,
                )

                exit_total = df["exit_total"].iloc[-1]
                min_exit_total = df["exit_total"].min()
                if min_exit_total > max_min_exit_total:
                    logger.info(
                        "!!new min found q:%s sib:%s sie:%s so:%s",
                        min_exit_total,
                        signal_buy_column_name,
                        signal_exit_column_name,
                        source_column_name,
                    )
                    max_min_exit_total = min_exit_total
                    best_min_max_signal_buy_column_name = signal_buy_column_name
                    best_min_max_signal_exit_column_name = signal_exit_column_name
                    best_min_max_source_column_name = source_column_name
                    not_worst_df = df.copy()

                if exit_total > max_exit_total:
                    logger.info(
                        "!!new max found q:%s sib:%s sie:%s so:%s",
                        exit_total,
                        signal_buy_column_name,
                        signal_exit_column_name,
                        source_column_name,
                    )
                    max_exit_total = exit_total
                    best_max_signal_buy_column_name = signal_buy_column_name
                    best_max_signal_exit_column_name = signal_exit_column_name
                    best_max_source_column_name = source_column_name
                    best_df = df.copy()

    logger.info("==best combination")
    logger.info(f"best source {best_max_source_column_name}")
    logger.info(f"best buy {best_max_signal_buy_column_name}")
    logger.info(f"best exit {best_max_signal_exit_column_name}")
    logger.info(f"final_exit_total: {max_exit_total}")
    logger.info(f"min_exit_total: {best_df['exit_total'].min()}")

    logger.info("==not worst combination")
    logger.info(f"best min source {best_min_max_source_column_name}")
    logger.info(f"best min buy {best_min_max_signal_buy_column_name}")
    logger.info(f"best min exit {best_min_max_signal_exit_column_name}")
    logger.info(f"final_exit_total: {not_worst_df['exit_total'].iloc[-1]}")
    logger.info(f"min_exit_total: {max_min_exit_total}")

    endTime = datetime.now()
    logger.info(f"run interval: {endTime - start_time}")
    logger.info("start time: %s", start_time.strftime("%Y-%m-%d %H:%M:%S"))


def bot(  # noqa: C901, PLR0915
    token: str, account_id: str, instrument: str, amount: float
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
            df = getOandaOHLC(ctx, instrument, count=BOT_COUNT, granularity=GRANULARITY)
            logger.debug(df.head(1).round(3).to_csv())
            logger.debug(df.tail(1).round(3).to_csv())
        except Exception as err:  # noqa: E722
            logger.error(err)
            trade_id = -1
            sleep(5)
            continue

        df = kernel(
            df,
            take_profit_value=TAKE_PROFIT_VALUE,
            wma_period=WMA_PERIOD,
            optimistic=OPTOMISTIC,
            signal_buy_column=BOT_SIGNAL_BUY_COLUMN,
            signal_exit_column=BOT_SIGNAL_EXIT_COLUMN,
            source_column=BOT_SOURCE_COLUMN,
        )

        trigger = df["trigger"].iloc[-1]
        signal = df["signal"].iloc[-1]
        if trigger == 1 and trade_id == -1:
            try:
                trade_id = place_order(ctx, account_id, instrument, amount)
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
        sleep(REFRESH_RATE)


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
