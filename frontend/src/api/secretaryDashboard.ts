import type { SecretaryDashboardResponse } from '../types/secretaryDashboard'

export class SecretaryDashboardError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'SecretaryDashboardError'
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
  return 'Nao foi possivel carregar a Central da Secretaria.'
}

export async function getSecretaryDashboard() {
  const response = await fetch('/api/secretaria/dashboard/', {
    credentials: 'same-origin',
  })
  const data = await parseResponse(response)
  if (!response.ok) {
    throw new SecretaryDashboardError(response.status, getMessage(data))
  }
  return data as SecretaryDashboardResponse
}
