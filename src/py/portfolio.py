import pandas as pd


def portfolio(data: pd.DataFrame) -> tuple[pd.DataFrame, float, float]:
    """
    Calculate the portfolio value based on a DataFrame of OHLC data.

    Args:
        data (pd.DataFrame): A DataFrame containing OHLC data.

    Returns:
        tuple[pd.DataFrame, float, float]: A tuple containing the portfolio DataFrame,
        the value in terms of the quote token and the value in terms of the base token.
    """

    portfolio=pd.DataFrame()

    portfolio['timestamp']=data['timestamp']

    # if position is 1 then it is a buy signal, if its a buy signal then
    # use the ask_close price
    # if the position is -1 then it is a sell signal, if its a sell signal then
    # use the bid_close price
    portfolio['buy signals'] = abs(data['position'].where(data['position'] == 1, 0))
    portfolio['sell signals'] = abs(data['position'].where(data['position'] == -1, 0))
    portfolio['buy spend']=(portfolio['buy signals']*data['ask_close']).cumsum()
    portfolio['sell spend']=(portfolio['sell signals']*data['bid_close']).cumsum()
    
    portfolio['quote net asset']=portfolio['sell spend']-portfolio['buy spend']
    portfolio['base net asset']=(portfolio['quote net asset']/data['bid_close'])
    portfolio['bid_close']=data['bid_close']
    portfolio['ask_close']=data['ask_close']

    portfolio.set_index('timestamp',inplace=True)

    return portfolio, portfolio['quote net asset'].iloc[-1], portfolio['base net asset'].iloc[-1]


portfolio
