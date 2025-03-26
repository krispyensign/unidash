import { chart, util } from './pytrade'
import { Strategy } from './strategy'
import type { TestSet, DataFrame } from './types'

/**
 * Generate trading signals using the specified strategy and parameters.
 *
 * @param ts The test set containing parameters for signal generation.
 * @param df The input DataFrame containing the trading data.
 * @param strategy The strategy to use for generating signals.
 * @returns A tuple containing the DataFrame with the trading signals, a boolean indicating
 * if the DataFrame is valid, the profit for the quote asset, and the profit for the base asset.
 */
export function generateSignals(
  ts: TestSet,
  df: DataFrame,
  strategy: Strategy
): [DataFrame, boolean, number, number] {
  // resample to 5 min
  const df_ohlc = chart.ohlc(df, '5Min')
  // console.log("=========resampled=========")
  // console.log(df_ohlc.tail(1).to_csv())

  let df_ha: DataFrame
  switch (ts.testStrategy) {
    case 'WMA_HEIKEN_ASHI':
      df_ha = strategy.wmaHeikenAshiStrategy(ts, df_ohlc)
      break
    case 'IWMA_HEIKEN_ASHI':
      df_ha = strategy.iwmaHeikenAshiStrategy(ts, df_ohlc)
      break
    case 'WMA_HEIKEN_ASHI_INVERSE':
      df_ha = strategy.wmaHeikenAshiInverseStrategy(ts, df_ohlc)
      break
    case 'IWMA_HEIKEN_ASHI_INVERSE':
      df_ha = strategy.iwmaHeikenAshiInverseStrategy(ts, df_ohlc)
      break
    case 'WMA_OHLC':
      df_ha = strategy.wmaOhlcStrategy(ts, df_ohlc)
      break
    case 'IWMA_OHLC':
      df_ha = strategy.iwmaOhlcStrategy(ts, df_ohlc)
      break
    case 'WMA_OHLC_INVERSE':
      df_ha = strategy.wmaOhlcInverseStrategy(ts, df_ohlc)
      break
    case 'IWMA_OHLC_INVERSE':
      df_ha = strategy.iwmaOhlcInverseStrategy(ts, df_ohlc)
      break
  }

  // portfolio calculation
  const [portfolio, isValid, profitQuote, profitBase] = util.portfolio(df_ha)
  // console.log("=========portfolio=========")
  // console.log(portfolio.tail(1).to_csv())

  // return the portfolio and profit
  return [portfolio, isValid, profitQuote, profitBase]
}
