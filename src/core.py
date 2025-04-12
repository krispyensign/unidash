import talib  # noqa: D100
from calc import entry_price, exit_total, take_profit, atr
from chart import heikin_ashi
import pandas as pd

Thursday = 4


def wma_signals(  # noqa: PLR0913
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

    # check if the buy column is greater than the wma
    df.loc[df[signal_buy_column] > df["wma"], "signal"] = 1
    df["trigger"] = df["signal"].diff().fillna(0).astype(int)

    df.loc[(df[signal_exit_column] < df["wma"]) & (df["trigger"] != 1), "signal"] = 0
    df["trigger"] = df["signal"].diff().fillna(0).astype(int)


def kernel(  # noqa: PLR0913
    df: pd.DataFrame,
    signal_buy_column: str = "ha_low",
    signal_exit_column: str = "ha_high",
    source_column: str = "bid_open",
    wma_period: int = 20,
    take_profit_value: float = 0,
    optimistic: bool = False,
) -> None:
    """Process a DataFrame containing trading data.

    This function processes a DataFrame containing trading data and generate trading signals
    using candlesticks and weighted moving average (wma).

    TODO: support other pipelines

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
    wma_signals(
        df,
        signal_exit_column=signal_exit_column,
        signal_buy_column=signal_buy_column,
        wma_period=wma_period,
        source_column=source_column,
    )

    # calculate the entry prices:
    entry_price(df, optimistic)

    # recalculate the entry prices after a take profit
    if take_profit_value > 0:
        take_profit(df, take_profit_value, optimistic)

    # calculate the exit total
    exit_total(df)
