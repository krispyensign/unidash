import { loadDataFrame, loadPy } from './pytrade'
import { GetSwaps } from './swaps'
import { backTest } from './backtest'

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
async function main(): Promise<void> {
  await loadPy()
  const data = await GetSwaps(
    '0x4200000000000000000000000000000000000006',
    '0x570b1533F6dAa82814B25B62B5c7c4c55eB83947'
  )

  const df = await loadDataFrame(JSON.stringify(data))

  backTest(df)
}

main()
