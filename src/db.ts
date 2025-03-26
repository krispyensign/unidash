import { Injectable } from '@angular/core'
import { MongoClient } from 'mongodb'
import { Swap } from './types'
import { mongodbURI } from './constants'

@Injectable({
  providedIn: 'root',
})
export class DbService {
  client: MongoClient

  constructor() {
    this.client = new MongoClient(mongodbURI)
  }

  public async getSwapsByDate(date: Date, token0: string, token1: string): Promise<Swap[]> {
    console.log('getSwapsByDate', date.getTime(), token0, token1)
    const dateA = new Date(date)
    const dateB = new Date(date)
    const cursor = this.client
      .db('swaps')
      .collection<Swap>('swapshistory')
      .find({
        timestamp: {
          $gte: new Date(dateA.setHours(0, 0, 0, 0)).getTime(),
          $lte: new Date(dateB.setHours(23, 59, 59, 999)).getTime(),
        },
        token0: token0,
        token1: token1,
      })

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
    const result = await this.client.db('swaps').collection<Swap>('swapshistory').insertMany(swaps)

    return result.acknowledged
  }
}
