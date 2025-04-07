# Unidash

Perform signal generation and backtesting using WMA and Heiken Ashi.

## WARNING

This is being revised and currently does not work as originally intended and only
works with Oanda FOREX.  

This is a homegrown application and does not replace perfectly valid trading
solutions already available. DO NOT USE WITHOUT FIRST TESTING YOURSELF.
Per section 7 of the license:

```text
   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.
```

This application is provided "AS IS" for educational purposes only.

## Current interim steps

```shell
cd src/py
pip install .

# i.e. for bot mode
main.py bot $YOUR_OANDA_TOKEN $YOUR_OANDA_ACCOUNT_ID USD_JPY

# i.e. for backtest mode
main.py backtest some_file.csv
```

## Results

Currently it does appear it could result in a profit as described in the article
[Best Indicators For Day Trading](https://www.liberatedstocktrader.com/best-indicators-for-day-trading/#wma)

## Future Work

Save OHLC data and various backtest scenarios to MS SQL
Using MS SQL for model prediction

## TODO

- [X] automated trading using python
- [X] logging
- [X] trailing stop loss
- [X] close open trades when signal is 0
- [ ] integration testing with Oanda sandbox
- [X] tune ATR
- [ ] save OHLC and results to ms sql using sqlalchemy
- [X] remove all unused typescript code
- [ ] asp.net service to periodically perform tasks
- [ ] embed python wma-ha pipeline(s) in ms sql
- [ ] perform backtests using ms sql
- [ ] mine data using ms sql predictive capabilities
