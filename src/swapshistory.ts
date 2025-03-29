// Define the GraphQL endpoint for the Uniswap subgraph v3
import { GraphQLClient, gql } from 'graphql-request'
import type { Swap, Data, RawSwap, Arguments } from './types'
import type { Token } from './types'
import { Inject, Injectable } from '@angular/core'
import { DbService } from './db'
import { ConfigToken } from './config'

@Injectable({
  providedIn: 'root',
})
export class SwapHistoryService {
  dbService: DbService
  graphqlEndpoint: string

  constructor(dbService: DbService, @Inject(ConfigToken) config: Arguments) {
    this.dbService = dbService
    this.graphqlEndpoint = config.graphqlEndpoint
  }

  public async GetSwapsSince(
    token0: Token,
    token1: Token,
    date: Date,
    batchSize = 100
  ): Promise<Swap[]> {
    // check if data is already saved
    const swaps = await this.dbService.getSwapsSince(date, token0, token1)
    let outData: Swap[] = []
    let latestDate = 0
    if (swaps.length > 0) {
      latestDate = Math.round(swaps[swaps.length - 1].timestamp / 1000)
      const latestSwap = swaps[swaps.length - 1]
      console.log(
        'latest swap: %s %s %s',
        latestSwap.swapId,
        new Date(latestSwap.timestamp).toLocaleDateString(),
        new Date(latestSwap.timestamp).toLocaleTimeString()
      )
    } else {
      latestDate = Math.round(new Date(new Date(date).setUTCHours(0, 0, 0, 0)).getTime() / 1000)
    }

    // create a graphql client
    const client = new GraphQLClient(this.graphqlEndpoint)

    // get swaps in k batches of batchSize
    let k = 0
    while (true) {
      // define the graphql query
      const query = gql`
      { 
        swaps(
            where: {
                token0: "${token0}",
                token1: "${token1}",
                timestamp_gte: ${latestDate}
            }
            orderBy: timestamp
            orderDirection: desc
            skip: ${k * batchSize}
            first: ${batchSize}
        ) {
            id
            timestamp
            amount0
            amount1
        }
      }
      `
      console.log(query)

      // make the graphql request
      const data: Data = await client.request(query)

      // aggregate the results
      outData = outData.concat(
        data.swaps.map((swap: RawSwap) => {
          return {
            swapId: swap.id,
            timestamp: parseInt(swap.timestamp) * 1000,
            amount0: parseFloat(swap.amount0),
            amount1: parseFloat(swap.amount1),
            token0: token0,
            token1: token1,
          }
        })
      )

      // break the loop if there are no more results
      if (data.swaps.length < batchSize) {
        break
      }

      // increment the offset for the next request
      k++
    }

    // return what was already provided if no new swaps were found
    if (outData.length === 0) {
      console.log('no more swaps found')
      return swaps
    }

    // save the data
    const isSaved = await this.dbService.insertSwaps(outData)
    if (!isSaved) {
      throw new Error('Failed to save data')
    }
    console.log('swaps saved to db')

    // append the new data to the existing data
    outData = swaps.concat(outData)
    outData.sort((a, b) => a.timestamp - b.timestamp)

    // print the latest swap
    const latestSwap = outData[outData.length - 1]
    console.log(
      'latest swap: %s %s %s',
      latestSwap.swapId,
      new Date(latestSwap.timestamp).toLocaleDateString(),
      new Date(latestSwap.timestamp).toLocaleTimeString()
    )

    // return the data
    return outData
  }
}
