"""Pipelines for generating trading signals."""

import pandas as pd
import talib

from chart import heikin_ashi


def wma_ha(
    data: pd.DataFrame,
    wmaSourceColumn: str = "ha_low",
    wmaPeriod: int = 20,
) -> pd.DataFrame:
    """Process the input DataFrame.

    This function processes the input DataFrame to generate trading signals using a weighted moving
    average (wma) of Heikin-Ashi candlesticks.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the trading data.
    wmaPeriod : int, optional
        The period for the wma calculation. The default is 20.
    wmaSourceColumn : str, optional
        The column name of the Heikin-Ashi candlesticks to use for the wma calculation.
        The default is "ha_low".

    Returns
    -------
    pd.DataFrame
        A DataFrame with the trading signals added.

    """
    data = heikin_ashi(data)
    data["wma"] = talib.WMA(data[wmaSourceColumn], wmaPeriod)

    return data
