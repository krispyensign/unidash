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
import { t } from 'file-system-cache/lib/common.t'

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

    // check the result, get the most recent trades and fail if invalid
    // convert to records from the dataframe
    const [dfSignals, valid] = result
    const records = toRecords(dfSignals)
    if (!valid) {
      console.log(colorize(records.slice(-1)))
      console.log('invalid signals')
      return false
    }

    // get the trades from the records
    const trades = records.filter((record, index) => {
      // if (record.position !== null && record.position !== 0) {
      //   console.log(record.position, index)
      // }
      return record.position !== null && record.position !== 0
    })
    if (trades.length === 0) {
      console.log('no trades found')
      return false
    }

    // format and print the most recent trades
    console.log(
      trades
        .slice(-5, trades.length)
        .map(record => {
          const direction = record.position === 1 ? 'Buy' : 'Sell'
          return `${direction} ${new Date(record.timestamp)}`
        })
        .join('\n')
    )

    const mostRecentTrade = trades.slice(-1)[0]
    const mostRecentPosition = records.slice(-1)[0]
    const pushDirection = mostRecentTrade.position === 1 ? 'Buy' : 'Sell'
    if (mostRecentPosition.position !== 0 && mostRecentPosition.position !== null) {
      await this.pushAlertService.pushAlert(pushDirection, mostRecentTrade.timestamp)
    } else {
      await this.pushAlertService.pushHeartbeat(pushDirection, mostRecentTrade.timestamp)
    }
    console.log(colorize(records.slice(-1)))

    return true
  }

  public async GetOHLC(): Promise<DataFrame> {
    const starterTimestamp = new Date(
      new Date().setUTCHours(0, 0, 0, 1) - dayInMS * this.config.daysToFetch
    )
    // console.log('starterTimestamp: %s', starterTimestamp)

    const df_ohlc = await this.swapService.GetOHLC(starterTimestamp, this.config.offset)

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
      // console.log('using pre-selected test set')
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
        period: this.config.strategyWmaPeriod,
      }
    }

    return testSet
  }
}
