"""Main module."""

import logging
import sys

import yaml

from bot.backtest import ChartConfig, backtest
from bot.bot import TradeConfig, bot
import cProfile
import pstats

from core.kernel import KernelConfig

logging.root.handlers = []


def get_logger(file_name: str):
    """Get logger for main module."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s|%(levelname)s|%(name)s|%(message)s",
        handlers=[logging.FileHandler(file_name), logging.StreamHandler()],
    )
    logger = logging.getLogger()
    numba_logger = logging.getLogger('numba')
    numba_logger.setLevel(logging.WARNING)
    return logger


if __name__ == "__main__":
    if "backtest" in sys.argv[1]:
        logger = get_logger("backtest.log")
        conf = yaml.safe_load(open(sys.argv[3]))
        chart_conf = ChartConfig(**conf["chart_config"])
        token = sys.argv[2]

        profiler = cProfile.Profile()
        profiler.enable()
        try:
            result = backtest(chart_conf, token=token)
        except KeyboardInterrupt:
            profiler.disable()
            stats = pstats.Stats(profiler)
            stats.sort_stats("cumtime")
            stats.print_stats(100)
            sys.exit(0)

        logger.info(result)
        if result is None:
            sys.exit(1)
    elif "bot" in sys.argv[1]:
        logger = get_logger("bot.log")
        token = sys.argv[2]
        account_id = sys.argv[3]
        conf = yaml.safe_load(open(sys.argv[4]))
        chart_conf = ChartConfig(**conf["chart_config"])
        signal_conf = KernelConfig(**conf["signal_config"])
        trade_conf = TradeConfig(**conf["trade_config"])
        bot(
            token=token,
            account_id=account_id,
            chart_conf=chart_conf,
            signal_conf=signal_conf,
            trade_conf=trade_conf,
        )
    else:
        print(sys.argv)
        print("""
            MutantMakerBot
              Usage: 
                python main.py backtest <token> <my_config>.yaml
                python main.py bot <token> <account_id> <my_config>.yaml
              """)
