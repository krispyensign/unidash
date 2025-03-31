import { loadPy } from './pytrade'
import { ChartService } from './chart'
import { DbService } from './db'
import { Injector } from '@angular/core'
import { Strategy } from './strategy'
import { Signals } from './signals'
import { BacktestService } from './backtest'
import { MainWorkflow } from './main'
import { PushAlertService } from './pushAlert'
import { ConfigToken, getArgs } from './config'

async function app(): Promise<void> {
  // load the config
  const args = getArgs()
  console.log(args)

  // load python environment
  await loadPy()

  // setup dep injections
  const injector = Injector.create({
    providers: [
      { provide: ConfigToken, useValue: args },
      { provide: PushAlertService, deps: [ConfigToken] },
      { provide: DbService, deps: [ConfigToken] },
      { provide: Strategy, deps: [] },
      { provide: ChartService, deps: [DbService, ConfigToken] },
      { provide: Signals, deps: [Strategy] },
      { provide: BacktestService, deps: [Signals] },
      {
        provide: MainWorkflow,
        deps: [ChartService, Signals, BacktestService, PushAlertService, ConfigToken],
      },
    ],
  })

  // get the main workflow
  const mainWorkflow = injector.get(MainWorkflow)

  // run the program
  try {
    const success = await mainWorkflow.run()
    if (!success) {
      throw new Error('something went wrong')
    }
  } catch (e) {
    // alert for errors
    console.log(e)
    await injector.get(PushAlertService).pushAlertError(e)
  }
}

app().finally(() => process.exit(0))
