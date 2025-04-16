# MutantMarketBot

MutantMarketBot is a bot to perform signal generation and backtesting using WMA on different charts.

## NOTICE

This bot is being revised.

This is a homegrown application and does not replace perfectly valid trading
solutions already available. DO NOT USE WITHOUT FIRST TESTING YOURSELF.

This application is provided "AS IS" for educational purposes only.

## Current interim steps

```shell
cd src/py
pip install '.[dev]'

# i.e. for bot mode
main.py bot $YOUR_OANDA_TOKEN $YOUR_OANDA_ACCOUNT_ID USD_JPY

# i.e. for backtest mode
main.py backtest $YOUR_OANDA_TOKEN USD_JPY
```

## Future Work

Save OHLC data and various backtest scenarios to MS SQL
Using MS SQL for model prediction

## TODO

- [ ] dashboard to view current charts
- [ ] integration testing with Oanda sandbox
- [ ] save OHLC and results to ms sql using sqlalchemy
- [ ] asp.net service to periodically perform tasks
- [ ] embed python kernel pipeline(s) in ms sql
- [ ] perform backtests using ms sql
- [ ] mine data using ms sql predictive capabilities
