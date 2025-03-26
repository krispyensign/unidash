// Define the GraphQL endpoint for the Uniswap subgraph v3
import { GraphQLClient, gql } from 'graphql-request'
import type { Swap, Data, RawSwap } from './types'
import type { Token } from './types'
import { Injectable } from '@angular/core'
import { DbService } from './db'
import { graphqlEndpoint } from './constants'

@Injectable({
  providedIn: 'root',
})
export class SwapHistoryService {
  dbService: DbService

  constructor(dbService: DbService) {
    this.dbService = dbService
  }

  public async GetSwapsByDate(
    token0: Token,
    token1: Token,
    date: Date,
    batchSize = 100
  ): Promise<Swap[]> {
    // check if data is already saved
    const swaps = await this.dbService.getSwapsByDate(date, token0, token1)
    if (swaps.length > 0) {
      console.log('swaps found in db')
      return swaps
    }

    // if not, fetch data
    let outData: Swap[] = []

    // create a graphql client
    const client = new GraphQLClient(graphqlEndpoint)

    // define the date range to query
    const i = Math.round(new Date(date).setUTCHours(0, 0, 0, 0) / 1000)
    const j = Math.round(new Date(date).setUTCHours(23, 59, 59, 0) / 1000)

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
                timestamp_gte: ${i},
                timestamp_lte: ${j},
            }
            orderBy: timestamp
            orderDirection: desc
            skip: ${k * batchSize}
            first: ${(k + 1) * batchSize}
        ) {
            id
            timestamp
            amount0
            amount1
        }
      }
      `
      // console.log(query)

      // make the graphql request
      const data: Data = await client.request(query)

      // break the loop if there are no more results
      if (data.swaps.length === 0) {
        break
      }

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

      // increment the offset for the next request
      k++
    }

    if (outData.length === 0) {
      throw new Error('No data found')
    }

    // save the data
    const isSaved = await this.dbService.insertSwaps(outData)
    if (!isSaved) {
      throw new Error('Failed to save data')
    }

    console.log('swaps saved to db')

    return outData
  }
}
