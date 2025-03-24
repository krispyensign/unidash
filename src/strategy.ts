import { chart, indicator } from './pytrade'
import { TestSet, DataFrame } from './types'

export class Strategy {
  /**
   * Generate trading signals using a weighted moving average (WMA) of Heikin-Ashi candlesticks.
   *
   * This function processes the input DataFrame to generate trading signals using a weighted
   * moving average (WMA) of Heikin-Ashi candlesticks. It first resamples the data to 5-minute
   * intervals, then generates Heikin-Ashi candlesticks. It then calculates the WMA of the
   * Heikin-Ashi candlesticks and generates trading signals based on the WMA. The trading
   * signals are added to the DataFrame as a new column.
   *
   * @param ts The test set containing parameters for signal generation and WMA calculation.
   * @param df The input DataFrame containing the trading data.
   * @returns A DataFrame with the trading signals added.
   */
  public wmaHeikenAshiStrategy(ts: TestSet, df: DataFrame): DataFrame {
    let df_ha = chart.heiken(df)
    df_ha = indicator.wma(df_ha, 20, ts.wmaColumnIn)
    df_ha = indicator.signal(df_ha, ts.signalColumnIn, 'WMA')
    return df_ha
  }

  /**
   * Generate trading signals using an inverse weighted moving average (WMA) of Heikin-Ashi candlesticks.
   *
   * This function processes the input DataFrame to generate trading signals using an inverse weighted
   * moving average (WMA) of Heikin-Ashi candlesticks. It first resamples the data to 5-minute intervals,
   * then generates Heikin-Ashi candlesticks. It calculates the WMA of the Heikin-Ashi candlesticks and
   * generates trading signals based on the inverse comparison of the WMA and a specified column. The
   * trading signals are added to the DataFrame as a new column.
   *
   * @param ts The test set containing parameters for signal generation and WMA calculation.
   * @param df The input DataFrame containing the trading data.
   * @returns A DataFrame with the trading signals added.
   */

  public wmaHeikenAshiInverseStrategy(ts: TestSet, df: DataFrame): DataFrame {
    let df_ha = chart.heiken(df)
    df_ha = indicator.wma(df_ha, 20, ts.wmaColumnIn)
    df_ha = indicator.signal(df_ha, 'WMA', ts.signalColumnIn)
    return df_ha
  }

  /**
   * Generate trading signals using an inverse weighted moving average (IWMA) of Heikin-Ashi candlesticks.
   *
   * This function processes the input DataFrame to generate trading signals using an inverse weighted
   * moving average (IWMA) of Heikin-Ashi candlesticks. It first resamples the data to 5-minute intervals,
   * then generates Heikin-Ashi candlesticks. It calculates the IWMA of the Heikin-Ashi candlesticks and
   * generates trading signals based on the IWMA. The trading signals are added to the DataFrame as a new column.
   *
   * @param ts The test set containing parameters for signal generation and IWMA calculation.
   * @param df The input DataFrame containing the trading data.
   * @returns A DataFrame with the trading signals added.
   */

  public iwmaHeikenAshiStrategy(ts: TestSet, df: DataFrame): DataFrame {
    let df_ha = chart.heiken(df)
    df_ha = indicator.iwma(df_ha, 20, ts.wmaColumnIn)
    df_ha = indicator.signal(df_ha, ts.signalColumnIn, 'IWMA')
    return df_ha
  }

  /**
   * Generate trading signals using an inverse weighted moving average (IWMA) of Heikin-Ashi candlesticks
   * and generate trading signals based on the inverse comparison of the IWMA and a specified column.
   *
   * This function processes the input DataFrame to generate trading signals using an inverse weighted
   * moving average (IWMA) of Heikin-Ashi candlesticks. It first resamples the data to 5-minute intervals,
   * then generates Heikin-Ashi candlesticks. It calculates the IWMA of the Heikin-Ashi candlesticks and
   * generates trading signals based on the inverse comparison of the IWMA and a specified column. The
   * trading signals are added to the DataFrame as a new column.
   *
   * @param ts The test set containing parameters for signal generation and IWMA calculation.
   * @param df The input DataFrame containing the trading data.
   * @returns A DataFrame with the trading signals added.
   */
  public iwmaHeikenAshiInverseStrategy(ts: TestSet, df: DataFrame): DataFrame {
    let df_ha = chart.heiken(df)
    df_ha = indicator.iwma(df_ha, 20, ts.wmaColumnIn)
    df_ha = indicator.signal(df_ha, 'IWMA', ts.signalColumnIn)
    return df_ha
  }
}
