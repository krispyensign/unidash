import path from 'path'
import { loadPyodide, PyodideInterface } from 'pyodide'
import type {
  DataFrame,
  PortfolioRecord,
  PythonFunc,
  TradingChart,
  TradingIndicator,
  TradingUtil,
} from './types'
import fs from 'fs'

type Pandas = {
  read_json: (json: string) => DataFrame
}

let pyodide: PyodideInterface
let pd: Pandas

export let indicator: TradingIndicator
export let chart: TradingChart
export let util: TradingUtil

export async function loadDataFrame(jsonData: string): Promise<DataFrame> {
  const df: DataFrame = await pyodide.runPythonAsync(`
    import pandas as pd
    pd.read_json('${jsonData}').drop_duplicates().set_index('timestamp').sort_index()
    `)
  console.log(df.tail(1).to_csv())
  return df
}

export function toRecords(df: DataFrame): PortfolioRecord[] {
  const globals = pyodide.toPy({ df: df })
  const records = pyodide.runPython(
    `
    import pandas as pd

    df_copy = df.copy()
    df_copy.reset_index(inplace=True)

    df_copy.to_json(orient='records')
  `,
    { globals }
  )

  return JSON.parse(records)
}

/**
 * Load Python code into a Pyodide environment.
 *
 * @param pyodide The Pyodide environment to load the code into.
 * @param command The Python code to load.
 *
 * @returns The loaded Python function.
 */
async function loadCode<T>(command: T): Promise<Extract<PythonFunc, { kind: T }>> {
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
  await pyodide.loadPackage(['numpy', 'pandas'])

  chart = {
    ohlc: await loadCode('ohlc'),
    heiken: await loadCode('heiken_ashi'),
  }

  indicator = {
    wma: await loadCode('wma'),
    iwma: await loadCode('iwma'),
    signal_compare: await loadCode('signal_compare'),
  }

  util = {
    portfolio: await loadCode('portfolio'),
  }

  pd = await pyodide.pyimport('pandas')
}
