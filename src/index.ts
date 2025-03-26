import { loadDataFrame, loadPy } from './pytrade'
import { SwapHistoryService } from './swapshistory'
import { DbService } from './db'
import { Injector } from '@angular/core'
import { Swap } from './types'
import { backTest } from './backtest'
import { dayInMS, daysBack, Tokens } from './constants'

async function GetSwapHistory(
  swapService: SwapHistoryService,
  token0: Tokens,
  token1: Tokens
): Promise<Swap[]> {
  let starterTimestamp = new Date().getTime()
  starterTimestamp -= dayInMS * daysBack

  const allSwaps: Swap[] = []

  for (let i = 0; i < daysBack; i++) {
    const date = new Date(starterTimestamp + i * dayInMS)
    const swaps = await swapService.GetSwapsByDate(token0, token1, date)
    allSwaps.push(...swaps)
  }

  return allSwaps
}

async function main(): Promise<void> {
  await loadPy()
  const injector = Injector.create({
    providers: [
      { provide: SwapHistoryService, deps: [DbService] },
      { provide: DbService, deps: [] },
    ],
  })

  const allSwaps = await GetSwapHistory(injector.get(SwapHistoryService), Tokens.WETH, Tokens.BOBO)

  const df = await loadDataFrame(JSON.stringify(allSwaps))

  backTest(df)

  process.exit(0)
}

main()
