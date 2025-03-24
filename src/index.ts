import { GraphQLClient, gql } from 'graphql-request'
import { Cache } from 'file-system-cache'
import { Data, Swap, TransformedSwap, DataFrame, TestSet, TestStrategy } from './types'
import { Strategy } from './strategy'
import { chart, loadDataFrame, loadPy, util } from './pytrade'

// Define the GraphQL endpoint for the Uniswap subgraph v3
import { apiKey } from './private.json'
export const endpoint = `https://gateway.thegraph.com/api/${apiKey}/subgraphs/id/HMuAwufqZ1YCRmzL2SfHTVkzZovC9VL2UAKhjvRqKiR1`

/**
 * Fetches swap data for specified tokens from a GraphQL endpoint.
 *
 * This function queries the Uniswap subgraph to retrieve swap data for the
 * specified token pair over the last 20 days. It makes 20 separate requests,
 * each fetching swaps for one day, and aggregates the results.
 *
 * TODO: Cache each day individually so that it doesn't have to fetch the full
 * X number of days every time.  This way this can be configurable to download
 * any number of days.
 *
 * @param token0 The address of the first token in the pair.
 * @param token1 The address of the second token in the pair.
 * @returns A promise that resolves to an array of TransformedSwap objects,
 *          containing the timestamp, amount0, and amount1 for each swap.
 */
async function GetSwaps(token0: string, token1: string): Promise<TransformedSwap[]> {
  // Create a cache
  const cache = new Cache({
    ttl: 360,
  })

  // Check if data is already in cache
  let outData: TransformedSwap[] = await cache.get('foo')
  if (outData) {
    return outData
  }

  // If not, fetch data
  outData = []

  // Create a GraphQL client
  const client = new GraphQLClient(endpoint)

  // call endpoint 20 times for each of the 20 days
  const now = Math.floor(new Date().getTime() / 1000)
  const dayInSecs = 86400
  const numDays = 20
  for (let i = now; i > now - dayInSecs * numDays; i -= dayInSecs) {
    // Define the GraphQL query
    const query = gql`
        {
            swaps(
                where: {
                    token0: "${token0}",
                    token1: "${token1}",
                    timestamp_gt: "${i}"
                }
                orderBy: timestamp
                orderDirection: desc
            ) {
                timestamp
                amount0
                amount1
            }
        }
        `

    const data: Data = await client.request(query)

    outData = outData.concat(
      data.swaps.map((swap: Swap) => {
        return {
          timestamp: parseInt(swap.timestamp),
          amount0: parseFloat(swap.amount0),
          amount1: parseFloat(swap.amount1),
        }
      })
    )
  }

  await cache.set('foo', outData)

  console.log(outData.length)
  return outData
}

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
function generateSignals(
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

/**
 * Fetches the swap data from the subgraph and converts it to a Pandas DataFrame.
 *
 * The data is fetched for the given token pair and then converted to a JSON string.
 * The JSON string is then used to create a Pandas DataFrame which is set to have the
 * 'timestamp' column as the index.
 *
 * @returns A promise that resolves to the DataFrame.
 */
async function fetchData(): Promise<DataFrame> {
  // fetch swap data from subgraph
  const data = await GetSwaps(
    '0x4200000000000000000000000000000000000006',
    '0x570b1533F6dAa82814B25B62B5c7c4c55eB83947'
  )
  const jsonData = JSON.stringify(data)

  // convert to dataframe
  const df = loadDataFrame(jsonData)
  return df
}

function backTest(df: DataFrame) {
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
  const trueOrFalse = [true, false]
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
    // } else {
    //     loss_results.push([ts, result, profitQuote, profitBase])
    // }
  }

  // console.log("=============================================")
  // for (const [ts, result, profitQuote, profitBase] of profit_results) {
  //     console.log(JSON.stringify(ts))
  //     console.log(result.tail(1).to_csv())
  //     console.log(`profitQuote: ${profitQuote} profitBase: ${profitBase}` )
  //     console.log("=============================================")
  // }

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

/**
 * Runs the backtesting and signal generation for all test sets.
 *
 * This function is the entry point for the script. It loads the Pyodide environment,
 * fetches swap data from the Uniswap subgraph, and runs the backtesting and signal
 * generation for all test sets. It then prints out the results of the profitable
 * and loss-making test sets.
 *
 * @returns A promise that resolves when all the test sets have been processed.
 */
async function main() {
  await loadPy()
  const df = await fetchData()
  backTest(df)
}

main()
