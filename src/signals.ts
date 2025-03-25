import { chart, util } from './pytrade'
import { Strategy } from './strategy'
import { TestSet, DataFrame, TestStrategy } from './types'

/**
 * Generates trading signals and calculates portfolio values based on the provided test set and data.
 *
 * This function processes the input DataFrame to generate trading signals using Heikin-Ashi candlesticks
 * and a weighted moving average. It then calculates the resulting portfolio values.
 *
 * The process includes:
 * 1. Resampling the data to 5-minute intervals.
 * 2. Generating Heikin-Ashi candlesticks.
 * 3. Calculating the weighted moving average (WMA).
 * 4. Generating trading signals based on the WMA and test set parameters.
 * 5. Calculating the portfolio values in terms of quote and base currencies.
 *
 * @param ts The test set containing parameters for signal generation and WMA calculation.
 * @param df The input DataFrame containing the trading data.
 * @returns A promise that resolves to a tuple containing the portfolio DataFrame,
 *          profit in the quote currency, and profit in the base currency.
 */
export function generateSignals(
  ts: TestSet,
  df: DataFrame,
  strategy: Strategy
): [DataFrame, number, number] {
  // resample to 5 min
  const df_ohlc = chart.ohlc(df, '5Min')
  // console.log("=========resampled=========")
  // console.log(df_ohlc.tail(1).to_csv())

  let df_ha: DataFrame
  switch (ts.testStrategy) {
    case TestStrategy.WMA_HEIKEN_ASHI:
      df_ha = strategy.wmaHeikenAshiStrategy(ts, df_ohlc)
      break
    case TestStrategy.IWMA_HEIKEN_ASHI:
      df_ha = strategy.iwmaHeikenAshiStrategy(ts, df_ohlc)
      break
    case TestStrategy.WMA_HEIKEN_ASHI_INVERSE:
      df_ha = strategy.wmaHeikenAshiInverseStrategy(ts, df_ohlc)
      break
    case TestStrategy.IWMA_HEIKEN_ASHI_INVERSE:
      df_ha = strategy.iwmaHeikenAshiInverseStrategy(ts, df_ohlc)
      break
  }

  // portfolio calculation
  const [portfolio, profitQuote, profitBase] = util.portfolio(df_ha)
  // console.log("=========portfolio=========")
  // console.log(portfolio.tail(1).to_csv())

  // return the portfolio and profit
  return [portfolio, profitQuote, profitBase]
}
