import pandas as pd


def portfolio(data: pd.DataFrame, initial: float = 1) -> pd.DataFrame:
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
    print("buy count", data["position"].value_counts()[1])
    print("sell count", data["position"].value_counts()[-1])

    portfolio=pd.DataFrame()
    ratio = initial/data.loc[0, 'open']
    print("ratio",ratio)
    portfolio['holdings']=data['position']*data['close']*ratio
    portfolio['cash']=initial-(data['position']*data['close']*ratio).cumsum()
    portfolio['total asset']=portfolio['holdings']+portfolio['cash']
    portfolio['profit']=portfolio['total asset']-initial
    portfolio['return']=portfolio['total asset'].pct_change()
    portfolio['position']=data['position']
    portfolio['timestamp']=data['timestamp']
    portfolio.set_index('timestamp',inplace=True)
    return portfolio



portfolio
