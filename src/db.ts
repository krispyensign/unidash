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
    const dateA = new Date(new Date(date).setUTCHours(0, 0, 0, 0))
    const dateB = new Date(new Date(date).setUTCHours(23, 59, 59, 999))
    console.log('getSwapsByDate', dateA, token0, token1)
    const cursor = this.client
      .db('swaps')
      .collection<Swap>('swapshistory')
      .find({
        timestamp: {
          $gte: dateA.getTime(),
          $lte: dateB.getTime(),
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
