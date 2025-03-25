import { generateSignals } from './signals'
import { Strategy } from './strategy'
import type { TestStrategy, DataFrame, TestSet } from './types'

const points = [
  'open',
  'close',
  // 'high',
  // 'low',
  'ha_open',
  'ha_close',
  // 'ha_high',
  // 'ha_low',
  'ha_bid_open',
  'ha_bid_close',
  // 'ha_bid_high',
  // 'ha_bid_low',
  'ha_ask_open',
  'ha_ask_close',
  // 'ha_ask_high',
  // 'ha_ask_low',
  'ask_open',
  'ask_close',
  // 'ask_high',
  // 'ask_low',
  'bid_open',
  'bid_close',
  // 'bid_high',
  // 'bid_low',
]

const strategies: TestStrategy[] = [
  // 'IWMA_HEIKEN_ASHI_INVERSE',
  // 'IWMA_HEIKEN_ASHI',
  'WMA_HEIKEN_ASHI',
  'WMA_HEIKEN_ASHI_INVERSE',
]

function input_is_ha(column0: string, column1: string): boolean {
  return column0.startsWith('ha_') || column1.startsWith('ha_')
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
export function backTest(df: DataFrame): void {
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
  const profit_results: [TestSet, DataFrame, number, number][] = []
  for (const ts of testSets) {
    const [result, profitQuote, profitBase] = generateSignals(ts, df, strategyService)
    if (profitQuote > 0) {
      profit_results.push([ts, result, profitQuote, profitBase])
    } else if (profitBase > 0) {
      profit_results.push([ts, result, profitQuote, profitBase])
    }
  }

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

  console.log('=============================================')
  console.log(`max profit quote: ${max_profit_quote}`)
  console.log(JSON.stringify(max_profit_quote_ts))
  console.log(max_result_quote?.tail(1)?.to_csv())
  console.log('=============================================')

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

  console.log('=============================================')
  console.log(`max profit base: ${max_profit_base}`)
  console.log(JSON.stringify(max_profit_base_ts))
  console.log(max_result_base?.tail(1)?.to_csv())
  console.log('=============================================')
}
