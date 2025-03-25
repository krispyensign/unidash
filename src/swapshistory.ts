// Define the GraphQL endpoint for the Uniswap subgraph v3
import { GraphQLClient, gql } from 'graphql-request'
import { apiKey } from './private.json'
import type { TransformedSwap, Data, Swap } from './types'
// eslint-disable-next-line max-len
export const endpoint = `https://gateway.thegraph.com/api/${apiKey}/subgraphs/id/HMuAwufqZ1YCRmzL2SfHTVkzZovC9VL2UAKhjvRqKiR1`
import { Cache } from 'file-system-cache'
import type { Token } from './types'

import { MongoClient } from 'mongodb'

// local usage only.  do not run in a real production environment
const uri =
  'mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.4.2' // eslint-disable-line max-len
const client = new MongoClient(uri)

async function run(): Promise<void> {
  try {
    await client.connect()

    // database and collection code goes here
    // find code goes here
    // iterate code goes here
  } finally {
    // Ensures that the client will close when you finish/error
    await client.close()
  }
}
run().catch(console.dir)

/**
 * Fetches swap data for specified tokens from a GraphQL endpoint.
 *
 * This function queries the Uniswap subgraph to retrieve swap data for the
 * specified token pair over the last 20 days. It makes 20 separate requests,
 * each fetching swaps for one day, and aggregates the results.
 *
 * TODO: Cache each day individually so that it doesn't have to fetch the full
 * X number of days every time.  This way this can be configurable to download
 * any number of days.
 *
 * @param token0 The address of the first token in the pair.
 * @param token1 The address of the second token in the pair.
 * @returns A promise that resolves to an array of TransformedSwap objects,
 *          containing the timestamp, amount0, and amount1 for each swap.
 */
export async function GetSwaps(token0: Token, token1: Token): Promise<TransformedSwap[]> {
  // Create a cache
  const cache = new Cache({
    ttl: 360,
  })

  // Check if data is already in cache
  let outData: TransformedSwap[] = await cache.get('foo')
  if (outData) {
    return outData
  }

  // If not, fetch data
  outData = []

  // Create a GraphQL client
  const client = new GraphQLClient(endpoint)

  // call endpoint 20 times for each of the 20 days
  const now = Math.floor(new Date().getTime() / 1000)
  const dayInSecs = 86400
  const numDays = 20
  for (let i = now; i > now - dayInSecs * numDays; i -= dayInSecs) {
    // Define the GraphQL query
    const query = gql`
        {
            swaps(
                where: {
                    token0: "${token0}",
                    token1: "${token1}",
                    timestamp_gt: "${i}"
                }
                orderBy: timestamp
                orderDirection: desc
            ) {
                timestamp
                amount0
                amount1
            }
        }
        `

    const data: Data = await client.request(query)

    outData = outData.concat(
      data.swaps.map((swap: Swap) => {
        return {
          timestamp: parseInt(swap.timestamp),
          amount0: parseFloat(swap.amount0),
          amount1: parseFloat(swap.amount1),
        }
      })
    )
  }

  await cache.set('foo', outData)

  console.log(outData.length)
  return outData
}
