import { apiKey } from './private.json'

export const daysBack = 20
export const mongodbURI =
  'mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.4.2' // eslint-disable-line max-len

// eslint-disable-next-line max-len
export const graphqlEndpoint = `https://gateway.thegraph.com/api/${apiKey}/subgraphs/id/HMuAwufqZ1YCRmzL2SfHTVkzZovC9VL2UAKhjvRqKiR1`

export enum Tokens {
  WETH = '0x4200000000000000000000000000000000000006',
  BOBO = '0x570b1533F6dAa82814B25B62B5c7c4c55eB83947',
}
