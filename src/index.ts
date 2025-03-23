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
    at: DataFrame
    loc: DataFrame
    shape: [number, number]
    resample(freq: string): DataFrame
    ohlc(): DataFrame
    set_index(column: string): DataFrame
    head(count?: number): DataFrame
    tail(count?: number): DataFrame
    to_json(): string
}

type resampleFunction = (dataIn: DataFrame, timeFrame: string, token0IsBase: boolean) => DataFrame
type heikenFunction = (dataIn: DataFrame) => DataFrame
type wmaFunction = (ha_df: DataFrame, wma_period: number) => DataFrame
type signalFunction = (ha_df: DataFrame, wma_period: number) => DataFrame
type portfolioFunction = (dataIn: DataFrame, capital0: number) => DataFrame
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
 * @param token0 The address of the first token in the pair.
 * @param token1 The address of the second token in the pair.
 * @returns A promise that resolves to an array of TransformedSwap objects,
 *          containing the timestamp, amount0, and amount1 for each swap.
 */
async function GetSwaps(token0: string, token1: string): Promise<TransformedSwap[]> {
    const cache = new Cache({
        ttl: 360,              
    });
    let outData: TransformedSwap[] = await cache.get("foo");
    if (outData) {
        return outData
    }

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

async function generateSignals() {
    const data = await GetSwaps("0x4200000000000000000000000000000000000006", "0x570b1533F6dAa82814B25B62B5c7c4c55eB83947")
    const jsonData = JSON.stringify(data)
    
    const pd = pyodide.pyimport("pandas")
    const df: DataFrame = pd.read_json(jsonData).set_index('timestamp')

    const df_ohlc = resamplefn(df, '5Min', true)

    let df_ha = heikenfn(df_ohlc)
    df_ha = wmafn(df_ha, 20)
    df_ha = signalfn(df_ha, 20)

    const portfolio = portfoliofn(df_ha, 480869000)
    console.log(portfolio.tail(1).to_csv())
}

async function main() {
    await loadPy()
    await generateSignals()
}

main()