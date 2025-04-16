"""Bot that trades on Oanda."""

from datetime import datetime, timedelta
import logging
from time import sleep
import v20  # type: ignore

from bot.backtest import PerfTimer, Record, SignalConfig, backtest
from bot.config import (
    BACKTEST_COUNT,
    ENTRY_COLUMN,
    EXIT_COLUMN,
    GRANULARITY,
    WMA_PERIOD,
)
from core.kernel import KernelConfig, kernel
from bot.reporting import report
from bot.exchange import (
    close_order,
    get_open_trade,
    getOandaOHLC,
    place_order,
    OandaContext,
)

logger = logging.getLogger("bot")
APP_START_TIME = datetime.now()


def bot_run(
    ctx: OandaContext, signal_conf: SignalConfig, amount: float
) -> tuple[int, Exception | None]:
    """Run the bot."""
    try:
        trade_id = get_open_trade(ctx)
        df = getOandaOHLC(ctx, count=BACKTEST_COUNT, granularity=GRANULARITY)
    except Exception as err:
        return -1, err

    kernel_conf = KernelConfig(
        signal_buy_column=signal_conf.signal_buy_column,
        source_column=signal_conf.source_column,
        entry_column=ENTRY_COLUMN,
        exit_column=EXIT_COLUMN,
        wma_period=WMA_PERIOD,
        stop_loss=signal_conf.trailing_stop,
        take_profit=signal_conf.take_profit,
    )
    df = kernel(
        df,
        include_incomplete=False,
        config=kernel_conf,
    )
    rec = Record(
        signal=df["signal"].iloc[-1],
        trigger=df["trigger"].iloc[-1],
        losses=df["losses"].iloc[-1],
        wins=df["wins"].iloc[-1],
        exit_total=df["exit_total"].iloc[-1],
        min_exit_total=df["min_exit_total"].iloc[-1],
    )

    if rec.trigger == 1 and trade_id == -1:
        try:
            trade_id = place_order(
                ctx,
                amount,
            )

        except Exception as err:
            return -1, err

    if rec.trigger == -1 and trade_id != -1:
        try:
            close_order(ctx, trade_id)
        except Exception as err:
            return trade_id, err

    if rec.trigger == 0 and rec.signal == 0 and trade_id != -1:
        close_order(ctx, trade_id)
        report(df, signal_conf.signal_buy_column, ENTRY_COLUMN, EXIT_COLUMN)
        assert trade_id == -1, "trades should not be open"

    # print the results
    report(df, signal_conf.signal_buy_column, ENTRY_COLUMN, EXIT_COLUMN)

    return trade_id, None


def bot(token: str, account_id: str, instrument: str, amount: float) -> None:
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
    signal_conf = backtest(
        instrument=instrument,
        token=token,
    )
    if signal_conf is None:
        logger.error("no signals found.")
        return

    logger.info("starting bot.")

    ctx = OandaContext(
        ctx=v20.Context("api-fxpractice.oanda.com", token=token),
        account_id=account_id,
        token=token,
        instrument=instrument,
    )

    while True:
        with PerfTimer(APP_START_TIME):
            trade_id, err = bot_run(ctx, signal_conf, amount)
            if err is not None:
                logger.error(err)
                sleep(5)
                continue

            logger.info(f"columns used: {signal_conf}")
            logger.info(f"trade id: {trade_id}") if trade_id == -1 else None

            sleep_until_next_5_minute(trade_id=trade_id)


def roundUp(dt):
    """Round a datetime object to the next 5 minute interval."""
    return (dt + timedelta(minutes=5 - dt.minute % 5)).replace(second=1, microsecond=0)


def sleep_until_next_5_minute(trade_id: int = -1):
    """Sleep until the next 5 minute interval."""
    now = datetime.now()
    next_time = roundUp(now)
    if (next_time - now) < timedelta(seconds=1):
        next_time = next_time + timedelta(minutes=5)
    logger.info(
        "sleeping until next 5 minute interval %s",
        next_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
    )
    sleep((next_time - now).total_seconds())
