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
  amount0: string
  amount1: string
  token0: string
  token1: string
}

export type DataFrame = {
  copy(): DataFrame
  set_index(column: string): DataFrame
  reset_index(): DataFrame
  sort_index(): DataFrame
  drop_duplicates(): DataFrame
  head(count?: number): DataFrame
  tail(count?: number): DataFrame
  to_json(): string
  to_csv(): string
  callKwargs<T, U>(call: string, args: U): T
}

export type ChartDatasource = 'uniswap' | 'oanda'

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

export type Token = string

export type TestSet = {
  signalColumnIn: string
  wmaColumnIn: string
  testStrategy: TestStrategy
  period: number
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
  (dataIn: DataFrame, timeFrame: string, isSwapped: boolean): [DataFrame, string]
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

export interface Arguments {
  [x: string]: unknown
  token0: string
  token1: string
  tokenSwap: boolean
  graphqlEndpoint: string | undefined
  oandaEndpoint: string | undefined
  oandaAPIKey: string | undefined
  chartDatasource: string
  mongodbEndpoint: string
  daysToFetch: number
  offset: number
  heartbeat: string | undefined
  priority: string | undefined
  strategyWmaColumn: string | undefined
  strategySignalColumn: string | undefined
  strategyName: string | undefined
  strategyWmaPeriod: number
  chartSaveFile: string | undefined
}

export type OHLC = {
  timestamp: number
  token0: string
  token1: string
  open: number
  high: number
  low: number
  close: number
  bid_open: number
  bid_high: number
  bid_low: number
  bid_close: number
  ask_open: number
  ask_high: number
  ask_low: number
  ask_close: number
}

export type OandaCandle = {
  time: string
  bid: {
    o: number
    h: number
    l: number
    c: number
  }
  ask: {
    o: number
    h: number
    l: number
    c: number
  }
  mid: {
    o: number
    h: number
    l: number
    c: number
  }
  volume: number
  complete: boolean
}

export type PortfolioRecord = {
  _id: string
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  ha_close: number
  ask_close: number
  bid_close: number
  ha_open: number
  ask_open: number
  bid_open: number
  ha_high: number
  ask_high: number
  bid_high: number
  ha_low: number
  ask_low: number
  bid_low: number
  wma: number
  iwma: number
  signal: number | null
  current_signal: number
  position: number
  buy_signals: number
  sell_signals: number
  num_buy_signals: number
  num_sell_signals: number
  buy_spend: number
  sell_spend: number
  holdings: number
  quote_net_assets: number
  base_net_assets: number
  drawdown: number
}
