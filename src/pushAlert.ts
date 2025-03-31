import { Inject, Injectable } from '@angular/core'
import { ConfigToken } from './config'
import { Arguments } from './types'

@Injectable({
  providedIn: 'root',
})
export class PushAlertService {
  private priority: string | undefined
  private heartbeat: string | undefined

  constructor(@Inject(ConfigToken) config: Arguments) {
    this.priority = config.priority
    this.heartbeat = config.heartbeat
  }

  public async pushAlertError(e: unknown): Promise<void> {
    if (!this.priority) return

    const response = await fetch(`https://ntfy.sh/${this.priority}`, {
      method: 'POST',
      body: `error: ${e}`,
      headers: { Priority: '2' },
    })
    console.log(response)
  }

  public async pushHeartbeat(
    mostRecentAction: string,
    mostRecentTradeTimestamp: number
  ): Promise<void> {
    if (!this.heartbeat) return

    const response = await fetch(`https://ntfy.sh/${this.heartbeat}`, {
      method: 'POST',
      body: `heartbeat ${mostRecentAction}
          ${new Date(mostRecentTradeTimestamp)}`,
      headers: { Priority: '2' },
    })

    console.log(await response.text())
  }

  public async pushAlert(
    mostRecentAction: string,
    mostRecentTradeTimestamp: number
  ): Promise<void> {
    if (!this.priority) return

    const response = await fetch(`https://ntfy.sh/${this.priority}`, {
      method: 'POST',
      body: `${mostRecentAction} ${new Date(mostRecentTradeTimestamp)}`,
      headers: { Priority: '2' },
    })

    console.log(await response.text())
  }
}
