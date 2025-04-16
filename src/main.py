"""Main module."""

import logging
import sys

from bot.backtest import backtest
from bot.bot import bot

logging.root.handlers = []


def get_logger(file_name: str):
    """Get logger for main module."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s|%(levelname)s|%(name)s|%(message)s",
        handlers=[logging.FileHandler(file_name), logging.StreamHandler()],
    )
    logger = logging.getLogger("main")
    return logger


if __name__ == "__main__":
    if "backtest" in sys.argv[1]:
        logger = get_logger("backtest.log")
        result = backtest(instrument=sys.argv[3], token=sys.argv[2])
        logger.info(result)
        if result is None:
            sys.exit(1)
    elif "bot" in sys.argv[1]:
        logger = get_logger("bot.log")
        bot(sys.argv[2], sys.argv[3], sys.argv[4], 1000)
    else:
        print(sys.argv)
        print("""
            MutantMakerBot
              Usage: 
                python main.py backtest <token> <instrument>
                python main.py bot <token> <account_id> <instrument>
              """)
