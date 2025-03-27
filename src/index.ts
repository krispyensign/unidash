import { loadDataFrame, loadPy } from './pytrade'
import { SwapHistoryService } from './swapshistory'
import { DbService } from './db'
import { Injectable, Injector } from '@angular/core'
import { DataFrame, Swap, TestSet } from './types'
import { cheatCode, dayInMS, daysBack, mostRecentTradeCount, Tokens } from './constants'
import { Strategy } from './strategy'
import { Signals } from './signals'
import { BacktestService } from './backtest'
import { priority, heartbeat } from './private.json'

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

    const df = await loadDataFrame(JSON.stringify(allSwaps))

    const testSet: TestSet = this.newMethod(df)

    const [dfSignals, valid] = this.signalService.generateSignals(testSet, df)
    if (!valid) {
      throw new Error('invalid signals')
      return false
    }

    console.log('valid signals')
    let mostRecentTrades: [number, number][] = []
    const recentSignals = JSON.parse(dfSignals.to_json())
    const positionRows: [string, number][] = Object.entries(recentSignals['position'])
    const mostRecentPosition = positionRows[positionRows.length - 1]
    for (const signal of positionRows) {
      if (signal[1] === 0) {
        continue
      }
      mostRecentTrades = mostRecentTrades.concat([[parseInt(signal[0]), signal[1] as number]])
    }
    const mostRecentTrade = mostRecentTrades[mostRecentTrades.length - 1]

    for (let i = 0; i < mostRecentTradeCount; i++) {
      if (i >= mostRecentTrades.length) {
        break
      }
      const trade = mostRecentTrades[mostRecentTrades.length - 1 - i]

      const signalTimestamp = trade[0]
      const signal = trade[1]
      console.log('%s %d', new Date(signalTimestamp).toLocaleString(), signal)
    }

    if (mostRecentPosition[1] !== 0) {
      const response = await fetch(`https://ntfy.sh/${priority}`, {
        method: 'POST',
        body: `${mostRecentTrade[1] === 1 ? 'buy' : 'sell'} ${new Date(mostRecentTrade[0])}`,
        headers: { Priority: '5' },
      })
      console.log(await response.text())
    } else {
      const response = await fetch(`https://ntfy.sh/${heartbeat}`, {
        method: 'POST',
        body: `heartbeat ${mostRecentTrade[1] === 1 ? 'buy' : 'sell'}
          ${new Date(mostRecentTrade[0])}`,
        headers: { Priority: '2' },
      })

      console.log(await response.text())
    }

    return true
  }

  private newMethod(df: DataFrame): TestSet {
    let testSet: TestSet | null = null
    if (cheatCode === null) {
      console.log('backtesting')
      const result = this.backtestService.backTest(df)
      if (!result || result[0] === null) {
        throw new Error('no valid test sets')
      }

      testSet = result[0]
    } else {
      testSet = {
        signalColumnIn: cheatCode.signalColumnIn,
        wmaColumnIn: cheatCode.wmaColumnIn,
        testStrategy: cheatCode.testStrategy,
      }
    }
    return testSet
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
  const success = true
  const delay = (ms: number | undefined): Promise<unknown> =>
    new Promise(resolve => setTimeout(resolve, ms))
  while (success) {
    console.log('waiting for next minute')
    await delay(1000 * 60)
    try {
      const success = await mainWorkflow.run()
      if (!success) {
        throw new Error('something went wrong')
      }
    } catch (e) {
      console.log(e)
      const response = await fetch(`https://ntfy.sh/${priority}`, {
        method: 'POST',
        body: `error: ${e}`,
        headers: { Priority: '4' },
      })
    }
  }

  console.log('done')
}

main().finally(() => process.exit(0))
