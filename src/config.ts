import { InjectionToken } from '@angular/core'
import { Arguments } from './types'
import yargs from 'yargs'
import { points, strategies } from './constants'

export const ConfigToken = new InjectionToken<Arguments>('app.config description')

export function getArgs(): Arguments {
  console.log('Unidash v0.1.0')
  console.log(process.cwd())
  console.log()
  return yargs(process.argv.slice(2))
    .config()
    .options({
      token0: {
        type: 'string',
        demandOption: true,
        description: 'The contract address of the first token',
      },
      token1: {
        type: 'string',
        demandOption: true,
        description: 'The contract address of the second token',
      },
      graphqlEndpoint: {
        type: 'string',
        demandOption: true,
        description: 'The Uniswap v3 or v4 GraphQL endpoint to use',
      },
      mongodbEndpoint: {
        type: 'string',
        demandOption: true,
        description: 'The MongoDB endpoint to use',
      },
      daysToFetch: {
        type: 'number',
        default: 60,
        description:
          'The number of days to fetch data for the token pair from the Uniswap subgraph',
      },
      heartbeat: { type: 'string', description: 'The ntfy heartbeat topic' },
      priority: { type: 'string', description: 'The ntfy priority topic' },
      strategyWmaColumn: {
        type: 'string',
        description: `The pandas column name for WMA calculations. This can be one of:
        ${points.join(', ')}`,
      },
      strategySignalColumn: {
        type: 'string',
        description: `The pandas column name for the signal comparison against the WMA. This can be 
        one of:
          ${points.join(', ')}`,
      },
      strategyName: {
        type: 'string',
        description: `The strategy name. This one of:
          ${strategies.join(', ')}`,
      },
    })
    .parseSync()
}
