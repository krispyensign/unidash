import path from 'path'
import { loadPyodide } from 'pyodide'
import { DataFrame, TradingChart, TradingIndicator, TradingUtil } from './types'
import fs from 'fs'

let pyodide: any
let pd: any

export let indicator: TradingIndicator
export let chart: TradingChart
export let util: TradingUtil

export async function loadDataFrame(jsonData: string): Promise<DataFrame> {
  const df: DataFrame = pd.read_json(jsonData).set_index('timestamp')
  return df
}

/**
 * Load Python code into a Pyodide environment.
 *
 * @param pyodide The Pyodide environment to load the code into.
 * @param command The Python code to load.
 *
 * @returns The loaded Python function.
 */
async function loadCode(command: string): Promise<any> {
  const filepath = path.join(__dirname, 'py', command + '.py')
  const code = fs.readFileSync(filepath, 'utf8')
  const fn = await pyodide.runPythonAsync(code)
  return fn
}

/**
 * Load the Pyodide environment with necessary packages and Python code.
 *
 * @returns A promise that resolves when the Pyodide environment is ready.
 */
export async function loadPy(): Promise<void> {
  pyodide = await loadPyodide()
  await pyodide.loadPackage(['numpy', 'scipy', 'pandas'])

  chart.ohlc = await loadCode('ohlc')
  chart.heiken = await loadCode('heiken_ashi')

  indicator.wma = await loadCode('wma')
  indicator.iwma = await loadCode('iwma')
  indicator.signal = await loadCode('signal')

  util.portfolio = await loadCode('portfolio')

  pd = await pyodide.pyimport('pandas')
}
