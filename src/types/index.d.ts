export type RawSwap = {
  timestamp: string
  id: string
  amount0: string
  amount1: string
}

export type Data = {
  swaps: RawSwap[]
}

export type Swap = {
  timestamp: number
  swapId: string
  amount0: number
  amount1: number
  token0: string
  token1: string
}

export type DataFrame = {
  copy(): DataFrame
  set_index(column: string): DataFrame
  head(count?: number): DataFrame
  tail(count?: number): DataFrame
  to_json(): string
  to_csv(): string
}

export type TestStrategy =
  | 'WMA_HEIKEN_ASHI'
  | 'IWMA_HEIKEN_ASHI'
  | 'WMA_HEIKEN_ASHI_INVERSE'
  | 'IWMA_HEIKEN_ASHI_INVERSE'
  | 'WMA_OHLC'
  | 'IWMA_OHLC'
  | 'WMA_OHLC_INVERSE'
  | 'IWMA_OHLC_INVERSE'

export type ColumnNames =
  | 'open'
  | 'close'
  | 'high'
  | 'low'
  | 'ha_open'
  | 'ha_close'
  | 'ha_high'
  | 'ha_low'
  | 'ha_bid_open'
  | 'ha_bid_close'
  | 'ha_bid_high'
  | 'ha_bid_low'
  | 'ha_ask_open'
  | 'ha_ask_close'
  | 'ha_ask_high'
  | 'ha_ask_low'
  | 'ask_open'
  | 'ask_close'
  | 'ask_high'
  | 'ask_low'
  | 'bid_open'
  | 'bid_close'
  | 'bid_high'
  | 'bid_low'

export type Token =
  | '0x4200000000000000000000000000000000000006'
  | '0x570b1533F6dAa82814B25B62B5c7c4c55eB83947'

export type TestSet = {
  signalColumnIn: string
  wmaColumnIn: string
  testStrategy: TestStrategy
}

export type Portfolio = {
  timestamp: number
  amount: number
  value: number
  base_value: number
  inverted: boolean
}

export type wmaFunc = {
  kind: 'wma'
  (df: DataFrame, period: number, column: string): DataFrame
}
export type iwmaFunc = {
  kind: 'iwma'
  (df: DataFrame, period: number, column: string): DataFrame
}
export type signalCompareFunc = {
  kind: 'signal_compare'
  (df: DataFrame, column0: string, column1: string): DataFrame
}

export type ohlcFunc = {
  kind: 'ohlc'
  (dataIn: DataFrame, timeFrame: string): DataFrame
}

export type heikenFunc = {
  kind: 'heiken_ashi'
  (dataIn: DataFrame): DataFrame
}
export type portfolioFunc = {
  kind: 'portfolio'
  (dataIn: DataFrame): [DataFrame, boolean, number, number]
}

export type TradingIndicator = {
  wma: wmaFunc
  iwma: iwmaFunc
  signal_compare: signalCompareFunc
}

export type TradingChart = {
  ohlc: ohlcFunc
  heiken: heikenFunc
}

export type TradingUtil = {
  portfolio: portfolioFunc
}

export type PythonFunc =
  | ohlcFunc
  | wmaFunc
  | iwmaFunc
  | signalCompareFunc
  | heikenFunc
  | portfolioFunc
