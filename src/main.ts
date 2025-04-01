import { ChartService } from './chart'
import { Inject, Injectable } from '@angular/core'
import type { Arguments, DataFrame, PortfolioRecord, TestSet, TestStrategy } from './types'
import { dayInMS } from './constants'
import { Signals } from './signals'
import { BacktestService } from './backtest'
import { color, colorize } from 'json-colorizer'
import { ConfigToken } from './config'
import { PushAlertService } from './pushAlert'
import { toRecords } from './pytrade'

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
    const testSet: TestSet = await this.backTest(df_ohlc)

    // generate signals from the selected test set
    console.log('generating signals for test set %s', colorize(testSet))
    const result = this.signalService.generateSignals(testSet, df_ohlc)
    if (result === null) {
      throw new Error('invalid signals')
    }
    console.log(result[0].tail(10).to_csv())

    // check the result, get the most recent trades and fail if invalid
    const [dfSignals, valid] = result
    // convert to records from the dataframe
    const records = toRecords(dfSignals)

    const [mostRecentPosition, mostRecentTrade] = this.signalService.getMostRecentTrades(records)
    if (!valid) {
      throw new Error('invalid signals')
    }
    console.log(colorize(mostRecentTrade))

    // push either a heartbeat or an alert
    if (mostRecentTrade === undefined) {
      console.log('no trades found')
      return false
    }
    const pushDirection = mostRecentTrade.position === 1 ? 'Buy' : 'Sell'
    if (mostRecentPosition.position !== 0) {
      await this.pushAlertService.pushAlert(pushDirection, mostRecentTrade.timestamp)
    } else {
      await this.pushAlertService.pushHeartbeat(pushDirection, mostRecentTrade.timestamp)
    }

    return true
  }

  public async GetOHLC(): Promise<DataFrame> {
    const starterTimestamp = new Date(
      new Date().setUTCHours(0, 0, 0, 1) - dayInMS * this.config.daysToFetch
    )
    console.log('starterTimestamp: %s', starterTimestamp)

    const df_ohlc = await this.swapService.GetOHLC(starterTimestamp)

    return df_ohlc
  }

  private async backTest(df: DataFrame): Promise<TestSet> {
    let testSet: TestSet | null = null
    if (this.config.strategyName === undefined) {
      console.log('backtesting')
      const result = await this.backtestService.backTest(df)
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
