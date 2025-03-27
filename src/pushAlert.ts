import { priority, heartbeat } from './private.json'

export async function pushAlertError(e: unknown): Promise<void> {
  const response = await fetch(`https://ntfy.sh/${priority}`, {
    method: 'POST',
    body: `error: ${e}`,
    headers: { Priority: '4' },
  })
  console.log(response)
}

export async function pushAlert(
  mostRecentPosition: [string, number],
  mostRecentTrade: [number, number]
): Promise<void> {
  if (mostRecentPosition[1] !== 0) {
    const response = await fetch(`https://ntfy.sh/${priority}`, {
      method: 'POST',
      body: `${mostRecentTrade[1] === 1 ? 'buy' : 'sell'} ${new Date(mostRecentTrade[0])}`,
      headers: { Priority: '5' },
    })
    console.log(await response.text())
  } else {
    const response = await fetch(`https://ntfy.sh/${heartbeat}`, {
      method: 'POST',
      body: `heartbeat ${mostRecentTrade[1] === 1 ? 'buy' : 'sell'}
          ${new Date(mostRecentTrade[0])}`,
      headers: { Priority: '2' },
    })

    console.log(await response.text())
  }
}
