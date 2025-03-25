import { Injectable } from '@angular/core'
import { MongoClient } from 'mongodb'
import { Swap } from './types'

const endpoint =
  'mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.4.2' // eslint-disable-line max-len

@Injectable({
  providedIn: 'root',
})
export class DbService {
  client: MongoClient

  constructor() {
    this.client = new MongoClient(endpoint)
  }

  public async getSwapsByDate(date: string, token0: string, token1: string): Promise<Swap[]> {
    const swaps = await this.client.db('swaps').collection<Swap[]>('swapshistory').findOne({
      date: date,
      token0: token0,
      token1: token1,
    })

    if (!swaps) {
      return []
    }

    return swaps
  }
  public async insertSwaps(swaps: Swap[]): Promise<boolean> {
    const result = await this.client.db('swaps').collection<Swap[]>('swapshistory').insertOne(swaps)

    return result.acknowledged
  }
}
