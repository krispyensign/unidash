import { colorize } from 'json-colorizer'
import { Strategy } from './strategy'
import type { TestStrategy, DataFrame, TestSet } from './types'
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

  /**
   * Performs backtesting on a DataFrame using a variety of strategies and signal points.
   *
   * This function generates all possible test sets by iterating over predefined signal
   * points, WMA points, and strategies. It filters out invalid test sets where the strategy
   * requires Heiken-Ashi columns but the input columns do not match. For each valid test set,
   * it runs the signal generation process and collects the results that yield positive profits
   * in either quote or base currency. It then identifies and logs the test set and results
   * with the maximum profit for both quote and base currencies.
   *
   * @param df The input DataFrame containing trading data to be used for backtesting.  The columns
   * expected in the dataframe are timestamp, amount0, and amount1
   */
  public backTest(df: DataFrame): [TestSet, DataFrame] | undefined {
    // generate all possible test sets
    const testSets: TestSet[] = []
    for (const signalPoint of points) {
      for (const wmaPoint of points) {
        for (const strategy of strategies) {
          // skip test set if strategy is HEIKEN_ASHI and input is not HEIKEN_ASHI columns
          if (strategy.includes('HEIKEN_ASHI') && !input_is_ha(signalPoint, wmaPoint)) {
            continue
          }

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
    const strategyService = new Strategy()

    let k = 0
    const profit_results: [TestSet, DataFrame, number, number][] = []
    for (const ts of testSets) {
      k++
      if (k % 10 === 0) {
        console.log(`processed ${k} of ${testSets.length} test sets`)
      }
      const [result, isValid, profitQuote, profitBase] = this.signals.generateSignals(ts, df)
      if (profitQuote > 0 && isValid) {
        profit_results.push([ts, result, profitQuote, profitBase])
      } else if (profitBase > 0 && isValid) {
        profit_results.push([ts, result, profitQuote, profitBase])
      }
    }
    console.log('processed all test sets')

    // find maximum profit of profit_results
    let max_profit_quote = 0
    let max_profit_quote_ts: TestSet | undefined
    let max_result_quote: DataFrame | undefined
    for (const [ts, result, profitQuote] of profit_results) {
      if (profitQuote > max_profit_quote) {
        max_profit_quote = profitQuote
        max_profit_quote_ts = ts
        max_result_quote = result
      }
    }

    if (max_profit_quote_ts) {
      console.log('=============================================')
      console.log(`max profit quote: ${max_profit_quote}`)
      console.log(colorize(max_profit_quote_ts))
      console.log(colorize(max_result_quote!.tail(1).to_json()))
      console.log('=============================================')
    }

    let max_profit_base = 0
    let max_profit_base_ts: TestSet | undefined
    let max_result_base: DataFrame | undefined
    for (const [ts, result, , profitBase] of profit_results) {
      if (profitBase > max_profit_base) {
        max_profit_base = profitBase
        max_profit_base_ts = ts
        max_result_base = result
      }
    }

    if (max_profit_base_ts) {
      console.log('=============================================')
      console.log(`max profit base: ${max_profit_base}`)
      console.log(colorize(max_profit_base_ts))
      console.log(colorize(max_result_base!.tail(1).to_json()))
      console.log('=============================================')
    }

    if (!max_profit_quote_ts || !max_result_quote) {
      return undefined
    }

    return [max_profit_quote_ts, max_result_quote]
  }
}
