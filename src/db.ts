import { Inject, Injectable } from '@angular/core'
import { InsertManyResult, MongoBulkWriteError, MongoClient } from 'mongodb'
import { Swap, Arguments } from './types'
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
}
