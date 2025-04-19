"""Functions for reporting trading results."""

from datetime import timedelta
import pandas as pd
import logging


logger = logging.getLogger("reporting")

ENTRY_COLUMN = "ask_close"
EXIT_COLUMN = "bid_close"


def report(
    df: pd.DataFrame,
    signal_buy_column: str,
    signal_exit_column: str,
):
    """Print a report of the trading results.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    signal_buy_column : str
        The column name for the buy signal data.
    signal_exit_column : str
        The column name for the exit signal data.

    """
    df_ticks = df.reset_index()[
        [
            "timestamp",
            "signal",
            "trigger",
            "atr",
            "wma",
            signal_buy_column,
            signal_exit_column,
            ENTRY_COLUMN,
            EXIT_COLUMN,
            "entry_price",
            "position_value",
            "exit_value",
            "running_total",
            "exit_total",
        ]
    ]
    df_ticks["timestamp"] = pd.to_datetime(df_ticks["timestamp"])
    df_ticks["completed_datetime"] = (
        (timedelta(minutes=5) + df_ticks["timestamp"]).dt
    ).strftime("%Y-%m-%d %H:%M:%S")
    df_ticks.drop("timestamp", axis=1, inplace=True)
    df_orders = df_ticks.copy()
    df_orders = df_orders[df_orders["trigger"] != 0]
    logger.info("recent trades")
    logger.info(
        "\n"
        + df_orders.tail(12)
        .round(4)
        .to_string(header=True, justify="left")
    )
    logger.info("current status")
    logger.info(
        "\n"
        + df_ticks.tail(6).round(4).to_string(header=True, justify="left")
    )
