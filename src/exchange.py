"""Get OHLC data from an exchange and convert it into a pandas DataFrame."""
from datetime import datetime, timedelta
import v20
import pandas as pd

Thursday = 4

def getOandaOHLC(ctx: v20.Context, instrment: str) -> pd.DataFrame:
    # create dataframe with candles
    """Get OHLC data from Oanda and convert it into a pandas DataFrame.

    Parameters
    ----------
    ctx : v20.Context
        The Oanda API context.
    instrment : str
        The instrument to get the OHLC data for.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the OHLC data with the following columns:

        - timestamp
        - open
        - high
        - low
        - close
        - bid_open
        - bid_high
        - bid_low
        - bid_close
        - ask_open
        - ask_high
        - ask_low
        - ask_close

    """
    df = pd.DataFrame(
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "bid_open",
            "bid_high",
            "bid_low",
            "bid_close",
            "ask_open",
            "ask_high",
            "ask_low",
            "ask_close",
        ]
    )

    daydelta = 1
    weekday = datetime.now().weekday()
    if weekday > Thursday:
        daydelta = weekday - 3

    resp = ctx.instrument.candles(
        instrument=instrment,
        granularity="M5",
        fromTime=(datetime.now() - timedelta(days=daydelta)).timestamp(),
        price="MAB",
    )
    if resp.body["candles"]:
        candles: v20.instrument.Candlesticks = resp.body["candles"]
        for i, candle in enumerate(candles):
            df.loc[i] = {  # type: ignore
                "timestamp": candle.time,
                "open": candle.mid.o,
                "high": candle.mid.h,
                "low": candle.mid.l,
                "close": candle.mid.c,
                "bid_open": candle.bid.o,
                "bid_high": candle.bid.h,
                "bid_low": candle.bid.l,
                "bid_close": candle.bid.c,
                "ask_open": candle.ask.o,
                "ask_high": candle.ask.h,
                "ask_low": candle.ask.l,
                "ask_close": candle.ask.c,
            }

    return df