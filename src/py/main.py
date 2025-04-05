"""Main module."""
from datetime import datetime, timedelta
import sys
from time import sleep  # noqa: D100
import pandas as pd
import numpy as np
import v20


def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """Generate Heikin Ashi candlesticks for a given dataframe.

    Heikin Ashi is a Japanese chart type that is used to identify trends and
    patterns in financial markets. It is similar to traditional candlestick charts,
    but it uses the average of the high, low, and closing prices to calculate
    the body of the candle.  This function also generates Heikin Ashi candlesticks
    for the bid and ask prices.

    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame containing OHLC data.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing Heikin Ashi candlesticks.  The candlesticks are
        added as new columns to the original DataFrame.  They are named
        'ha_close', 'ha_open', 'ha_high', and 'ha_low'. The 'ha_bid_close',
        'ha_ask_close', 'ha_bid_open', 'ha_ask_open', 'ha_bid_high', 'ha_ask_high',
        'ha_bid_low', and 'ha_ask_low' are also added.

    """
    df.reset_index(inplace=True)

    df["ha_close"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
    df["ha_bid_close"] = (
        df["bid_open"] + df["bid_high"] + df["bid_low"] + df["bid_close"]
    ) / 4
    df["ha_ask_close"] = (
        df["ask_open"] + df["ask_high"] + df["ask_low"] + df["ask_close"]
    ) / 4

    df.at[0, "ha_open"] = df.at[0, "open"]
    for i in range(1, len(df)):
        df.at[i, "ha_open"] = (df.at[i - 1, "ha_open"] + df.at[i - 1, "ha_close"]) / 2

    df.at[0, "ha_bid_open"] = df.at[0, "bid_open"]
    for i in range(1, len(df)):
        df.at[i, "ha_bid_open"] = (
            df.at[i - 1, "ha_bid_open"] + df.at[i - 1, "ha_bid_close"]
        ) / 2

    df.at[0, "ha_ask_open"] = df.at[0, "ask_open"]
    for i in range(1, len(df)):
        df.at[i, "ha_ask_open"] = (
            df.at[i - 1, "ha_ask_open"] + df.at[i - 1, "ha_ask_close"]
        ) / 2

    df["ha_high"] = df[["high", "ha_open", "ha_close"]].max(axis=1)
    df["ha_low"] = df[["low", "ha_open", "ha_close"]].min(axis=1)

    df["ha_bid_high"] = df[["bid_high", "ha_bid_open", "ha_bid_close"]].max(axis=1)
    df["ha_bid_low"] = df[["bid_low", "ha_bid_open", "ha_bid_close"]].min(axis=1)

    df["ha_ask_high"] = df[["ask_high", "ha_ask_open", "ha_ask_close"]].max(axis=1)
    df["ha_ask_low"] = df[["ask_low", "ha_ask_open", "ha_ask_close"]].min(axis=1)

    df.set_index("timestamp", inplace=True)

    return df


def wma(df: pd.DataFrame, period: int = 288, column: str = "ha_low") -> pd.DataFrame:
    """Calculate the weighted moving average (wma) of a column of a given DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the input column to which the wma will be applied.
    period : int, optional
        The period in days. The default is 288.
    column : str, optional
        The column to which the wma will be applied. The default is 'ha_low'.

    Returns
    -------
    pd.Dataframe
        The DataFrame with the 'wma' column added.

    Raises
    ------
    ValueError
        If wma_period is not greater than 0.
    ValueError
        If df is empty.
    ValueError
        If df does not contain the provided column.

    """
    weights = np.arange(1, period + 1)
    df["wma"] = (
        df[column]
        .rolling(period)
        .apply(lambda x: np.dot(x, weights) / np.sum(weights), raw=True)
    )

    return df


def generate_signals(
    df: pd.DataFrame, buyColumn: str = "ha_ask_high", sellColumn: str = "ha_bid_low"
) -> pd.DataFrame:
    """Generate trading signals based on a comparison of the Heikin-Ashi highs and lows to the wma.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    buyColumn : str, optional
        The column name for buying prices. The default is "ha_ask_high".
    sellColumn : str, optional
        The column name for selling prices. The default is "ha_bid_low".

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
    df.loc[df[buyColumn] > df["wma"], "signal"] = 1
    df.loc[df[sellColumn] < df["wma"], "signal"] = 0

    return df


def portfolio(
    data: pd.DataFrame, buyColumn: str = "ask_open", sellColumn: str = "bid_open"
) -> tuple[pd.DataFrame, bool, float, float]:
    """Calculate the portfolio value based on a DataFrame of OHLC data.

    Args:
        data (pd.DataFrame): A DataFrame containing OHLC data.
        buyColumn (str, optional): The column name for buying prices. The default is "ask_close".
        sellColumn (str, optional): The column name for selling prices. The default is "bid_open".

    Returns:
        tuple[pd.DataFrame, float, float]: A tuple containing the portfolio DataFrame,
        the value in terms of the quote token and the value in terms of the base token.

    """
    portfolio = data[(data["close"] > 0)]

    portfolio["trigger"] = portfolio["signal"].diff()

    # portfolio["current_signal"] = portfolio["trigger"].cumsum()
    portfolio["buy_signals"] = abs(
        portfolio["trigger"].where(portfolio["trigger"] == 1, 0)
    )
    portfolio["sell_signals"] = abs(
        portfolio["trigger"].where(portfolio["trigger"] == -1, 0)
    )
    portfolio["num_buy_signals"] = portfolio["buy_signals"].cumsum()
    portfolio["num_sell_signals"] = portfolio["sell_signals"].cumsum()

    # calculate the trigger based on the signal

    # if trigger is 1 then it is a buy signal, if its a buy signal then
    # use the ask_close price
    # calculate the buy spend
    portfolio["buy_spend"] = (portfolio["buy_signals"] * portfolio[buyColumn]).cumsum()
    # portfolio["long_credit"] = portfolio["buy_spend"] * .015

    # if the trigger is -1 then it is a sell signal, if its a sell signal then
    # use the bid_close price
    # calculate the sell spend
    portfolio["sell_spend"] = (
        portfolio["sell_signals"] * portfolio[sellColumn]
    ).cumsum()
    portfolio["holdings"] = portfolio["signal"] * portfolio[sellColumn]

    portfolio["quote_net_asset"] = (
        portfolio["holdings"] + portfolio["sell_spend"] - portfolio["buy_spend"]
    )
    portfolio["base_net_asset"] = portfolio["quote_net_asset"] / portfolio[sellColumn]
    portfolio["drawdown"] = (
        portfolio["quote_net_asset"] - portfolio["quote_net_asset"].cummax()
    )

    # check if the net asset is less than 0 this would mean that we have a loss
    # and that this is a bad signal
    result = any(np.where(portfolio["quote_net_asset"] < 0, False, True))

    return (
        portfolio,
        result,
        portfolio["quote_net_asset"].iloc[-1],
        portfolio["base_net_asset"].iloc[-1],
    )


def wma_ha_pipeline(
    data: pd.DataFrame,
    wmaSourceColumn: str = "ha_low",
    wmaPeriod: int = 20,
    buyColumn: str = "ha_ask_high",
    sellColumn: str = "ha_bid_low",
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
    buyColumn : str, optional
        The column name of the prices to use for buying. The default is "ask_open".
    sellColumn : str, optional
        The column name of the prices to use for selling. The default is "bid_open".

    Returns
    -------
    pd.DataFrame
        A DataFrame with the trading signals added.

    """
    data = heikin_ashi(data)
    data = wma(data, wmaPeriod, wmaSourceColumn)
    data = generate_signals(data, buyColumn, sellColumn)

    return data


def report(
    df: pd.DataFrame,
    result: bool,
    quote_net_asset: float,
    base_net_asset: float,
):
    """Print a report of the trading results.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the trading data.
    result : bool
        A boolean indicating if the trading strategy was successful.
    quote_net_asset : float
        The profit for the quote asset.
    base_net_asset : float
        The profit for the base asset.

    """
    df_orders_temp = df[df["trigger"] != 0]
    df_orders_temp.reset_index(inplace=True)
    df_orders = df_orders_temp[
        [
            "timestamp",
            "signal",
            "trigger",
            "wma",
            "ask_close",
            "bid_open",
        ]
    ]
    print(df_orders.tail(6).to_csv())
    print(
        f"result: {result} quote_net_asset: {quote_net_asset} base_net_asset: {base_net_asset}"
    )


def backtest(filename: str):
    """Process trading data from a CSV file to calculate Heikin-Ashi candlesticks and
    weighted moving average (wma).

    This function reads the trading data from a CSV file, processes it using the
    pipeline function, and generates trading signals.

    Parameters
    ----------
    filename : str
        The path to the CSV file containing the trading data.

    """  # noqa: D205
    df = pd.read_csv(
        filename,
        header=0,
        parse_dates=["timestamp"],
    )
    # signal using the ha_ask_open and ha_bid_close prices
    # signal and trigger interval could appears as this
    # 0 0 1 1 1 0 0 - 1 above or 0 below the wma
    # 0 0 1 0 0 -1 0 - diff gives actual trigger
    # that means that the price to open the trade at would be the open price
    # if we check that the open price is above the wma then we buy
    # the price to close the trade at would be the close price below the wma
    df = wma_ha_pipeline(df, "ha_low", 20, "ha_ask_open", "ha_bid_close")

    # calculate the portfolio:
    # When the trigger is 1, use the ask_open price (buy signal)
    # When the trigger is -1, it means the buy signal is no longer valid, and the bid_open price
    # at this point would be the same as the bid_close price at the previous point (where the signal
    # was 1)
    # since the closing price is trailing we can use the bid_open in the immediate
    # next row
    res = portfolio(df, "ask_open", "bid_open")

    # print the results
    report(*res)


def bot(token: str, instrument: str) -> None:
    """Continuously fetches OHLC data from Oanda, processes it, and reports trading results.

    This function establishes a connection to the Oanda API using the provided token and
    instrument. It enters an infinite loop where it fetches the latest OHLC data, processes
    it through a pipeline to generate trading signals, calculates the portfolio value,
    and prints a report of the trading results. The function handles exceptions during
    data fetching and retries after a short delay.

    Parameters
    ----------
    token : str
        The API token for authenticating with the Oanda service.
    instrument : str
        The financial instrument for which to fetch OHLC data.

    """
    ctx = v20.Context("api-fxpractice.oanda.com", token=token)
    while True:
        df: pd.DataFrame
        try:
            df = getOandaOHLC(ctx, instrument)
        except Exception as err:  # noqa: E722
            print(err)
            sleep(5)

        print(df.tail(1).to_csv())
        df = wma_ha_pipeline(df, "ha_low", 20, "ha_ask_open", "ha_bid_close")
        res = portfolio(df, "ask_open", "bid_open")
        # TODO: place orders or close orders
        report(*res)
        sleep(30)


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
    resp = ctx.instrument.candles(
        instrument=instrment,
        granularity="M5",
        fromTime=(datetime.now() - timedelta(days=2)).timestamp(),
        price="MAB",
    )
    if resp.body["candles"]:
        candles: v20.instrument.Candlesticks = resp.body["candles"]
        for i, candle in enumerate(candles):
            df.loc[i] = {
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

    return resp


if __name__ == "__main__":
    if "backtest" in sys.argv[1]:
        backtest(sys.argv[2])
    elif "bot":
        bot(sys.argv[1], sys.argv[2])
    else:
        print(sys.argv)
        print("""
            WMA HEIKEN ASHI
              Usage: 
                python main.py backtest <some csv file>
                python main.py bot <token> <instrument>
              """)
