"""Get OHLC data from an exchange and convert it into a pandas DataFrame."""

import v20  # type: ignore
import pandas as pd
import logging

Thursday = 4


logger = logging.getLogger("exchange.py")


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


def getOandaOHLC(
    ctx: v20.Context, instrment: str, granularity: str = "M5", count: int = 288
) -> pd.DataFrame:
    # create dataframe with candles
    """Get OHLC data from Oanda and convert it into a pandas DataFrame.

    Parameters
    ----------
    ctx : v20.Context
        The Oanda API context.
    instrment : str
        The instrument to get the OHLC data for.
    granularity : str, optional
        The granularity of the OHLC data, by default "M5".
    count : int, optional
        The number of candles to get, by default 288.

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

    resp = ctx.instrument.candles(
        instrument=instrment,
        granularity=granularity,
        price="MAB",
        count=count,
    )
    if resp.body["candles"]:
        candles: v20.instrument.Candlesticks = resp.body["candles"]
        candle: v20.instrument.Candlestick
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


def place_order(  # noqa: PLR0913
    ctx: v20.Context,
    account_id: str,
    instrument: str,
    amount: float,
    take_profit: float,
    trailing_distance: float,
    stop_loss: float,
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
    take_profit : float
        The take profit price for the order.
    stop_loss : float
        The stop loss price for the order.
    trailing_distance : float
        The trailing distance for the order.

    Returns
    -------
    int
        The order ID of the placed order.

    """
    # place the order
    decimals = 5
    if instrument.split("_")[1] == "JPY":
        decimals = 3

    order: v20.order.MarketOrder = v20.order.MarketOrder(
        instrument=instrument,
        units=amount,
        takeProfitOnFill=v20.transaction.TakeProfitDetails(
            price=f"{round(take_profit, decimals)}"
        ),
        trailingStopLossOnFill=v20.transaction.TrailingStopLossDetails(
            distance=f"{round(trailing_distance + 0.01, decimals)}",
        ),
        # stopLossOnFill=v20.transaction.StopLossDetails(
        #     price=f"{round(stop_loss, decimals)}"
        # ),
    )
    logger.info(order.json())
    resp = ctx.order.create(
        account_id,
        order=order,
    )

    # get the trade id from the response body and return it if it exists
    trade_id: int
    if resp.body is not None and "orderFillTransaction" in resp.body:
        result: v20.transaction.OrderFillTransaction = resp.body["orderFillTransaction"]
        trade: v20.trade.TradeOpen = result.tradeOpened
        trade_id = trade.tradeID
    else:
        if resp.body is not None and "orderRejectTransaction" in resp.body:
            reject_result: v20.transaction.MarketOrderRejectTransaction = resp.body[
                "orderRejectTransaction"
            ]
            logger.error(reject_result.summary())
            logger.error(reject_result.json())
            raise Exception(reject_result.reason)

        raise Exception(resp.body.__str__())

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
    resp = ctx.trade.close(account_id, trade_id)

    if resp.body is not None:
        if "orderRejectTransaction" in resp.body:
            raise Exception(resp.body.to_json())


def get_open_trades(ctx: v20.Context, account_id: str) -> int:
    """Get the open trades from the Oanda API.

    Parameters
    ----------
    ctx : v20.Context
        The Oanda API context.
    account_id : str
        The account ID associated with the Oanda account.

    Returns
    -------
    int
        The trade ID of the first open trade.

    """
    resp = ctx.trade.list_open(account_id)
    trades: list[v20.trade.Trade] = []
    if resp.body is not None:
        if "trades" in resp.body:
            trades = resp.body["trades"]
            if len(trades) > 0:
                return trades[0].id

    return -1
