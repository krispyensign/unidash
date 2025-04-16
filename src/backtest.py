"""Backtest the trading strategy."""

from dataclasses import dataclass
from datetime import datetime
import itertools
import pandas as pd
import v20  # type: ignore

from config import (
    BACKTEST_COUNT,
    ENTRY_COLUMN,
    EXIT_COLUMN,
    GRANULARITY,
    WMA_PERIOD,
)
from core.kernel import KernelConfig, kernel
from exchange import (
    getOandaOHLC,
    OandaContext,
)

import logging

from reporting import report

logger = logging.getLogger("backtest")
APP_START_TIME = datetime.now()

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


class PerfTimer:
    """PerfTimer class."""

    def __init__(self, app_start_time: datetime):
        """Initialize a PerfTimer object."""
        self.app_start_time = app_start_time
        pass

    def __enter__(self):
        """Start the timer."""
        self.start = datetime.now()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Stop the timer."""
        self.end = datetime.now()
        logger.info(f"run interval: {self.end - self.start}")
        logger.info("up time: %s", (self.end - self.app_start_time))
        logger.info("last run time: %s", self.end.strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class SignalConfig:
    """SignalConfig class."""

    source_column: str
    signal_buy_column: str
    trailing_stop: float
    take_profit: float

    def __str__(self):
        """Return a string representation of the SignalConfig object."""
        return f"so:{self.source_column}, sib:{self.signal_buy_column}, ts:{self.trailing_stop}, tp:{self.take_profit}"


@dataclass
class Record:
    """Record class."""

    signal: int
    trigger: int
    losses: int
    wins: int
    exit_total: float
    min_exit_total: float

    def __str__(self) -> str:
        """Return a string representation of the Record object."""
        return f"w:{self.wins} l:{self.losses}, q:{round(self.exit_total, 5)}, q_min:{round(self.min_exit_total, 5)}"


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
        v20.Context("api-fxpractice.oanda.com", token=token), None, token, instrument
    )

    orig_df = getOandaOHLC(ctx, count=BACKTEST_COUNT, granularity=GRANULARITY)
    logger.info(
        "count: %s granularity: %s wma_period: %s",
        BACKTEST_COUNT,
        GRANULARITY,
        WMA_PERIOD,
    )

    best_max_conf = SignalConfig("", "", 0.0, 0.0)
    not_worst_conf = SignalConfig("", "", 0.0, 0.0)
    best_df = pd.DataFrame()
    not_worst_df = pd.DataFrame()
    best_rec = Record(0, 0, 0, 0, -99.0, -99.0)
    not_worst_rec = Record(0, 0, 0, 0, -99.0, -99.0)

    take_profit_multipliers = (x / 2 for x in range(0, 7, 1))
    stop_loss_multipliers = (x / 2 for x in range(0, 7, 1))
    column_pairs = itertools.product(
        SOURCE_COLUMNS, SOURCE_COLUMNS, take_profit_multipliers, stop_loss_multipliers
    )
    column_pair_len = len(SOURCE_COLUMNS) * len(SOURCE_COLUMNS) * 8 * 8
    logger.info(f"total_combinations: {column_pair_len}")
    count = -1
    total_found = 0
    with PerfTimer(start_time):
        for (
            source_column_name,
            signal_buy_column_name,
            take_profit_multiplier,
            stop_loss_multiplier,
        ) in column_pairs:
            count += 1
            if count % 1000 == 0:
                logger.debug(
                    "heartbeat: %s found. %s%%",
                    total_found,
                    round(count / column_pair_len, 3),
                )

            if stop_loss_multiplier >= take_profit_multiplier:
                continue

            kernel_conf = KernelConfig(
                signal_buy_column=signal_buy_column_name,
                source_column=source_column_name,
                wma_period=WMA_PERIOD,
                take_profit_value=take_profit_multiplier,
                entry_column=ENTRY_COLUMN,
                exit_column=EXIT_COLUMN,
                stop_loss=stop_loss_multiplier,
            )
            df = kernel(
                orig_df.copy(),
                include_incomplete=False,
                config=kernel_conf,
            )

            signal_conf = SignalConfig(
                source_column_name,
                signal_buy_column_name,
                stop_loss_multiplier,
                take_profit_multiplier,
            )

            rec = Record(
                signal=df["signal"].iloc[-1],
                trigger=df["trigger"].iloc[-1],
                losses=df["losses"].iloc[-1],
                wins=df["wins"].iloc[-1],
                exit_total=df["exit_total"].iloc[-1],
                min_exit_total=df["min_exit_total"].iloc[-1],
            )

            if rec.losses >= rec.wins:
                continue
            else:
                total_found += 1

            if rec.min_exit_total > not_worst_rec.min_exit_total:
                logger.debug(
                    "new min found %s %s",
                    rec,
                    signal_conf,
                )
                not_worst_rec = rec
                not_worst_conf = signal_conf
                not_worst_df = df.copy()

            if rec.exit_total > best_rec.exit_total:
                logger.debug(
                    "new max found %s %s",
                    rec,
                    signal_conf,
                )
                best_rec = rec
                best_max_conf = signal_conf
                best_df = df.copy()

    logger.debug(
        "best max found %s %s",
        best_max_conf,
        best_rec,
    )
    report(best_df, best_max_conf.signal_buy_column, ENTRY_COLUMN, EXIT_COLUMN)

    logger.debug(
        "not worst found %s %s",
        not_worst_conf,
        not_worst_rec,
    )
    report(not_worst_df, not_worst_conf.signal_buy_column, ENTRY_COLUMN, EXIT_COLUMN)

    # choose the least worst combination to minimize loss
    if (not_worst_rec.wins - not_worst_rec.losses) > (best_rec.wins - best_rec.losses):
        logger.info("best min selected")
        return not_worst_conf

    logger.info("best max selected")
    return best_max_conf
