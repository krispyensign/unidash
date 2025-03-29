import { loadDataFrame } from './pytrade'
import { SwapHistoryService } from './swapshistory'
import { Inject, Injectable } from '@angular/core'
import type { Arguments, DataFrame, Swap, TestSet, TestStrategy, Token } from './types'
import { dayInMS } from './constants'
import { Signals } from './signals'
import { BacktestService } from './backtest'
import { colorize } from 'json-colorizer'
import { ConfigToken } from './config'
import { PushAlertService } from './pushAlert'

@Injectable({
  providedIn: 'root',
})
export class MainWorkflow {
  swapService: SwapHistoryService
  signalService: Signals
  backtestService: BacktestService
  config: Arguments
  pushAlertService: PushAlertService

  constructor(
    swapService: SwapHistoryService,
    signalService: Signals,
    backtestService: BacktestService,
    pushAlertService: PushAlertService,
    @Inject(ConfigToken) config: Arguments
  ) {
    this.swapService = swapService
    this.signalService = signalService
    this.backtestService = backtestService
    this.pushAlertService = pushAlertService
    this.config = config
  }

  public async run(): Promise<boolean> {
    // get swap history
    const allSwaps = await this.GetSwapHistory(
      this.config.token0 as Token,
      this.config.token1 as Token
    )
    if (allSwaps.length === 0) {
      console.log('no swaps found')
      return false
    }

    // load dataframe
    const df = await loadDataFrame(JSON.stringify(allSwaps))

    // backtest unless a test set has already been pre-selected
    const testSet: TestSet = this.backTest(df)

    // generate signals from the selected test set
    console.log('generating signals for test set %s', colorize(testSet))
    const result = this.signalService.generateSignals(testSet, df)
    if (result === null) {
      throw new Error('invalid signals')
    }

    // check the result, get the most recent trades and perform any push alerts
    const [dfSignals, valid] = result
    console.log(colorize(dfSignals.tail(1).to_json()))
    const { mostRecentPosition, mostRecentTrade } =
      this.signalService.getMostRecentTrades(dfSignals)
    if (!valid) {
      throw new Error('invalid signals')
    }

    // push either a heartbeat or an alert
    const pushDirection = mostRecentTrade[1] === 1 ? 'Buy' : 'Sell'
    if (mostRecentPosition[1] in [1, -1]) {
      await this.pushAlertService.pushAlert(pushDirection, mostRecentPosition[0])
    } else {
      await this.pushAlertService.pushHeartbeat(pushDirection, mostRecentTrade[0])
    }

    return true
  }

  public async GetSwapHistory(token0: Token, token1: Token): Promise<Swap[]> {
    const starterTimestamp = new Date(
      new Date().setUTCHours(0, 0, 0, 1) - dayInMS * this.config.daysToFetch
    )

    const swaps = await this.swapService.GetSwapsSince(token0, token1, starterTimestamp)

    return swaps
  }

  private backTest(df: DataFrame): TestSet {
    let testSet: TestSet | null = null
    if (this.config.strategyName === undefined) {
      console.log('backtesting')
      const result = this.backtestService.backTest(df)
      if (!result || result[0] === null) {
        throw new Error('no valid test sets')
      }

      testSet = result[0]
    } else {
      console.log('using pre-selected test set')
      if (
        this.config.strategySignalColumn === undefined ||
        this.config.strategyWmaColumn === undefined ||
        this.config.strategyName === undefined
      ) {
        throw new Error('invalid test set')
      }
      testSet = {
        signalColumnIn: this.config.strategySignalColumn,
        wmaColumnIn: this.config.strategyWmaColumn,
        testStrategy: this.config.strategyName as TestStrategy,
      }
    }

    return testSet
  }
}
