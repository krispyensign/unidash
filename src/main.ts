import { loadDataFrame } from './pytrade'
import { SwapHistoryService } from './swapshistory'
import { Injectable } from '@angular/core'
import { DataFrame, Swap, TestSet, Token } from './types'
import { cheatCode, dayInMS, daysBack } from './constants'
import { Signals } from './signals'
import { BacktestService } from './backtest'
import { tokenIn0, tokenIn1 } from './private.json'
import { colorize } from 'json-colorizer'
import { pushAlert } from './pushAlert'

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

  public async GetSwapHistory(token0: Token, token1: Token): Promise<Swap[]> {
    const starterTimestamp = new Date(new Date().setUTCHours(0, 0, 0, 1) - dayInMS * daysBack)

    const swaps = await this.swapService.GetSwapsSince(token0, token1, starterTimestamp)

    return swaps
  }

  public async run(): Promise<boolean> {
    // get swap history
    const allSwaps = await this.GetSwapHistory(tokenIn0 as Token, tokenIn1 as Token)
    if (allSwaps.length === 0) {
      console.log('no swaps found')
      return false
    }

    // load dataframe
    const df = await loadDataFrame(JSON.stringify(allSwaps))

    // backtest
    const testSet: TestSet = this.backTest(df)

    // generate signals
    console.log('generating signals for test set %s', colorize(testSet))
    const result = this.signalService.generateSignals(testSet, df)
    if (result === null) {
      throw new Error('invalid signals')
    }

    // log mostRecentTrade and then fail if invalid
    const [dfSignals, valid] = result
    console.log(colorize(dfSignals.tail(1).to_json()))
    const { mostRecentPosition, mostRecentTrade } =
      this.backtestService.getMostRecentTrades(dfSignals)
    if (!valid) {
      throw new Error('invalid signals')
    }

    // push alert if there is a trade
    await pushAlert(mostRecentPosition, mostRecentTrade)

    return true
  }

  private backTest(df: DataFrame): TestSet {
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
