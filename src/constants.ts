import { apiKey } from './private.json'
import { TestStrategy } from './types'

export type CheatCode = {
  wmaColumnIn: string
  signalColumnIn: string
  testStrategy: TestStrategy
}

export const dayInMS = 1000 * 60 * 60 * 24
export const daysBack = 60
export const mongodbURI =
  'mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.4.2' // eslint-disable-line max-len

// eslint-disable-next-line max-len
export const graphqlEndpoint = `https://gateway.thegraph.com/api/${apiKey}/subgraphs/id/HMuAwufqZ1YCRmzL2SfHTVkzZovC9VL2UAKhjvRqKiR1`

export enum Tokens {
  WETH = '0x4200000000000000000000000000000000000006',
  BOBO = '0x570b1533F6dAa82814B25B62B5c7c4c55eB83947',
}

export const cheatCode: CheatCode | null = null

// export const cheatCode: CheatCode | null = {
//   wmaColumnIn: 'ha_close',
//   signalColumnIn: 'ha_close',
//   testStrategy: 'IWMA_HEIKEN_ASHI',
// }

export const points = [
  // 'open',
  // 'close',
  // 'high',
  // 'low',
  // 'ha_open',
  'ha_close',
  // 'ha_high',
  // 'ha_low',
  // 'ha_bid_open',
  // 'ha_bid_close',
  // 'ha_bid_high',
  // 'ha_bid_low',
  // 'ha_ask_open',
  // 'ha_ask_close',
  // 'ha_ask_high',
  // 'ha_ask_low',
  'ask_open',
  // 'ask_close',
  // 'ask_high',
  // 'ask_low',
  // 'bid_open',
  // 'bid_close',
  // 'bid_high',
  // 'bid_low',
]

export const strategies: TestStrategy[] = [
  'IWMA_HEIKEN_ASHI_INVERSE',
  'IWMA_HEIKEN_ASHI',
  'WMA_HEIKEN_ASHI',
  'WMA_HEIKEN_ASHI_INVERSE',
]
