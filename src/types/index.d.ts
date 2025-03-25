export type Swap = {
  timestamp: string
  amount0: string
  amount1: string
}

export type Data = {
  swaps: Swap[]
}

export type TransformedSwap = {
  timestamp: number
  amount0: number
  amount1: number
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

export type TradingIndicator = {
  wma: (df: DataFrame, period: number, column: string) => DataFrame
  iwma: (df: DataFrame, period: number, column: string) => DataFrame
  signal_compare: (df: DataFrame, column0: string, column1: string) => DataFrame
}

export type TradingChart = {
  ohlc: (dataIn: DataFrame, timeFrame: string) => DataFrame
  heiken: (dataIn: DataFrame) => DataFrame
}

export type TradingUtil = {
  portfolio: (dataIn: DataFrame) => [DataFrame, number, number]
}
