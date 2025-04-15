import pandas as pd  # noqa: D100
import logging


logger = logging.getLogger("reporting")


def report(
    df: pd.DataFrame,
    signal_buy_column: str,
):
    """Print a report of the trading results.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    signal_buy_column : str
        The column name for the buy signal data.

    """
    df_ticks = df.reset_index()[
        [
            "timestamp",
            "signal",
            "trigger",
            "atr",
            "wma",
            signal_buy_column,
            "ask_open",
            "bid_open",
            "position_value",
            "exit_value",
            "running_total",
            "exit_total",
        ]
    ]
    df_ticks['timestamp'] = pd.to_datetime(df_ticks['timestamp'])
    df_ticks['date'] = df_ticks['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_ticks.drop("timestamp", axis=1, inplace=True)
    df_orders = df_ticks.copy()
    df_orders = df_orders[df_orders["trigger"] != 0]
    logger.info("recent trades")
    logger.info("\n" +df_orders.tail(2).round(4).to_string(index=False, header=True, justify="left"))
    logger.debug("current status")
    logger.debug("\n" + df_ticks.tail(6).round(4).to_string(index=False, header=True, justify="left"))
