set ansi_nulls on
GO
set QUOTED_IDENTIFIER ON
go

create or alter PROCEDURE [dbo].[update_ohlchistory_from_staging]
(
    @token0 varchar(50),
    @token1 varchar(50)
)
AS
BEGIN

    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
    SET NOCOUNT ON;

    -- Insert statements for procedure here
    INSERT INTO [dbo].[ohlchistory]
           ([timestamp]
           ,[token0]
           ,[token1]
           ,[open]
           ,[high]
           ,[low]
           ,[close]
           ,[ask_open]
           ,[ask_high]
           ,[ask_low]
           ,[ask_close]
           ,[bid_open]
           ,[bid_high]
           ,[bid_low]
           ,[bid_close])
    SELECT convert( datetime, [timestamp])
      ,[token0]
      ,[token1] 
      ,convert(float,[open])
      ,convert(float,[high])
      ,convert(float,[low])
      ,convert(float,[close])
      ,convert(float,[ask_open])
      ,convert(float,[ask_high])
      ,convert(float,[ask_low])
      ,convert(float,[ask_close])
      ,convert(float,[bid_open])
      ,convert(float,[bid_high])
      ,convert(float,[bid_low])
      ,convert(float,[bid_close])
    FROM [dbo].[ohlcstaging]
    WHERE [token0] = @token0 AND [token1] = @token1;

END
go

exec dbo.update_ohlchistory_from_staging @token0 = 'HKD', @token1 = 'JPY'
go

exec dbo.update_ohlchistory_from_staging @token0 = 'USD', @token1 = 'JPY'
go