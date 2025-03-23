import pandas as pd


def portfolio(data: pd.DataFrame, initial: float = 1) -> tuple[pd.DataFrame, float]:
    """
    Calculate the portfolio value based on a DataFrame of OHLC data.

    Args:
        data (pd.DataFrame): A DataFrame containing OHLC data.
    """

    # given a data frame with a signal that is 1 for buy and 0 for sell and a
    # position of 1 for buy, -1 for sell and 0 for no action
    # calculate the assets, the remaining capital, and the total value

    #cumsum column is created to check the holding of the position
    data['cumsum']=data['position'].cumsum()

    # count number of buy signals in position

    portfolio=pd.DataFrame()
    ratio = initial/data.loc[0, 'open']
    print("ratio",ratio)
    portfolio['holdings']=data['position']*data['close']*ratio
    portfolio['cash']=initial-(data['position']*data['close']*ratio).cumsum()
    portfolio['total asset']=portfolio['holdings']+portfolio['cash']
    portfolio['profit']=portfolio['total asset']-initial
    portfolio['timestamp']=data['timestamp']
    portfolio['buy count']=data["position"].value_counts()[1]
    portfolio['sell count']=data["position"].value_counts()[-1]
    portfolio.set_index('timestamp',inplace=True)
    return [portfolio, portfolio['profit'].iloc[-1]/initial]


portfolio
