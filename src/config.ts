import { InjectionToken } from '@angular/core'
import { Arguments } from './types'
import yargs from 'yargs'

export const ConfigToken = new InjectionToken<Arguments>('app.config description')

/**
 * Parse the command line arguments and return the Arguments object.
 *
 * The available options are:
 *   --token0: The address of the first token.
 *   --token1: The address of the second token.
 *   --graphqlEndpoint: The GraphQL endpoint to use.
 *   --mongodbEndpoint: The MongoDB endpoint to use.
 *   --daysToFetch: The number of days to fetch data for. Defaults to 60.
 *   --heartbeat: The string to use for the heartbeat.
 *   --priority: The string to use for the priority.
 *   --strategyWmaColumn: The string to use for the WMA column.
 *   --strategySignalColumn: The string to use for the signal column.
 *   --strategyName: The string to use for the strategy name.
 *
 * @returns The Arguments object.
 */

export function getArgs(): Arguments {
  return yargs(process.argv.slice(2))
    .config()
    .options({
      token0: { type: 'string', demandOption: true },
      token1: { type: 'string', demandOption: true },
      graphqlEndpoint: { type: 'string', demandOption: true },
      mongodbEndpoint: { type: 'string', demandOption: true },
      daysToFetch: { type: 'number', default: 60 },
      heartbeat: { type: 'string' },
      priority: { type: 'string' },
      strategyWmaColumn: { type: 'string' },
      strategySignalColumn: { type: 'string' },
      strategyName: { type: 'string' },
    })
    .parseSync()
}
