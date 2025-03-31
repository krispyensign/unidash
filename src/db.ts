import { Inject, Injectable } from '@angular/core'
import { InsertManyResult, MongoBulkWriteError, MongoClient } from 'mongodb'
import { Swap, Arguments, OHLC } from './types'
import { ConfigToken } from './config'

@Injectable({
  providedIn: 'root',
})
export class DbService {
  client: MongoClient

  constructor(@Inject(ConfigToken) config: Arguments) {
    this.client = new MongoClient(config.mongodbEndpoint)
  }

  public async getSwapsSince(date: Date, token0: string, token1: string): Promise<Swap[]> {
    const dateA = new Date(new Date(date).setUTCHours(0, 0, 0, 0))
    console.log('getSwapsByDate', dateA, token0, token1)
    const cursor = this.client
      .db('swaps')
      .collection<Swap>('swapshistory')
      .find({
        timestamp: {
          $gte: dateA.getTime(),
        },
        token0: token0,
        token1: token1,
      })
      .sort({ timestamp: 1 })

    const swaps: Swap[] = []
    for await (const doc of cursor) {
      swaps.push(doc)
    }

    if (!swaps) {
      return []
    }

    return swaps
  }

  public async insertSwaps(swaps: Swap[]): Promise<boolean> {
    let result: InsertManyResult<Swap> | null = null
    try {
      result = await this.client.db('swaps').collection<Swap>('swapshistory').insertMany(swaps)
    } catch (e) {
      if (e instanceof MongoBulkWriteError) {
        if (e.code === '11000') {
          console.log('already exists')
          return true
        }
      }
      console.log(e)
      throw e
    }

    return result.acknowledged
  }

  public async insertOHLC(ohlc: OHLC[]): Promise<boolean> {
    let result: InsertManyResult<OHLC> | null = null
    try {
      // get the already present ohlc
      const lastOHLC = await this.client
        .db('ohlc')
        .collection<OHLC>('ohlchistory')
        .find({
          token0: ohlc[0].token0,
          token1: ohlc[1].token1,
        })
        .sort({ timestamp: -1 })
        .limit(1)
        .toArray()

      if (lastOHLC.length > 0) {
        // drop the most recent ohlc from the db since it most likely was pending
        await this.client
          .db('ohlc')
          .collection<OHLC>('ohlchistory')
          .deleteOne({ timestamp: lastOHLC[0].timestamp })

        // keep only the new ohlc
        ohlc = ohlc.filter(ohlc => {
          return ohlc.timestamp >= lastOHLC[0].timestamp
        })
      }

      // insert the new ohlc
      result = await this.client.db('ohlc').collection<OHLC>('ohlchistory').insertMany(ohlc)
    } catch (e) {
      if (e instanceof MongoBulkWriteError) {
        if (e.code === '11000') {
          console.log('already exists')
          return true
        }
      }
      console.log(e)
      throw e
    }

    return result.acknowledged
  }
}
