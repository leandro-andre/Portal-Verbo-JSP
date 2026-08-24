import type { DashboardResponse } from '../types/dashboard'

export class DashboardError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'DashboardError'
    this.status = status
  }
}

async function parseResponse(response: Response) {
  return response.json().catch(() => null) as Promise<unknown>
}

function getMessage(data: unknown) {
  if (typeof data === 'object' && data !== null && 'message' in data && typeof data.message === 'string') {
    return data.message
  }
  if (typeof data === 'object' && data !== null && 'detail' in data && typeof data.detail === 'string') {
    return data.detail
  }
  return 'Nao foi possivel carregar sua pagina inicial.'
}

export async function getMyDashboard() {
  const response = await fetch('/api/me/dashboard/', {
    credentials: 'same-origin',
  })
  const data = await parseResponse(response)
  if (!response.ok) {
    throw new DashboardError(response.status, getMessage(data))
  }
  return data as DashboardResponse
}
