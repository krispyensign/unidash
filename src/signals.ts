import { Injectable } from '@angular/core'
import { chart, util } from './pytrade'
import { Strategy } from './strategy'
import type { TestSet, DataFrame } from './types'

@Injectable({
  providedIn: 'root',
})
export class Signals {
  strategy: Strategy

  constructor(strategy: Strategy) {
    this.strategy = strategy
  }

  public getMostRecentTrades(dfSignals: DataFrame): {
    mostRecentPosition: [string, number]
    mostRecentTrade: [number, number]
  } {
    let mostRecentTrades: [number, number][] = []
    const recentSignals = JSON.parse(dfSignals.to_json())
    const positionRows: [string, number | null][] = Object.entries(recentSignals['position'])

    // get most recent position
    const mostRecentPosition: [string, number] = positionRows[positionRows.length - 1] as [
      string,
      number,
    ]

    // get most recent trades
    for (const signal of positionRows) {
      if (signal[1] === 0 || signal[1] === null) {
        continue
      }
      mostRecentTrades = mostRecentTrades.concat([[parseInt(signal[0]), signal[1] as number]])
    }
    const mostRecentTrade = mostRecentTrades[mostRecentTrades.length - 1]

    // print most recent trades
    for (let i = 0; i < 5; i++) {
      if (i >= mostRecentTrades.length) {
        break
      }
      const trade = mostRecentTrades[mostRecentTrades.length - 1 - i]
      console.log('%s %d', new Date(trade[0]).toLocaleString(), trade[1])
    }

    return { mostRecentPosition, mostRecentTrade }
  }

  /**
   * Generate trading signals using the specified strategy and parameters.
   *
   * @param ts The test set containing parameters for signal generation.
   * @param df The input DataFrame containing the trading data.
   * @param strategy The strategy to use for generating signals.
   * @returns A tuple containing the DataFrame with the trading signals, a boolean indicating
   * if the DataFrame is valid, the profit for the quote asset, and the profit for the base asset.
   */
  public generateSignals(
    ts: TestSet,
    df_ohlc: DataFrame
  ): [DataFrame, boolean, number, number] | null {
    let df_ha: DataFrame
    switch (ts.testStrategy) {
      case 'WMA_HEIKEN_ASHI':
        df_ha = this.strategy.wmaHeikenAshiStrategy(ts, df_ohlc)
        break
      case 'IWMA_HEIKEN_ASHI':
        df_ha = this.strategy.iwmaHeikenAshiStrategy(ts, df_ohlc)
        break
      case 'WMA_HEIKEN_ASHI_INVERSE':
        df_ha = this.strategy.wmaHeikenAshiInverseStrategy(ts, df_ohlc)
        break
      case 'IWMA_HEIKEN_ASHI_INVERSE':
        df_ha = this.strategy.iwmaHeikenAshiInverseStrategy(ts, df_ohlc)
        break
      case 'WMA_OHLC':
        df_ha = this.strategy.wmaOhlcStrategy(ts, df_ohlc)
        break
      case 'IWMA_OHLC':
        df_ha = this.strategy.iwmaOhlcStrategy(ts, df_ohlc)
        break
      case 'WMA_OHLC_INVERSE':
        df_ha = this.strategy.wmaOhlcInverseStrategy(ts, df_ohlc)
        break
      case 'IWMA_OHLC_INVERSE':
        df_ha = this.strategy.iwmaOhlcInverseStrategy(ts, df_ohlc)
        break
    }

    // portfolio calculation
    const [portfolio, isValid, profitQuote, profitBase] = util.portfolio(df_ha)

    // return the portfolio and profit
    return [portfolio, isValid, profitQuote, profitBase]
  }
}
