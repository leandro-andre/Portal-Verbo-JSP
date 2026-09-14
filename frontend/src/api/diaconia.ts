import type {
  CreateStockCategoryInput,
  CreateStockItemInput,
  DiaconiaValidationErrors,
  StockCategory,
  StockItem,
  StockUnit,
  UpdateStockCategoryInput,
  UpdateStockItemInput,
} from '../types/diaconia'
import { csrfJsonHeaders } from './http'

export class DiaconiaApiValidationError extends Error {
  fieldErrors: DiaconiaValidationErrors

  constructor(fieldErrors: DiaconiaValidationErrors) {
    super('Nao foi possivel validar os dados da Diaconia.')
    this.name = 'DiaconiaApiValidationError'
    this.fieldErrors = fieldErrors
  }
}

export class DiaconiaHttpError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'DiaconiaHttpError'
    this.status = status
  }
}

export class DiaconiaBusinessError extends Error {
  code: string

  constructor(code: string, message: string) {
    super(message)
    this.name = 'DiaconiaBusinessError'
    this.code = code
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function parseValidationErrors(value: unknown): DiaconiaValidationErrors {
  if (!isRecord(value)) return {}
  const errors: DiaconiaValidationErrors = {}
  Object.entries(value).forEach(([field, fieldValue]) => {
    if (isStringArray(fieldValue)) {
      errors[field] = fieldValue
    } else if (typeof fieldValue === 'string') {
      errors[field] = [fieldValue]
    }
  })
  return errors
}

async function parseResponse(response: Response) {
  return response.json().catch(() => null) as Promise<unknown>
}

function throwBusinessError(data: unknown): never {
  if (isRecord(data) && typeof data.code === 'string') {
    throw new DiaconiaBusinessError(
      data.code,
      typeof data.message === 'string' ? data.message : 'Nao foi possivel concluir a acao.',
    )
  }
  throw new Error('Nao foi possivel concluir a acao.')
}

export async function getStockUnits(): Promise<StockUnit[]> {
  const response = await fetch('/api/diaconia/stock/units/', { credentials: 'same-origin' })
  if (!response.ok) throw new DiaconiaHttpError(response.status, 'Nao foi possivel carregar unidades.')
  return response.json() as Promise<StockUnit[]>
}

export async function getStockCategories(): Promise<StockCategory[]> {
  const response = await fetch('/api/diaconia/stock/categories/', { credentials: 'same-origin' })
  if (!response.ok) throw new DiaconiaHttpError(response.status, 'Nao foi possivel carregar categorias.')
  return response.json() as Promise<StockCategory[]>
}

export async function createStockCategory(payload: CreateStockCategoryInput): Promise<StockCategory> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/diaconia/stock/categories/', {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (!response.ok) throwBusinessError(data)
  return data as StockCategory
}

export async function updateStockCategory(id: number, payload: UpdateStockCategoryInput): Promise<StockCategory> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/diaconia/stock/categories/${id}/`, {
    method: 'PATCH',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (!response.ok) throwBusinessError(data)
  return data as StockCategory
}

async function runCategoryLifecycle(id: number, action: 'deactivate' | 'reactivate') {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/diaconia/stock/categories/${id}/${action}/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
  })
  const data = await parseResponse(response)
  if (!response.ok) throwBusinessError(data)
  return data as StockCategory
}

export function deactivateStockCategory(id: number) {
  return runCategoryLifecycle(id, 'deactivate')
}

export function reactivateStockCategory(id: number) {
  return runCategoryLifecycle(id, 'reactivate')
}

export async function getStockItems(): Promise<StockItem[]> {
  const response = await fetch('/api/diaconia/stock/items/', { credentials: 'same-origin' })
  if (!response.ok) throw new DiaconiaHttpError(response.status, 'Nao foi possivel carregar itens.')
  return response.json() as Promise<StockItem[]>
}

export async function getStockItem(id: number): Promise<StockItem> {
  const response = await fetch(`/api/diaconia/stock/items/${id}/`, { credentials: 'same-origin' })
  if (response.status === 404) throw new DiaconiaHttpError(404, 'Item nao encontrado.')
  if (!response.ok) throw new DiaconiaHttpError(response.status, 'Nao foi possivel carregar item.')
  return response.json() as Promise<StockItem>
}

export async function createStockItem(payload: CreateStockItemInput): Promise<StockItem> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/diaconia/stock/items/', {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (!response.ok) throwBusinessError(data)
  return data as StockItem
}

export async function updateStockItem(id: number, payload: UpdateStockItemInput): Promise<StockItem> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/diaconia/stock/items/${id}/`, {
    method: 'PATCH',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (response.status === 404) throw new DiaconiaHttpError(404, 'Item nao encontrado.')
  if (!response.ok) throwBusinessError(data)
  return data as StockItem
}

async function runItemLifecycle(id: number, action: 'deactivate' | 'reactivate') {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/diaconia/stock/items/${id}/${action}/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
  })
  const data = await parseResponse(response)
  if (!response.ok) throwBusinessError(data)
  return data as StockItem
}

export function deactivateStockItem(id: number) {
  return runItemLifecycle(id, 'deactivate')
}

export function reactivateStockItem(id: number) {
  return runItemLifecycle(id, 'reactivate')
}
