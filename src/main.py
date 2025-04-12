"""Main module."""

import logging
import sys

from backtest import backtest
from bot import bot

logging.root.handlers = []

if __name__ == "__main__":
    if "backtest" in sys.argv[1]:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s|%(levelname)s|%(name)s|%(message)s",
            handlers=[logging.FileHandler("backtest.log"), logging.StreamHandler()],
        )
        logger = logging.getLogger("main")
        result = backtest(instrument=sys.argv[3], token=sys.argv[2])
        logger.info("so:%s sib:%s sie:%s", result[0], result[1], result[2])
    elif "bot" in sys.argv[1]:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s|%(levelname)s|%(name)s|%(message)s",
            handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
        )
        logger = logging.getLogger("main")
        bot(sys.argv[2], sys.argv[3], sys.argv[4], 1000)
    else:
        print(sys.argv)
        print("""
            WMA HEIKEN ASHI
              Usage: 
                python main.py backtest <some csv file>
                python main.py bot <token> <account_id> <instrument>
              """)
