import type {
  GenerateWorshipServicesInput,
  GenerateWorshipServicesResult,
  WorshipService,
  WorshipServiceInput,
  WorshipServiceTemplate,
  WorshipTemplateInput,
} from '../types/worship'
import { csrfJsonHeaders } from './http'

export class WorshipHttpError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'WorshipHttpError'
    this.status = status
  }
}

async function parseResponse(response: Response) {
  return response.json().catch(() => null) as Promise<unknown>
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function getErrorMessage(data: unknown, fallback: string) {
  if (isRecord(data) && typeof data.message === 'string') {
    return data.message
  }
  if (isRecord(data) && typeof data.detail === 'string') {
    return data.detail
  }
  return fallback
}

async function requestJson<T>(url: string, options: RequestInit = {}, fallback = 'Nao foi possivel concluir a acao.') {
  const response = await fetch(url, {
    credentials: 'same-origin',
    ...options,
  })
  const data = await parseResponse(response)

  if (!response.ok) {
    throw new WorshipHttpError(response.status, getErrorMessage(data, fallback))
  }

  return data as T
}

export function getWorshipTemplates() {
  return requestJson<WorshipServiceTemplate[]>('/api/worship/templates/', {}, 'Nao foi possivel carregar os cultos padrao.')
}

export async function createWorshipTemplate(payload: WorshipTemplateInput) {
  const headers = await csrfJsonHeaders()
  return requestJson<WorshipServiceTemplate>(
    '/api/worship/templates/',
    { method: 'POST', headers, body: JSON.stringify(payload) },
    'Nao foi possivel criar o culto padrao.',
  )
}

export async function updateWorshipTemplate(id: number, payload: WorshipTemplateInput) {
  const headers = await csrfJsonHeaders()
  return requestJson<WorshipServiceTemplate>(
    `/api/worship/templates/${id}/`,
    { method: 'PATCH', headers, body: JSON.stringify(payload) },
    'Nao foi possivel atualizar o culto padrao.',
  )
}

async function runTemplateLifecycle(id: number, action: 'deactivate' | 'reactivate') {
  const headers = await csrfJsonHeaders()
  return requestJson<WorshipServiceTemplate>(
    `/api/worship/templates/${id}/${action}/`,
    { method: 'POST', headers },
    'Nao foi possivel alterar o status do culto padrao.',
  )
}

export function deactivateWorshipTemplate(id: number) {
  return runTemplateLifecycle(id, 'deactivate')
}

export function reactivateWorshipTemplate(id: number) {
  return runTemplateLifecycle(id, 'reactivate')
}

export function getWorshipServices(year: number, month: number) {
  return requestJson<WorshipService[]>(
    `/api/worship/services/?year=${year}&month=${month}`,
    {},
    'Nao foi possivel carregar a agenda de cultos.',
  )
}

export async function generateWorshipServices(payload: GenerateWorshipServicesInput) {
  const headers = await csrfJsonHeaders()
  return requestJson<GenerateWorshipServicesResult>(
    '/api/worship/services/generate/',
    { method: 'POST', headers, body: JSON.stringify(payload) },
    'Nao foi possivel gerar a agenda do mes.',
  )
}

export async function createExtraordinaryWorshipService(payload: WorshipServiceInput) {
  const headers = await csrfJsonHeaders()
  return requestJson<WorshipService>(
    '/api/worship/services/extraordinary/',
    { method: 'POST', headers, body: JSON.stringify(payload) },
    'Nao foi possivel criar o culto extraordinario.',
  )
}

export async function updateWorshipService(id: number, payload: WorshipServiceInput) {
  const headers = await csrfJsonHeaders()
  return requestJson<WorshipService>(
    `/api/worship/services/${id}/`,
    { method: 'PATCH', headers, body: JSON.stringify(payload) },
    'Nao foi possivel atualizar o culto.',
  )
}

async function runServiceLifecycle(id: number, action: 'cancel' | 'reactivate') {
  const headers = await csrfJsonHeaders()
  return requestJson<WorshipService>(
    `/api/worship/services/${id}/${action}/`,
    { method: 'POST', headers },
    'Nao foi possivel alterar o status do culto.',
  )
}

export function cancelWorshipService(id: number) {
  return runServiceLifecycle(id, 'cancel')
}

export function reactivateWorshipService(id: number) {
  return runServiceLifecycle(id, 'reactivate')
}
