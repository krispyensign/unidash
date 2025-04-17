"""Bot that trades on Oanda."""

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from time import sleep
import v20  # type: ignore

from bot.backtest import ChartConfig, PerfTimer, Record, SignalConfig
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


@dataclass
class TradeConfig:
    """Configuration for the bot."""

    amount: float


def bot_run(
    ctx: OandaContext, signal_conf: SignalConfig, chart_conf: ChartConfig, amount: float
) -> tuple[int, Exception | None]:
    """Run the bot."""
    try:
        trade_id = get_open_trade(ctx)
        df = getOandaOHLC(
            ctx, count=chart_conf.candle_count, granularity=chart_conf.granularity
        )
    except Exception as err:
        return -1, err

    kernel_conf = KernelConfig(
        signal_buy_column=signal_conf.signal_buy_column,
        signal_exit_column=signal_conf.signal_exit_column,
        source_column=signal_conf.source_column,
        wma_period=chart_conf.wma_period,
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
        report(df, signal_conf.signal_buy_column, signal_conf.signal_exit_column)
        assert trade_id == -1, "trades should not be open"

    # print the results
    report(df, signal_conf.signal_buy_column, signal_conf.signal_exit_column)

    return trade_id, None


def bot(
    token: str,
    account_id: str,
    chart_conf: ChartConfig,
    signal_conf: SignalConfig,
    trade_conf: TradeConfig,
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
    chart_conf : ChartConfig
        The chart configuration.
    signal_conf : SignalConfig
        The signal configuration.
    trade_conf : TradeConfig
        The trade configuration.

    """
    logger.info("starting bot.")

    ctx = OandaContext(
        ctx=v20.Context("api-fxpractice.oanda.com", token=token),
        account_id=account_id,
        token=token,
        instrument=chart_conf.instrument,
    )

    while True:
        with PerfTimer(APP_START_TIME, logger):
            trade_id, err = bot_run(
                ctx, signal_conf, chart_conf=chart_conf, amount=trade_conf.amount
            )
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
