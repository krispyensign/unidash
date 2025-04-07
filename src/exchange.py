"""Get OHLC data from an exchange and convert it into a pandas DataFrame."""

from datetime import datetime, timedelta
import v20 # type: ignore
import pandas as pd

Thursday = 4


def getOandaBalance(ctx: v20.Context, account_id: str) -> float:
    """Get the current balance from Oanda.

    Parameters
    ----------
    ctx : v20.Context
        The Oanda API context.
    account_id : str
        The account ID associated with the Oanda account.

    Returns
    -------
    float
        The current balance in the Oanda account.

    """
    resp = ctx.account.get(account_id)
    if resp.body["account"]:
        account: v20.account.Account = resp.body["account"]
        return account.balance

    return 0


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
            "atr",
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


def place_order(
    ctx: v20.Context, account_id: str, instrument: str, amount: float
) -> int:
    """Place an order on the Oanda API.

    Parameters
    ----------
    ctx : v20.Context
        The Oanda API context.
    account_id : str
        The account ID associated with the Oanda account.
    instrument : str
        The instrument to place the order on.
    direction : str
        The direction of the order, either "buy" or "sell".
    amount : float
        The amount of the instrument to buy or sell.

    Returns
    -------
    int
        The order ID of the placed order.

    """
    # place the order
    order: v20.order.MarketOrder = v20.order.MarketOrder(
        instrument=instrument,
        units=amount,
        trailingStopLossOnFill=v20.transaction.TrailingStopLossDetails(distance=0.5),
    )
    resp = ctx.order.create(
        account_id,
        order=order,
    )

    # get the trade id from the response body and return it if it exists
    trade_id: int
    if resp.body is not None:
        if "orderFillTransaction" in resp.body:
            result: v20.transaction.OrderFillTransaction = resp.body[
                "orderFillTransaction"
            ]
            trade: v20.trade.TradeOpen = result.tradeOpened
            trade_id = trade.tradeID
        elif "orderCancelTransaction" in resp.body:
            raise Exception(resp.body["orderCancelTransaction"])
        elif "orderRejectTransaction" in resp.body:
            raise Exception(resp.body["orderRejectTransaction"])
    else:
        raise Exception("No response body")

    return trade_id


def close_order(ctx: v20.Context, account_id: str, trade_id: int) -> None:
    """Close an order on the Oanda API.

    Parameters
    ----------
    ctx : v20.Context
        The Oanda API context.
    account_id : str
        The account ID associated with the Oanda account.
    trade_id : str
        The trade ID of the order to close.

    """
    resp = ctx.order.cancel(account_id, trade_id)

    if resp.body is not None:
        if "orderRejectTransaction" in resp.body:
            raise Exception(resp.body["orderRejectTransaction"])
