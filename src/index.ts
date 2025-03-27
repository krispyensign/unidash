import { loadPy } from './pytrade'
import { SwapHistoryService } from './swapshistory'
import { DbService } from './db'
import { Injector } from '@angular/core'
import { Strategy } from './strategy'
import { Signals } from './signals'
import { BacktestService } from './backtest'
import { MainWorkflow } from './main'

const delay = (ms: number | undefined): Promise<unknown> =>
  new Promise(resolve => setTimeout(resolve, ms))

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

  // start the main poller
  const success = true
  while (success) {
    try {
      // run the program
      const success = await mainWorkflow.run()
      if (!success) {
        throw new Error('something went wrong')
      }

      // wait till the next run
      console.log('waiting for next minute')
      await delay(1000 * 60)
    } catch (e) {
      // alert for errors
      console.log(e)
      // await pushAlertError(e)
      break
    }
  }
}

main().finally(() => process.exit(0))
