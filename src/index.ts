import { loadDataFrame, loadPy } from './pytrade'
import { SwapHistoryService } from './swapshistory'
import { DbService } from './db'
import { Injectable, Injector } from '@angular/core'
import { Swap, TestSet } from './types'
import { cheatCode, dayInMS, daysBack, Tokens } from './constants'
import { Strategy } from './strategy'
import { Signals } from './signals'
import { BacktestService } from './backtest'

@Injectable({
  providedIn: 'root',
})
export class MainWorkflow {
  swapService: SwapHistoryService
  signalService: Signals
  backtestService: BacktestService
  constructor(
    swapService: SwapHistoryService,
    signalService: Signals,
    backtestService: BacktestService
  ) {
    this.swapService = swapService
    this.signalService = signalService
    this.backtestService = backtestService
  }

  public async GetSwapHistory(token0: Tokens, token1: Tokens): Promise<Swap[]> {
    const starterTimestamp = new Date(new Date().setUTCHours(0, 0, 0, 1) - dayInMS * daysBack)

    const swaps = await this.swapService.GetSwapsSince(token0, token1, starterTimestamp)

    return swaps
  }

  public async run(): Promise<boolean> {
    const allSwaps = await this.GetSwapHistory(Tokens.WETH, Tokens.BOBO)
    if (allSwaps.length === 0) {
      console.log('no swaps found')
      return false
    }

    const latestSwap = allSwaps[allSwaps.length - 1]
    console.log(
      'latest swap: %s %s %s',
      latestSwap.swapId,
      new Date(latestSwap.timestamp).toLocaleDateString(),
      new Date(latestSwap.timestamp).toLocaleTimeString()
    )

    const df = await loadDataFrame(JSON.stringify(allSwaps))

    let testSet: TestSet | null = null
    if (cheatCode === null) {
      const result = this.backtestService.backTest(df)
      if (!result) {
        console.log('no valid test sets')
        return false
      }

      testSet = result[0]
    }

    if (testSet === null) {
      console.log('no valid test sets')
      return false
    }

    const [dfSignals, valid, quoteProfit, baseProfit] = this.signalService.generateSignals(
      testSet,
      df
    )

    if (!valid) {
      console.log('invalid signals')
      return false
    }

    return true
  }
}

async function main(): Promise<void> {
  await loadPy()
  const injector = Injector.create({
    providers: [
      { provide: DbService, deps: [] },
      { provide: Strategy, deps: [] },
      { provide: SwapHistoryService, deps: [DbService] },
      { provide: Signals, deps: [Strategy] },
      { provide: BacktestService, deps: [Signals] },
      { provide: MainWorkflow, deps: [SwapHistoryService, Signals, BacktestService] },
    ],
  })

  const mainWorkflow = injector.get(MainWorkflow)
  const success = await mainWorkflow.run()
  if (!success) {
    console.log('something went wrong')
    throw new Error('something went wrong')
  }

  console.log('done')
}

main().finally(() => process.exit(0))
