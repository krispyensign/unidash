from datetime import datetime  # noqa: D100
import pandas as pd
import v20  # type: ignore

from core.config import BACKTEST_COUNT, GRANULARITY, WMA_PERIOD, TAKE_PROFIT_MULTIPLIER
from core.kernel import kernel
from exchange import (
    getOandaOHLC,
    OandaContext,
)

import logging

logger = logging.getLogger("backtest")


class SignalConfig:
    """SignalConfig class."""

    def __init__(
        self, source_column: str, signal_buy_column: str, signal_exit_column: str
    ):
        """Initialize a SignalConfig object."""
        self.source_column = source_column
        self.signal_buy_column = signal_buy_column
        self.signal_exit_column = signal_exit_column

    def __str__(self):
        """Return a string representation of the SignalConfig object."""
        return f"so:{self.source_column}, sib:{self.signal_buy_column}, sie:{self.signal_exit_column}"


def backtest(instrument: str, token: str) -> SignalConfig:  # noqa: PLR0915
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
    ]
    signal_buy_columns = [
        "open",
        "high",
        "bid_open",
        "bid_high",
        "ask_open",
        "ask_high",
    ]
    signal_exit_columns = [
        "open",
        "low",
        "bid_open",
        "bid_low",
        "ask_open",
        "ask_low",
    ]
    total_combinations = (
        len(source_columns) * len(signal_buy_columns) * len(signal_exit_columns)
    )
    logger.info(f"total_combinations: {total_combinations}")
    for source_column_name in source_columns:
        for signal_buy_column_name in signal_buy_columns:
            for signal_exit_column_name in signal_exit_columns:
                df = orig_df.copy()
                kernel(
                    df,
                    source_column=source_column_name,
                    signal_buy_column=signal_buy_column_name,
                    signal_exit_column=signal_exit_column_name,
                    wma_period=WMA_PERIOD,
                    take_profit_value=TAKE_PROFIT_MULTIPLIER,
                )

                df_wins = len(df[(df["exit_total"] > 0) & (df["trigger"] == -1)])
                df_losses = len(df[(df["exit_total"] < 0) & (df["trigger"] == -1)])
                if df_wins <= df_losses:
                    continue

                exit_total = df["exit_total"].iloc[-1]
                min_exit_total = df["exit_total"].min()
                if min_exit_total > max_min_exit_total:
                    logger.debug(
                        "new min found q:%s so:%s sib:%s sie:%s ",
                        round(min_exit_total, 5),
                        source_column_name,
                        signal_buy_column_name,
                        signal_exit_column_name,
                    )
                    max_min_exit_total = min_exit_total
                    best_min_max_signal_buy_column_name = signal_buy_column_name
                    best_min_max_signal_exit_column_name = signal_exit_column_name
                    best_min_max_source_column_name = source_column_name
                    not_worst_df = df.copy()

                if exit_total > max_exit_total:
                    logger.debug(
                        "new max found q:%s so:%s sib:%s sie:%s",
                        round(exit_total, 5),
                        source_column_name,
                        signal_buy_column_name,
                        signal_exit_column_name,
                    )
                    max_exit_total = exit_total
                    best_max_signal_buy_column_name = signal_buy_column_name
                    best_max_signal_exit_column_name = signal_exit_column_name
                    best_max_source_column_name = source_column_name
                    best_df = df.copy()

    df_wins = len(best_df[(best_df["exit_total"] > 0) & (best_df["trigger"] == -1)])
    df_losses = len(best_df[(best_df["exit_total"] < 0) & (best_df["trigger"] == -1)])
    logger.debug(
        "best max found so:%s sib:%s sie:%s w:%s l:%s q_max:%s q_min:%s",
        best_max_source_column_name,
        best_max_signal_buy_column_name,
        best_max_signal_exit_column_name,
        df_wins,
        df_losses,
        round(max_exit_total, 5),
        round(best_df["exit_total"].min(), 5),
    )

    df_wins = len(
        not_worst_df[(not_worst_df["exit_total"] > 0) & (not_worst_df["trigger"] == -1)]
    )
    df_losses = len(
        not_worst_df[(not_worst_df["exit_total"] < 0) & (not_worst_df["trigger"] == -1)]
    )
    logger.debug(
        "not worst found so:%s sib:%s sie:%s w:%s l:%s q_max:%s q_min:%s",
        best_min_max_source_column_name,
        best_min_max_signal_buy_column_name,
        best_min_max_signal_exit_column_name,
        df_wins,
        df_losses,
        round(not_worst_df["exit_total"].iloc[-1], 5),
        round(not_worst_df["exit_total"].min(), 5),
    )

    endTime = datetime.now()
    logger.info(f"run interval: {endTime - start_time}")
    logger.debug("start time: %s", start_time.strftime("%Y-%m-%d %H:%M:%S"))

    # choose the least worst combination to minimize loss
    if (
        max_min_exit_total > best_df["exit_total"].min()
        and not_worst_df["exit_total"].iloc[-1] > 0
    ):
        logger.info("best min selected")
        return SignalConfig(
            best_min_max_source_column_name,
            best_min_max_signal_buy_column_name,
            best_min_max_signal_exit_column_name,
        )

    logger.info("best max selected")
    return SignalConfig(
        best_max_source_column_name,
        best_max_signal_buy_column_name,
        best_max_signal_exit_column_name,
    )
