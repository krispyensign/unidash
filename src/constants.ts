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

export const cheatCode: CheatCode | null = {
  wmaColumnIn: 'ha_close',
  signalColumnIn: 'ha_close',
  testStrategy: 'IWMA_HEIKEN_ASHI',
}
