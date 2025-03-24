import { loadPyodide } from "pyodide";

import { GraphQLClient, gql } from 'graphql-request';
import { apiKey } from './private.json'
import fs from 'fs';
import path from 'path';
import { Cache } from 'file-system-cache'

// Define the GraphQL endpoint for the Uniswap subgraph v3
const endpoint = `https://gateway.thegraph.com/api/${apiKey}/subgraphs/id/HMuAwufqZ1YCRmzL2SfHTVkzZovC9VL2UAKhjvRqKiR1`

type Swap = {
    timestamp: string
    amount0: string
    amount1: string
}

type Data = {
    swaps: Swap[]
}

type TransformedSwap = {
    timestamp: number
    amount0: number
    amount1: number
}

type DataFrame = {
    [key: string]: any
    copy(): DataFrame
    reset_index(): DataFrame
    at: any
    loc: DataFrame
    shape: [number, number]
    resample(freq: string): DataFrame
    ohlc(): DataFrame
    set_index(column: string): DataFrame
    head(count?: number): DataFrame
    tail(count?: number): DataFrame
    to_json(): string
}

type resampleFunction = (dataIn: DataFrame, timeFrame: string) => DataFrame
type heikenFunction = (dataIn: DataFrame) => DataFrame
type wmaFunction = (ha_df: DataFrame, wma_period: number, point: string) => DataFrame
type signalFunction = (ha_df: DataFrame, wma_period: number, inverted: boolean, point: string) => DataFrame
type portfolioFunction = (dataIn: DataFrame) => [DataFrame, number, number]
let resamplefn: resampleFunction
let heikenfn: heikenFunction
let wmafn: wmaFunction
let signalfn: signalFunction
let portfoliofn: portfolioFunction

let pyodide: any

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
    });

    // Check if data is already in cache
    let outData: TransformedSwap[] = await cache.get("foo");
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

        outData = outData.concat(data.swaps.map((swap: Swap) => {
            return {
                timestamp: parseInt(swap.timestamp),
                amount0: parseFloat(swap.amount0),
                amount1: parseFloat(swap.amount1)
            }
        }))

    }

    await cache.set("foo", outData)

    console.log(outData.length)
    return outData
}

/**
 * Load Python code into a Pyodide environment.
 *
 * @param pyodide The Pyodide environment to load the code into.
 * @param command The Python code to load.
 *
 * @returns The loaded Python function.
 */
async function loadCode(pyodide: any, command: string): Promise<any> {
    const filepath = path.join(__dirname, 'py', command + ".py")
    const code = fs.readFileSync(filepath, 'utf8')
    const fn = await pyodide.runPythonAsync(code)
    return fn
}

/**
 * Load the Pyodide environment with necessary packages and Python code.
 *
 * @returns A promise that resolves when the Pyodide environment is ready.
 */
async function loadPy(): Promise<void> {
    pyodide = await loadPyodide();
    await pyodide.loadPackage(["numpy", "scipy", "pandas","matplotlib", "micropip"]);
    resamplefn = await loadCode(pyodide, 'resample')
    heikenfn = await loadCode(pyodide, 'heiken_ashi')
    wmafn = await loadCode(pyodide, 'wma')
    signalfn = await loadCode(pyodide, 'signal')
    portfoliofn = await loadCode(pyodide, 'portfolio')
}

type TestSet = {
    inverted: boolean,
    signalPoint: string,
    wmaPoint: string,
}

type Portfolio = {
    timestamp: number,
    amount: number,
    value: number
    base_value: number
    inverted: boolean
}

/**
 * Generates trading signals and calculates portfolio performance.
 *
 * This function fetches swap data from the Uniswap subgraph, processes it
 * into OHLC data, and applies Heikin-Ashi candlestick transformation,
 * weighted moving average (WMA), and trading signal generation. It then
 * calculates portfolio performance based on the generated signals.
 *
 * @param ts A TestSet object containing configuration for signal generation
 *           and portfolio calculation, including whether token0 is the base,
 *           initial capital, signal inversion, and the point of Heikin-Ashi
 *           candlestick to use.
 * @returns A promise that resolves to a tuple containing a DataFrame of the
 *          portfolio and the calculated profit as a number.
 */

