import { ChartService } from './chart'
import { Inject, Injectable } from '@angular/core'
import type { Arguments, DataFrame, TestSet, TestStrategy } from './types'
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
  swapService: ChartService
  signalService: Signals
  backtestService: BacktestService
  config: Arguments
  pushAlertService: PushAlertService

  constructor(
    swapService: ChartService,
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
    // get ohlc
    const df_ohlc = await this.GetOHLC()

    // backtest unless a test set has already been pre-selected
    const testSet: TestSet = this.backTest(df_ohlc)

    // generate signals from the selected test set
    console.log('generating signals for test set %s', colorize(testSet))
    const result = this.signalService.generateSignals(testSet, df_ohlc)
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
    if (mostRecentTrade === undefined) {
      console.log('no trades found')
      return false
    }
    const pushDirection = mostRecentTrade[1] === 1 ? 'Buy' : 'Sell'
    if (mostRecentPosition[1] !== 0) {
      await this.pushAlertService.pushAlert(pushDirection, mostRecentTrade[0])
    } else {
      await this.pushAlertService.pushHeartbeat(pushDirection, mostRecentTrade[0])
    }

    return true
  }

  public async GetOHLC(): Promise<DataFrame> {
    const starterTimestamp = new Date(
      new Date().setUTCHours(0, 0, 0, 1) - dayInMS * this.config.daysToFetch
    )

    const df_ohlc = await this.swapService.GetOHLC(starterTimestamp)

    return df_ohlc
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
