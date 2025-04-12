import pandas as pd  # noqa: D100
import logging


logger = logging.getLogger("reporting")


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
            # "open",
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
    df_orders = df_ticks.copy()
    df_orders = df_orders[df_orders["trigger"] != 0]
    logger.info("last 2 trades")
    logger.info(df_orders.tail(2).round(4).to_csv())
    logger.debug("current status")
    logger.debug(df_ticks.tail(6).round(4).to_csv())
