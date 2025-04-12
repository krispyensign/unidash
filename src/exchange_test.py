import v20


def test_open_order():
    atr = 0.1128
    ctx = v20.Context("api-fxpractice.oanda.com", "asdf")
    order: v20.order.MarketOrder = v20.order.MarketOrder(
        instrument="USD_JPY",
        units=100,
        takeProfitOnFill=v20.transaction.TakeProfitDetails(price=f"{take_profit}"),
        trailingStopLossOnFill=v20.transaction.TrailingStopLossDetails(
            distance=f"{round(atr, 2)}"
        ),
    )
    resp = ctx.order.create(
        account_id,
        order=order,
    )
