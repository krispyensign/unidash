"""Main module."""

from datetime import datetime
import sys
from time import sleep
import pandas as pd
import numpy as np
import talib
import v20  # type: ignore

from exchange import close_order, getOandaOHLC, getOandaBalance, place_order
from pipeline import wma_ha


Thursday = 4
WMA_PERIOD = 20


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

    # check if the Heikin-Ashi high is greater than the wma
    df.loc[df[buyColumn] > df["wma"], "signal"] = 1
    df["trigger"] = df["signal"].diff()

    # check if the Heikin-Ashi low is less than the wma and the trigger is not 1
    df.loc[(df[sellColumn] < df["wma"]) & (df["trigger"] != 1), "signal"] = 0

    df["trigger"] = df["signal"].diff()

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

    # set the trailing stop loss
    portfolio["trailing_stop_loss"] = (
        portfolio[portfolio["signal"] == 1]
        .groupby((portfolio["signal"] == 1).cumsum())["high"]
        .transform(lambda x: x.rolling(window=len(x)).max())
        - portfolio["atr"]
    )
    # set the signal to 0 if the trailing stop loss is less than the bid close
    portfolio["ts_signal"] = portfolio["signal"].copy()
    portfolio.loc[(portfolio["bid_close"] < portfolio["trailing_stop_loss"]) & (portfolio["trigger"] != 1), "ts_signal"] = 0
    portfolio["ts_trigger"] = portfolio["ts_signal"].diff()

    # portfolio["current_signal"] = portfolio["ts_trigger"].cumsum()
    portfolio["buy_signals"] = abs(
        portfolio["ts_trigger"].where(portfolio["ts_trigger"] == 1, 0)
    )
    portfolio["sell_signals"] = abs(
        portfolio["ts_trigger"].where(portfolio["ts_trigger"] == -1, 0)
    )
    portfolio["num_buy_signals"] = portfolio["buy_signals"].cumsum()
    portfolio["num_sell_signals"] = portfolio["sell_signals"].cumsum()

    # calculate the trigger based on the signal

    # if trigger is 1 then it is a buy signal, if its a buy signal then
    # use the ask_close price
    # calculate the buy spend
    portfolio["buy_spend"] = (portfolio["buy_signals"] * portfolio[buyColumn]).cumsum()

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


def report(
    df: pd.DataFrame,
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
    df_ticks = df[
        [
            "signal",
            "trigger",
            "quote_net_asset",
            "wma",
            "atr",
            "ha_ask_open",
            "ha_bid_close",
            "ask_close",
            "bid_open",
        ]
    ]
    df_ticks.reset_index(inplace=True)
    df_orders = df_ticks[df_ticks["trigger"] != 0]
    print("last 6 trades")
    print(df_orders.tail(6).round(3).to_csv())
    print("current status")
    print(df_ticks.tail(1).round(3).to_csv())


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

    res = kernel(df)

    report(res[0])


def kernel(df: pd.DataFrame) -> tuple[pd.DataFrame, bool, float, float]:
    """Process a DataFrame containing trading data.

    This function processes a DataFrame containing trading data and generate trading signals
    using Heikin-Ashi candlesticks and weighted moving average (wma).

    TODO: support pipelines other than wma_ha

    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame containing trading data.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the trading signals and portfolio calculations.

    """
    # calculate the ATR and multiply it by .5 for the trailing stop loss
    df["atr"] = (
        talib.ATR(
            df["high"].to_numpy(),
            df["low"].to_numpy(),
            df["close"].to_numpy(),
            timeperiod=WMA_PERIOD,
        )
    )

    # signal using the ha_ask_open and ha_bid_close prices
    # signal and trigger interval could appears as this
    # 0 0 1 1 1 0 0 - 1 above or 0 below the wma
    # 0 0 1 0 0 -1 0 - diff gives actual trigger
    # that means that the price to open the trade at would be the open price
    # if we check that the open price is above the wma then we buy
    # the price to close the trade at would be the close price below the wma
    df = wma_ha(df, "ha_low", WMA_PERIOD)
    df = generate_signals(df, "ha_ask_open", "ha_bid_close")

    # calculate the portfolio:
    # When the trigger is 1, use the ask_open price (buy signal)
    # When the trigger is -1, it means the buy signal is no longer valid, and the bid_open price
    # at this point would be the same as the bid_close price at the previous point (where the signal
    # was 1)
    # since the closing price is trailing we can use the bid_open in the immediate
    # next row
    res = portfolio(df, "ask_open", "bid_open")

    return res


def bot(
    token: str, account_id: str, instrument: str, amount: float | None = None
) -> None:
    """Bot that trades on Oanda.

    This function trades on Oanda using the Oanda API. It places market orders based on the
    trading signals generated by the kernel function.  It closes the trade when the trigger is -1.

    Parameters
    ----------
    token : str
        The Oanda API token.
    account_id : str
        The Oanda account ID.
    instrument : str
        The instrument to trade.
    amount : float | None
        The amount to trade. If None, the bot will calculate the amount based
        on the current balance.

    """
    ctx = v20.Context("api-fxpractice.oanda.com", token=token)
    trade_id = -1
    while True:
        df: pd.DataFrame
        startTime = datetime.now()
        try:
            df = getOandaOHLC(ctx, instrument)
            print(df.head(1).round(3).to_csv())
            print(df.tail(1).round(3).to_csv())
        except Exception as err:  # noqa: E722
            print(err)
            sleep(5)
            continue

        res = kernel(df)
        df = res[0]
        closeout_risk = res[1]

        quote_net_asset = df["quote_net_asset"].iloc[-1]
        if quote_net_asset < 0:
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} losing money {quote_net_asset}",
            )
            report(res[0])
            sleep(300)
            continue
        if closeout_risk:
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} closeout risk {quote_net_asset}"
            )

        trigger = df["trigger"].iloc[-1]
        signal = df["signal"].iloc[-1]
        if trigger != 0:
            if trigger == 1 and trade_id == -1:
                try:
                    if amount is None:
                        balance = getOandaBalance(ctx, account_id)
                        amount = (balance // 2 + 1) * 50
                    trade_id = place_order(ctx, account_id, instrument, amount)
                except Exception as err:
                    print(err)
                    sleep(5)
                    continue

            elif trigger == -1 and trade_id != -1:
                try:
                    close_order(ctx, account_id, trade_id)
                    trade_id = -1
                except Exception as err:
                    print(err)
                    sleep(5)
                    continue
        elif trigger == 0 and signal == 0 and trade_id != -1:
            try:
                close_order(ctx, account_id, trade_id)
                trade_id = -1
            except Exception as err:
                print(err)
                sleep(30)
                continue

        endTime = datetime.now()
        print(f"runtime: {endTime - startTime}")
        # print the results
        report(res[0])
        sleep(15)


if __name__ == "__main__":
    if "backtest" in sys.argv[1]:
        backtest(sys.argv[2])
    elif "bot":
        bot(sys.argv[1], sys.argv[2], sys.argv[3], 1000)
    else:
        print(sys.argv)
        print("""
            WMA HEIKEN ASHI
              Usage: 
                python main.py backtest <some csv file>
                python main.py bot <token> <account_id> <instrument>
              """)
