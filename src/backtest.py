"""Backtest the trading strategy."""

from datetime import datetime
import pandas as pd
import v20  # type: ignore

from core.config import (
    BACKTEST_COUNT,
    ENTRY_COLUMN,
    GRANULARITY,
    WMA_PERIOD,
    TAKE_PROFIT_MULTIPLIER,
)
from core.kernel import kernel
from exchange import (
    getOandaOHLC,
    OandaContext,
)

import logging

from reporting import report

logger = logging.getLogger("backtest")

SOURCE_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "bid_open",
    "bid_low",
    "bid_high",
    "bid_close",
    "ask_open",
    "ask_low",
    "ask_high",
    "ask_close",
    "ha_open",
    "ha_low",
    "ha_close",
    "ha_high",
    "ha_bid_open",
    "ha_bid_low",
    "ha_bid_close",
    "ha_bid_high",
    "ha_ask_open",
    "ha_ask_low",
    "ha_ask_close",
    "ha_ask_high",
]


class SignalConfig:
    """SignalConfig class."""

    def __init__(self, source_column: str, signal_buy_column: str):
        """Initialize a SignalConfig object."""
        self.source_column = source_column
        self.signal_buy_column = signal_buy_column

    def __str__(self):
        """Return a string representation of the SignalConfig object."""
        return f"so:{self.source_column}, sib:{self.signal_buy_column}"


def backtest(instrument: str, token: str) -> SignalConfig:
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
    logger.info("starting backtest")
    start_time = datetime.now()
    ctx = OandaContext(
        v20.Context("api-fxpractice.oanda.com", token=token), None, token
    )

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
    best_max_conf = SignalConfig("", "")
    not_worst_conf = SignalConfig("", "")
    best_df = pd.DataFrame()
    not_worst_df = pd.DataFrame()
    total_combinations = len(SOURCE_COLUMNS) * len(SOURCE_COLUMNS)
    logger.info(f"total_combinations: {total_combinations}")
    for source_column_name in SOURCE_COLUMNS:
        for signal_buy_column_name in SOURCE_COLUMNS:
            df = orig_df.copy()
            kernel(
                df,
                source_column=source_column_name,
                signal_buy_column=signal_buy_column_name,
                wma_period=WMA_PERIOD,
                take_profit_value=TAKE_PROFIT_MULTIPLIER,
                entry_column=ENTRY_COLUMN,
            )

            df_wins = len(df[(df["exit_value"] > 0) & (df["trigger"] == -1)])
            df_losses = len(df[(df["exit_value"] < 0) & (df["trigger"] == -1)])
            if df_losses > df_wins:
                continue

            exit_total = df["exit_total"].iloc[-1]
            min_exit_total = df["exit_total"].min()
            if min_exit_total > max_min_exit_total:
                logger.debug(
                    "new min found q:%s so:%s sib:%s",
                    round(min_exit_total, 5),
                    source_column_name,
                    signal_buy_column_name,
                )
                max_min_exit_total = min_exit_total
                not_worst_conf = SignalConfig(
                    source_column_name, signal_buy_column_name
                )
                not_worst_df = df.copy()

            if exit_total > max_exit_total:
                logger.debug(
                    "new max found q:%s so:%s sib:%s",
                    round(exit_total, 5),
                    source_column_name,
                    signal_buy_column_name,
                )
                max_exit_total = exit_total
                best_max_conf = SignalConfig(source_column_name, signal_buy_column_name)
                best_df = df.copy()

    df_wins = len(best_df[(best_df["exit_value"] > 0) & (best_df["trigger"] == -1)])
    df_losses = len(best_df[(best_df["exit_value"] < 0) & (best_df["trigger"] == -1)])
    logger.debug(
        "best max found %s w:%s l:%s q_max:%s q_min:%s",
        best_max_conf,
        df_wins,
        df_losses,
        round(max_exit_total, 5),
        round(best_df["exit_total"].min(), 5),
    )
    report(best_df, best_max_conf.signal_buy_column)

    df_wins = len(
        not_worst_df[(not_worst_df["exit_value"] > 0) & (not_worst_df["trigger"] == -1)]
    )
    df_losses = len(
        not_worst_df[(not_worst_df["exit_value"] < 0) & (not_worst_df["trigger"] == -1)]
    )
    logger.debug(
        "not worst found %s w:%s l:%s q_max:%s q_min:%s",
        not_worst_conf,
        df_wins,
        df_losses,
        round(not_worst_df["exit_total"].iloc[-1], 5),
        round(not_worst_df["exit_total"].min(), 5),
    )
    report(not_worst_df, not_worst_conf.signal_buy_column)

    endTime = datetime.now()
    logger.info(f"run interval: {endTime - start_time}")
    logger.debug("start time: %s", start_time.strftime("%Y-%m-%d %H:%M:%S"))

    # choose the least worst combination to minimize loss
    if (
        max_min_exit_total > best_df["exit_total"].min()
        and not_worst_df["exit_total"].iloc[-1] > 0
    ):
        logger.info("best min selected")
        return not_worst_conf

    logger.info("best max selected")
    return best_max_conf
