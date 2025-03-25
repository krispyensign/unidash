import { generateSignals } from "./signals"
import { Strategy } from "./strategy"
import { DataFrame, TestStrategy, TestSet } from "./types"

export function backTest(df: DataFrame) {
  const points = [
    'open',
    'close',
    'high',
    'low',
    'ha_open',
    'ha_close',
    'ha_high',
    'ha_low',
    'ha_bid_open',
    'ha_bid_close',
    'ha_bid_high',
    'ha_bid_low',
    'ha_ask_open',
    'ha_ask_close',
    'ha_ask_high',
    'ha_ask_low',
    'ask_open',
    'ask_close',
    'ask_high',
    'ask_low',
    'bid_open',
    'bid_close',
    'bid_high',
    'bid_low',
  ]
  const strategyName = [
    TestStrategy.WMA_HEIKEN_ASHI,
    TestStrategy.IWMA_HEIKEN_ASHI,
    TestStrategy.WMA_HEIKEN_ASHI_INVERSE,
    TestStrategy.IWMA_HEIKEN_ASHI_INVERSE,
  ]

  const testSets: TestSet[] = []
  for (const signalPoint of points) {
    for (const wmaPoint of points) {
      for (const strategy of strategyName) {
        let testSet: TestSet = {
          signalColumnIn: signalPoint,
          wmaColumnIn: wmaPoint,
          testStrategy: strategy,
        }
        testSets.push(testSet)
      }
    }
  }

  const strategyService = new Strategy()

  let profit_results: [TestSet, DataFrame, number, number][] = []
  // let loss_results: [TestSet, DataFrame, number, number][] = []

  for (const ts of testSets) {
    //console.log(ts)
    let [result, profitQuote, profitBase] = generateSignals(ts, df, strategyService)
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