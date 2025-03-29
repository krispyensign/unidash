import { colorize } from 'json-colorizer'
import type { DataFrame, TestSet } from './types'
import { points, strategies } from './constants'
import { Injectable } from '@angular/core'
import { Signals } from './signals'

function input_is_ha(column0: string, column1: string): boolean {
  return column0.startsWith('ha_') || column1.startsWith('ha_')
}

@Injectable({
  providedIn: 'root',
})
export class BacktestService {
  signals: Signals

  constructor(signals: Signals) {
    this.signals = signals
  }

  public backTest(df: DataFrame): [TestSet, DataFrame] | null {
    // generate all possible test sets
    const testSets: TestSet[] = []
    for (const signalPoint of points) {
      for (const wmaPoint of points) {
        for (const strategy of strategies) {
          // skip test set if strategy is HEIKEN_ASHI and input is not HEIKEN_ASHI columns
          if (strategy.includes('HEIKEN_ASHI') && !input_is_ha(signalPoint, wmaPoint)) {
            continue
          }

          // skip test set if strategy is OHLC and input is not OHLC columns
          if (strategy.includes('OHLC') && input_is_ha(signalPoint, wmaPoint)) {
            continue
          }

          // create test set
          const testSet: TestSet = {
            signalColumnIn: signalPoint,
            wmaColumnIn: wmaPoint,
            testStrategy: strategy,
          }
          testSets.push(testSet)
        }
      }
    }

    // run all test sets
    let k = 0
    const profit_results: [TestSet, DataFrame, number, number][] = []
    for (const ts of testSets) {
      k++

      // generate signals
      let genResult: [DataFrame, boolean, number, number] | null
      try {
        genResult = this.signals.generateSignals(ts, df)
        if (genResult === null) {
          console.log('invalid signals')
          continue
        }
      } catch (e) {
        console.log(e)
        console.log(ts)
        throw e
      }
      const [result, isValid, profitQuote, profitBase] = genResult

      // collect results
      if (profitQuote > 0 && isValid) {
        profit_results.push([ts, result, profitQuote, profitBase])
      } else if (profitBase > 0 && isValid) {
        profit_results.push([ts, result, profitQuote, profitBase])
      }

      // log progress
      if (k % 10 === 0) {
        this.logProgress(k, testSets.length, profit_results.length, ts, result)
      }
    }
    console.log('processed all test sets')

    // find maximum profit of profit_results
    const profitResult = this.findMaxProfit(profit_results)
    if (!profitResult) {
      console.log('no valid signals found')
      return null
    }
    const [max_profit_quote_ts, max_result] = profitResult

    return [max_profit_quote_ts, max_result]
  }

  private findMaxProfit(
    profit_results: [TestSet, DataFrame, number, number][]
  ): [TestSet, DataFrame] | null {
    let max_profit_quote = 0
    let max_profit_quote_ts: TestSet | undefined
    let max_result: DataFrame | undefined
    for (const [ts, result, profitQuote] of profit_results) {
      if (profitQuote > max_profit_quote) {
        max_profit_quote = profitQuote
        max_profit_quote_ts = ts
        max_result = result
      }
    }
    if (max_profit_quote_ts) {
      console.log('=============================================')
      console.log(`max profit quote: ${max_profit_quote}`)
      console.log(colorize(max_profit_quote_ts))
      console.log(colorize(max_result!.tail(1).to_json()))
      console.log('=============================================')
    }

    if (!max_profit_quote_ts || !max_result) {
      return null
    }

    return [max_profit_quote_ts, max_result]
  }

  private logProgress(
    k: number,
    testSetLength: number,
    profitResultsLength: number,
    ts: TestSet,
    result: DataFrame
  ): void {
    console.log(
      `processed ${k} of ${testSetLength} test sets. ${profitResultsLength} valid signals`
    )
    console.log(`last test set: ${colorize(ts)} ${colorize(result.tail(1).to_json())}`)
    this.signals.getMostRecentTrades(result)
  }
}
