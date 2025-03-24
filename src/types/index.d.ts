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
  [key: string]: any
  copy(): DataFrame
  reset_index(): DataFrame
  at: any
  loc: DataFrame
  shape: [number, number]
  resample(freq: string): DataFrame
  ohlc(): DataFrame
  set_index(column: string): DataFrame
  head(count?: number): DataFrame
  tail(count?: number): DataFrame
  to_json(): string
}

export type TestSet = {
  signalColumnIn: string
  wmaColumnIn: string
  testStrategy: TestStrategy
}

export enum TestStrategy {
  WMA_HEIKEN_ASHI = 'WMA_HEIKEN_ASHI',
  IWMA_HEIKEN_ASHI = 'IWMA_HEIKEN_ASHI',
  WMA_HEIKEN_ASHI_INVERSE = 'WMA_HEIKEN_ASHI_INVERSE',
  IWMA_HEIKEN_ASHI_INVERSE = 'IWMA_HEIKEN_ASHI_INVERSE',
}

export type Portfolio = {
  timestamp: number
  amount: number
  value: number
  base_value: number
  inverted: boolean
}

export type TradingIndicator = {
  wma: (ha_df: DataFrame, period: number, column: string) => DataFrame
  iwma: (ha_df: DataFrame, period: number, column: string) => DataFrame
  signal: (ha_df: DataFrame, column0: string, column1: string) => DataFrame
}

export type TradingChart = {
  ohlc: (dataIn: DataFrame, timeFrame: string) => DataFrame
  heiken: (dataIn: DataFrame) => DataFrame
}

export type TradingUtil = {
  portfolio: (dataIn: DataFrame) => [DataFrame, number, number]
}
