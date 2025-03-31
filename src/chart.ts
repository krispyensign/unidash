// Define the GraphQL endpoint for the Uniswap subgraph v3
import { GraphQLClient, gql } from 'graphql-request'
import type { Swap, Data, RawSwap, Arguments, DataFrame, OHLC, OandaCandle } from './types'
import { Inject, Injectable } from '@angular/core'
import { DbService } from './db'
import { ConfigToken } from './config'
import { ethers } from 'ethers'
import { chart, loadDataFrame } from './pytrade'

@Injectable({
  providedIn: 'root',
})
export class ChartService {
  dbService: DbService
  graphqlEndpoint: string | undefined
  oandaEndpoint: string | undefined
  oandaAPIKey: string | undefined
  daysToFetch: number
  token0: string
  token1: string
  swapTokens: boolean

  constructor(dbService: DbService, @Inject(ConfigToken) config: Arguments) {
    this.dbService = dbService
    if (config.chartDatasource === 'uniswap') {
      if (config.graphqlEndpoint === undefined) {
        throw new Error('graphqlEndpoint is required')
      }
      this.graphqlEndpoint = config.graphqlEndpoint
    } else if (config.chartDatasource === 'oanda') {
      if (config.oandaEndpoint === undefined) {
        throw new Error('oandaEndpoint is required')
      }
      if (config.oandaAPIKey === undefined) {
        throw new Error('oandaAPIKey is required')
      }
      this.oandaEndpoint = config.oandaEndpoint
      this.oandaAPIKey = config.oandaAPIKey
    }
    this.token0 = config.token0
    this.token1 = config.token1
    this.swapTokens = config.tokenSwap
    this.daysToFetch = config.daysToFetch
  }

  public async GetOHLC(date: Date): Promise<DataFrame | null> {
    if (this.graphqlEndpoint) {
      return this.GetOHLCUniswap(date)
    } else {
      return this.GetOHLCOanda(date)
    }
  }

  private async GetOHLCOanda(date: Date): Promise<DataFrame | null> {
    // fetch ohlc data from oanda for each day
    let oandaOhlcData: OandaCandle[] = []
    for (let i = 0; i < this.daysToFetch; i++) {
      const dateStart = new Date(date)
      const dateEnd = new Date(date)
      dateStart.setUTCHours(0, 0, 0, 0)
      dateEnd.setUTCHours(23, 59, 59, 999)
      const response = await fetch(
        // eslint-disable-next-line max-len
        `${this.oandaEndpoint}/v3/instruments/${this.token0}_${this.token1}/candles?price=MAB&granularity=M5&from=${dateStart.toISOString()}&to=${dateEnd.toISOString()}`,
        {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${this.oandaAPIKey}`,
          },
        }
      )
      const data = await response.json()
      oandaOhlcData = oandaOhlcData.concat(data.candles)
      date.setDate(date.getDate() + 1)
    }

    const ohlcDate = oandaOhlcData.map<OHLC>(s => ({
      ask_close: s.ask.c,
      ask_high: s.ask.h,
      ask_low: s.ask.l,
      ask_open: s.ask.o,
      bid_close: s.bid.c,
      bid_high: s.bid.h,
      bid_low: s.bid.l,
      bid_open: s.bid.o,
      close: s.mid.c,
      high: s.mid.h,
      low: s.mid.l,
      open: s.mid.o,
      timestamp: new Date(s.time).getTime(),
      token0: this.token0,
      token1: this.token1,
    }))

    // save ohlc
    try {
      const saved = await this.SaveOHLC(ohlcDate)
      if (!saved) {
        console.log('ohlc not saved')
        throw new Error('ohlc not saved')
      }
    } catch (e) {
      console.log(e)
      throw e
    }

    // load dataframe
    const df = await loadDataFrame(JSON.stringify(ohlcDate))
    console.log('loaded oanda data %d', ohlcDate.length)
    console.log(df.tail(1).to_json())
    return df
  }

  private async GetOHLCUniswap(date: Date): Promise<DataFrame> {
    // get swap history
    const allSwaps = await this.GetSwaps(date)
    if (allSwaps.length === 0) {
      console.log('no swaps found')
      throw new Error('no swaps found')
    }

    // load dataframe
    const df = await loadDataFrame(JSON.stringify(allSwaps))

    // resample to 5 min
    const [df_ohlc, jsonData] = chart.ohlc(df, '5Min', this.swapTokens)

    // save ohlc
    const ohlcData = JSON.parse(jsonData)
    try {
      const saved = await this.SaveOHLC(ohlcData)
      if (!saved) {
        console.log('ohlc not saved')
        throw new Error('ohlc not saved')
      }
    } catch (e) {
      console.log(e)
      throw e
    }

    return df_ohlc
  }

  public async GetSwaps(date: Date, batchSize = 100): Promise<Swap[]> {
    // check if data is already saved
    const swaps = await this.dbService.getSwapsSince(date, this.token0, this.token1)
    let outData: Swap[] = []
    let latestDate = 0

    // if data is already saved, get the latest date (in unix) and start from there
    // else start from the beginning
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
    const client = new GraphQLClient(this.graphqlEndpoint!)

    // get swaps in k batches of batchSize
    let k = 0
    while (true) {
      // define the graphql query
      const query = gql`
      { 
        swaps(
            where: {
                token0: "${this.token0}",
                token1: "${this.token1}",
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

      // map the results to the internal Swap type
      const mappedSwapps = data.swaps.map((swap: RawSwap) => {
        return {
          swapId: swap.id,
          timestamp: parseInt(swap.timestamp) * 1000,
          amount0: ethers.parseEther(swap.amount0).toString(),
          amount1: ethers.parseEther(swap.amount1).toString(),
          token0: this.token0,
          token1: this.token1,
        }
      })

      // aggregate the results
      outData = outData.concat(mappedSwapps)

      // save the data
      if (data.swaps.length > 0) {
        const isSaved = await this.dbService.insertSwaps(mappedSwapps)
        if (!isSaved) {
          throw new Error('Failed to save data')
        }
        console.log('swaps saved to db')
      }

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

  public async SaveOHLC(ohlcData: OHLC[]): Promise<boolean> {
    for (const ohlc of ohlcData) {
      ohlc.token0 = this.token0
      ohlc.token1 = this.token1
    }
    const isSaved = await this.dbService.insertOHLC(ohlcData)
    if (isSaved) {
      return true
    }

    return false
  }
}
