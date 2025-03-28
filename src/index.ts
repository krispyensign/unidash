import { loadPy } from './pytrade'
import { SwapHistoryService } from './swapshistory'
import { DbService } from './db'
import { Injector } from '@angular/core'
import { Strategy } from './strategy'
import { Signals } from './signals'
import { BacktestService } from './backtest'
import { MainWorkflow } from './main'
import { pushAlertError } from './pushAlert'

async function main(): Promise<void> {
  // load python environment
  await loadPy()

  // setup dep injections
  const injector = Injector.create({
    providers: [
      { provide: DbService, deps: [] },
      { provide: Strategy, deps: [] },
      { provide: SwapHistoryService, deps: [DbService] },
      { provide: Signals, deps: [Strategy] },
      { provide: BacktestService, deps: [Signals] },
      { provide: MainWorkflow, deps: [SwapHistoryService, Signals, BacktestService] },
    ],
  })

  // get the main workflow
  const mainWorkflow = injector.get(MainWorkflow)

  try {
    // run the program
    const success = await mainWorkflow.run()
    if (!success) {
      throw new Error('something went wrong')
    }
  } catch (e) {
    // alert for errors
    console.log(e)
    await pushAlertError(e)
  }
}

main().finally(() => process.exit(0))
