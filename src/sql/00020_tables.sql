if exists (select name from sys.tables where name = N'ohlchistory')
    drop table [dbo].[ohlchistory];

if not exists (select name from sys.tables where name = N'ohlchistory')
    create table [dbo].[ohlchistory] (
        id INT IDENTITY (1, 1) NOT NULL PRIMARY KEY,
        [token0] [varchar](50) NOT NULL,
        [token1] [varchar](50) NOT NULL,
        [timestamp] [datetime] NOT NULL,
        [open] [float] NOT NULL,
        [high] [float] NOT NULL,
        [low] [float] NOT NULL,
        [close] [float] NOT NULL,
        [ask_open] [float] NOT NULL,
        [ask_high] [float] NOT NULL,
        [ask_low] [float] NOT NULL,
        [ask_close] [float] NOT NULL,
        [bid_open] [float] NOT NULL,
        [bid_high] [float] NOT NULL,
        [bid_low] [float] NOT NULL,
        [bid_close] [float] NOT NULL,
    );

if exists (select name from sys.tables where name = N'ohlcstaging')
    DROP TABLE [dbo].[ohlcstaging];

if not exists (select name from sys.tables where name = N'ohlcstaging')
    create table [dbo].[ohlcstaging] (
        [timestamp] [varchar](50) NOT NULL,
        [_id] [varchar](50) NOT NULL,
        [token0] [varchar](50) NOT NULL,
        [token1] [varchar](50) NOT NULL,
        [open] [varchar](50) NOT NULL,
        [high] [varchar](50) NOT NULL,
        [low] [varchar](50) NOT NULL,
        [close] [varchar](50) NOT NULL,
        [ask_open] [varchar](50) NOT NULL,
        [ask_high] [varchar](50) NOT NULL,
        [ask_low] [varchar](50) NOT NULL,
        [ask_close] [varchar](50) NOT NULL,
        [bid_open] [varchar](50) NOT NULL,
        [bid_high] [varchar](50) NOT NULL,
        [bid_low] [varchar](50) NOT NULL,
        [bid_close] [varchar](50) NOT NULL,
    );

bulk insert [dbo].[ohlcstaging] 
from '/datasets/usdjpy_chart.csv'
with (firstrow = 2, format = 'csv', fieldterminator = ',', rowterminator = '\n');

bulk insert [dbo].[ohlcstaging] 
from '/datasets/hkdjpy_chart.csv'
with (firstrow = 2, format = 'csv', fieldterminator = ',', rowterminator = '\n');