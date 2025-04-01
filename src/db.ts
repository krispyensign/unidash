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

  public async upsertOHLC(ohlc: OHLC[], startDate: Date, endDate: Date): Promise<boolean> {
    // check if ohlc is empty skip insert
    if (ohlc.length === 0) {
      console.log('no ohlc to insert')
      return true
    }

    // validate names are not undefined
    if (ohlc[0].token0 === undefined || ohlc[0].token1 === undefined) {
      throw new Error('token0 or token1 is undefined')
    }

    let result: InsertManyResult<OHLC> | null = null
    try {
      // delete the already present ohlc
      await this.client
        .db('ohlc')
        .collection<OHLC>('ohlchistory')
        .deleteMany({
          token0: ohlc[0].token0,
          token1: ohlc[0].token1,
          timestamp: {
            $gte: startDate.getTime(),
            $lte: endDate.getTime(),
          },
        })

      // insert the new ohlc
      result = await this.client.db('ohlc').collection<OHLC>('ohlchistory').insertMany(ohlc)
    } catch (e) {
      // if ohlc already exists skip
      if (e instanceof MongoBulkWriteError) {
        if (e.code === '11000') {
          console.log('already exists')
          return true
        }
      }

      throw e
    }

    return result.acknowledged
  }

  public async getOHLC(
    token0: string,
    token1: string,
    startDate: Date,
    endDate: Date
  ): Promise<OHLC[]> {
    const cursor = this.client
      .db('ohlc')
      .collection<OHLC>('ohlchistory')
      .find({
        token0: token0,
        token1: token1,
        timestamp: {
          $gte: startDate.getTime(),
          $lte: endDate.getTime(),
        },
      })
      .sort({ timestamp: 1 })

    const ohlc: OHLC[] = []
    for await (const doc of cursor) {
      ohlc.push(doc)
    }

    if (!ohlc) {
      return []
    }

    return ohlc
  }
}
