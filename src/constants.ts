import { apiKey } from './private.json'
import { TestStrategy } from './types'

export type CheatCode = {
  wmaColumnIn: string
  signalColumnIn: string
  testStrategy: TestStrategy
}

export const mostRecentTradeCount = 10
export const dayInMS = 1000 * 60 * 60 * 24
export const daysBack = 60
export const mongodbURI =
  'mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.4.2' // eslint-disable-line max-len

// eslint-disable-next-line max-len
export const graphqlEndpoint = `https://gateway.thegraph.com/api/${apiKey}/subgraphs/id/HMuAwufqZ1YCRmzL2SfHTVkzZovC9VL2UAKhjvRqKiR1`

// export const cheatCode: CheatCode | null = null

export const cheatCode: CheatCode | null = {
  wmaColumnIn: 'ha_open',
  signalColumnIn: 'ha_open',
  testStrategy: 'WMA_HEIKEN_ASHI_INVERSE',
}

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
