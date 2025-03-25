import { loadDataFrame, loadPy } from './pytrade'
import { GetSwaps } from './swaps'
import { backTest } from './backtest'
import { Token } from './types'

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
  const data = await GetSwaps(Token.WETH, Token.BOBO)

  const df = await loadDataFrame(JSON.stringify(data))

  backTest(df)
}

main()
