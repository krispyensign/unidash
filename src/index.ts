import { loadDataFrame, loadPy } from './pytrade'
import { SwapHistoryService } from './swapshistory'
import { DbService } from './db'
import { Injector } from '@angular/core'
import { Swap } from './types'
import { backTest } from './backtest'
import { daysBack, Tokens } from './constants'
import { start } from 'repl'

async function main(): Promise<void> {
  await loadPy()
  const injector = Injector.create({
    providers: [
      { provide: SwapHistoryService, deps: [DbService] },
      { provide: DbService, deps: [] },
    ],
  })

  const dayInMS = 1000 * 60 * 60 * 24
  let starterTimestamp = new Date().getTime()
  starterTimestamp -= dayInMS * daysBack

  const allSwaps: Swap[] = []

  for (let i = 0; i < daysBack; i++) {
    const date = new Date(starterTimestamp + i * dayInMS)
    const swaps = await injector
      .get(SwapHistoryService)
      .GetSwapsByDate(Tokens.WETH, Tokens.BOBO, date)
    allSwaps.push(...swaps)
  }

  const df = await loadDataFrame(JSON.stringify(allSwaps))

  backTest(df)

  process.exit(0)
}

main()
