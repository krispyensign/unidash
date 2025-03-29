import { TestStrategy } from './types'

export const dayInMS = 1000 * 60 * 60 * 24

export const points = ['open', 'close', 'high', 'low', 'ha_open', 'ha_close', 'ha_high', 'ha_low']

export const strategies: TestStrategy[] = [
  'IWMA_HEIKEN_ASHI_INVERSE',
  'IWMA_HEIKEN_ASHI',
  'WMA_HEIKEN_ASHI',
  'WMA_HEIKEN_ASHI_INVERSE',
  'IWMA_OHLC',
  'WMA_OHLC',
  'IWMA_OHLC_INVERSE',
  'WMA_OHLC_INVERSE',
]
