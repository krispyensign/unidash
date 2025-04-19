"""Main module."""

import logging
import sys

import yaml

from bot.backtest import ChartConfig, SignalConfig, backtest
from bot.bot import TradeConfig, bot

logging.root.handlers = []


def get_logger(file_name: str):
    """Get logger for main module."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s|%(levelname)s|%(name)s|%(message)s",
        handlers=[logging.FileHandler(file_name), logging.StreamHandler()],
    )
    logger = logging.getLogger("main")
    numba_logger = logging.getLogger("numba")
    numba_logger.setLevel(logging.WARNING)
    return logger


if __name__ == "__main__":
    if "backtest" in sys.argv[1]:
        logger = get_logger("backtest.log")
        conf = yaml.safe_load(open(sys.argv[3]))
        chart_conf = ChartConfig(**conf["chart_config"])
        token = sys.argv[2]

        result = backtest(chart_conf, token=token)
        logger.info(result)
        if result is None:
            sys.exit(1)
    elif "bot" in sys.argv[1]:
        logger = get_logger("bot.log")
        token = sys.argv[2]
        account_id = sys.argv[3]
        conf = yaml.safe_load(open(sys.argv[4]))
        chart_conf = ChartConfig(**conf["chart_config"])
        signal_conf = SignalConfig(**conf["signal_config"])
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
