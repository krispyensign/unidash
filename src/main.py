"""Main module."""
import logging
import sys

from backtest import backtest
from bot import bot

logger = logging.getLogger("main.py")



if __name__ == "__main__":
    if "backtest" in sys.argv[1]:
        logging.basicConfig(level=logging.DEBUG, filename="backtest.log")
        result = backtest(instrument=sys.argv[3], token=sys.argv[2])
        logger.info(result)
    elif "bot" in sys.argv[1]:
        logging.basicConfig(level=logging.DEBUG, filename="bot.log")
        bot(sys.argv[2], sys.argv[3], sys.argv[4], 1000)
    else:
        print(sys.argv)
        print("""
            WMA HEIKEN ASHI
              Usage: 
                python main.py backtest <some csv file>
                python main.py bot <token> <account_id> <instrument>
              """)
