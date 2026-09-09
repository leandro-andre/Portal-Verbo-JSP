import type { GlobalSearchResponse } from '../types/globalSearch'

export class GlobalSearchHttpError extends Error {
  status: number

  constructor(status: number) {
    super('Nao foi possivel buscar no portal.')
    this.name = 'GlobalSearchHttpError'
    this.status = status
  }
}

export async function getGlobalSearch(query: string, signal?: AbortSignal): Promise<GlobalSearchResponse> {
  const params = new URLSearchParams({ q: query.trim() })
  const response = await fetch(`/api/search/?${params.toString()}`, {
    credentials: 'same-origin',
    signal,
  })

  if (!response.ok) {
    throw new GlobalSearchHttpError(response.status)
  }

  return response.json() as Promise<GlobalSearchResponse>
}