async function generateSignals(ts: TestSet): Promise<[DataFrame, number, number]> {
    // fetch swap data from subgraph
    const data = await GetSwaps("0x4200000000000000000000000000000000000006", "0x570b1533F6dAa82814B25B62B5c7c4c55eB83947")
    const jsonData = JSON.stringify(data)
    
    // convert to dataframe
    const pd = pyodide.pyimport("pandas")
    const df: DataFrame = pd.read_json(jsonData).set_index('timestamp')

    // resample to 5 min
    const df_ohlc = resamplefn(df, '5Min')
    console.log("=========resampled=========")
    console.log(df_ohlc.tail(1).to_csv())
    // heiken-ashi
    let df_ha = heikenfn(df_ohlc)
    console.log("=========heiken-ashi=========")
    console.log(df_ha.tail(1).to_csv())
    // weighted moving average
    df_ha = wmafn(df_ha, 20, ts.wmaPoint)
    console.log("=========wma=========")
    console.log(df_ha.tail(1).to_csv())
    // signal generation
    df_ha = signalfn(df_ha, 20, ts.inverted, ts.signalPoint)
    console.log("=========signal=========")
    console.log(df_ha.tail(1).to_csv())
    // portfolio calculation
    const [portfolio, profitQuote, profitBase] = portfoliofn(df_ha)
    console.log("=========portfolio=========")
    console.log(portfolio.tail(1).to_csv())

    // return the portfolio and profit
    return [portfolio, profitQuote, profitBase]
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

    const points = [
        'open', 'close', 'high', 'low',
        'ha_open', 'ha_close', 'ha_high', 'ha_low',
        'ha_bid_open', 'ha_bid_close', 'ha_bid_high', 'ha_bid_low',
        'ha_ask_open', 'ha_ask_close', 'ha_ask_high', 'ha_ask_low',
        'ask_open', 'ask_close', 'ask_high', 'ask_low',
        'bid_open', 'bid_close', 'bid_high', 'bid_low',
    ]
    const trueOrFalse = [true, false]

    const testSets: TestSet[] = []
    for (const inverted of trueOrFalse) {
        for (const signalPoint of points) {
            for (const wmaPoint of points) {
                testSets.push({inverted, signalPoint, wmaPoint})
            }
        }
    }

    let profit_results: [TestSet, DataFrame, number, number][] = []
    let loss_results: [TestSet, DataFrame, number, number][] = []

    for (const ts of testSets) {
        //console.log(ts)
        let [result, profitQuote, profitBase] = await generateSignals(ts)
        if (profitQuote > 0) {
            profit_results.push([ts, result, profitQuote, profitBase])
        } else if (profitBase > 0) {
            profit_results.push([ts, result, profitQuote, profitBase])
        } else {
            loss_results.push([ts, result, profitQuote, profitBase])
        }
    }

    console.log("=============================================")
    for (const [ts, result, profitQuote, profitBase] of profit_results) {
        console.log(JSON.stringify(ts))
        console.log(result.tail(1).to_csv())
        console.log(`profitQuote: ${profitQuote} profitBase: ${profitBase}` )
        console.log("=============================================")
    }

    // find maximum profit of profit_results
    let max_profit_quote = 0
    let max_profit_quote_ts: TestSet | undefined
    let max_result_quote: DataFrame | undefined
    for (const [ts, result, profitQuote, ] of profit_results) {
        if (profitQuote > max_profit_quote) {
            max_profit_quote = profitQuote
            max_profit_quote_ts = ts
            max_result_quote = result
        }
    }

    console.log("=============================================")
    console.log(`max profit quote: ${max_profit_quote}`) 
    console.log(JSON.stringify(max_profit_quote_ts))
    console.log(max_result_quote?.tail(1)?.to_csv())
    console.log("=============================================")

    let max_profit_base = 0
    let max_profit_base_ts: TestSet | undefined
    let max_result_base: DataFrame | undefined
    for (const [ts, result, profitQuote, profitBase] of profit_results) {
        if (profitBase > max_profit_base) {
            max_profit_base = profitBase
            max_profit_base_ts = ts
            max_result_base = result
        }
    }

    console.log("=============================================")
    console.log(`max profit base: ${max_profit_base}`) 
    console.log(JSON.stringify(max_profit_base_ts))
    console.log(max_result_base?.tail(1)?.to_csv())
    console.log("=============================================")
}

main()