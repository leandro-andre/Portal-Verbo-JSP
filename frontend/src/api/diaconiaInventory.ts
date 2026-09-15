import {
  DiaconiaApiValidationError,
  DiaconiaBusinessError,
  DiaconiaHttpError,
} from './diaconia'
import { csrfJsonHeaders } from './http'
import type {
  CreateInventoryCategoryInput,
  CreateInventoryCountInput,
  CreateInventoryItemInput,
  CreateInventoryLocationInput,
  InventoryCategory,
  InventoryCount,
  InventoryCountComparison,
  InventoryCountFilters,
  InventoryCountListItem,
  InventoryFilters,
  InventoryItem,
  InventoryItemFilters,
  InventoryLocation,
  UpdateInventoryCategoryInput,
  UpdateInventoryCountInput,
  UpdateInventoryItemInput,
  UpdateInventoryLocationInput,
} from '../types/diaconiaInventory'
import type { DiaconiaValidationErrors } from '../types/diaconia'

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

function inventoryQuery(filters?: InventoryFilters) {
  const params = new URLSearchParams()
  if (filters?.search?.trim()) params.set('search', filters.search.trim())
  if (filters?.status && filters.status !== 'ALL') params.set('status', filters.status)
  const query = params.toString()
  return query ? `?${query}` : ''
}

function inventoryItemQuery(filters?: InventoryItemFilters) {
  const params = new URLSearchParams()
  if (filters?.search?.trim()) params.set('search', filters.search.trim())
  if (filters?.category) params.set('category', filters.category)
  if (filters?.status && filters.status !== 'ALL') params.set('status', filters.status)
  const query = params.toString()
  return query ? `?${query}` : ''
}

function inventoryCountQuery(filters?: InventoryCountFilters) {
  const params = new URLSearchParams()
  if (filters?.date_from) params.set('date_from', filters.date_from)
  if (filters?.date_to) params.set('date_to', filters.date_to)
  if (filters?.created_by) params.set('created_by', filters.created_by)
  const query = params.toString()
  return query ? `?${query}` : ''
}

export async function getInventoryItems(filters?: InventoryItemFilters): Promise<InventoryItem[]> {
  const response = await fetch(`/api/diaconia/inventory/items/${inventoryItemQuery(filters)}`, { credentials: 'same-origin' })
  if (!response.ok) throw new DiaconiaHttpError(response.status, 'Nao foi possivel carregar itens de inventario.')
  return response.json() as Promise<InventoryItem[]>
}

export async function getInventoryItem(id: number): Promise<InventoryItem> {
  const response = await fetch(`/api/diaconia/inventory/items/${id}/`, { credentials: 'same-origin' })
  if (response.status === 404) throw new DiaconiaHttpError(404, 'Item nao encontrado.')
  if (!response.ok) throw new DiaconiaHttpError(response.status, 'Nao foi possivel carregar item de inventario.')
  return response.json() as Promise<InventoryItem>
}

export async function createInventoryItem(payload: CreateInventoryItemInput): Promise<InventoryItem> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/diaconia/inventory/items/', {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (!response.ok) throwBusinessError(data)
  return data as InventoryItem
}

export async function updateInventoryItem(id: number, payload: UpdateInventoryItemInput): Promise<InventoryItem> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/diaconia/inventory/items/${id}/`, {
    method: 'PATCH',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (response.status === 404) throw new DiaconiaHttpError(404, 'Item nao encontrado.')
  if (!response.ok) throwBusinessError(data)
  return data as InventoryItem
}

async function runInventoryItemLifecycle(id: number, action: 'deactivate' | 'reactivate') {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/diaconia/inventory/items/${id}/${action}/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
  })
  const data = await parseResponse(response)
  if (!response.ok) throwBusinessError(data)
  return data as InventoryItem
}

export function deactivateInventoryItem(id: number) {
  return runInventoryItemLifecycle(id, 'deactivate')
}

export function reactivateInventoryItem(id: number) {
  return runInventoryItemLifecycle(id, 'reactivate')
}

export async function createInventoryCount(payload: CreateInventoryCountInput): Promise<InventoryCount> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/diaconia/inventory/counts/', {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (!response.ok) throwBusinessError(data)
  return data as InventoryCount
}

export async function getInventoryCounts(filters?: InventoryCountFilters): Promise<InventoryCountListItem[]> {
  const response = await fetch(`/api/diaconia/inventory/counts/${inventoryCountQuery(filters)}`, { credentials: 'same-origin' })
  if (!response.ok) throw new DiaconiaHttpError(response.status, 'Nao foi possivel carregar contagens de inventario.')
  return response.json() as Promise<InventoryCountListItem[]>
}

export async function getInventoryCount(id: number): Promise<InventoryCount> {
  const response = await fetch(`/api/diaconia/inventory/counts/${id}/`, { credentials: 'same-origin' })
  if (response.status === 404) throw new DiaconiaHttpError(404, 'Contagem nao encontrada.')
  if (!response.ok) throw new DiaconiaHttpError(response.status, 'Nao foi possivel carregar contagem de inventario.')
  return response.json() as Promise<InventoryCount>
}

export async function updateInventoryCount(id: number, payload: UpdateInventoryCountInput): Promise<InventoryCount> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/diaconia/inventory/counts/${id}/`, {
    method: 'PATCH',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (response.status === 404) throw new DiaconiaHttpError(404, 'Contagem nao encontrada.')
  if (!response.ok) throwBusinessError(data)
  return data as InventoryCount
}

export async function getInventoryCountComparison(id: number): Promise<InventoryCountComparison> {
  const response = await fetch(`/api/diaconia/inventory/counts/${id}/comparison/`, { credentials: 'same-origin' })
  if (response.status === 404) throw new DiaconiaHttpError(404, 'Contagem nao encontrada.')
  if (!response.ok) throw new DiaconiaHttpError(response.status, 'Nao foi possivel carregar comparativo de inventario.')
  return response.json() as Promise<InventoryCountComparison>
}

export async function getInventoryCategories(filters?: InventoryFilters): Promise<InventoryCategory[]> {
  const response = await fetch(`/api/diaconia/inventory/categories/${inventoryQuery(filters)}`, { credentials: 'same-origin' })
  if (!response.ok) throw new DiaconiaHttpError(response.status, 'Nao foi possivel carregar categorias de inventario.')
  return response.json() as Promise<InventoryCategory[]>
}

export async function createInventoryCategory(payload: CreateInventoryCategoryInput): Promise<InventoryCategory> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/diaconia/inventory/categories/', {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (!response.ok) throwBusinessError(data)
  return data as InventoryCategory
}

export async function updateInventoryCategory(id: number, payload: UpdateInventoryCategoryInput): Promise<InventoryCategory> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/diaconia/inventory/categories/${id}/`, {
    method: 'PATCH',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (!response.ok) throwBusinessError(data)
  return data as InventoryCategory
}

async function runInventoryCategoryLifecycle(id: number, action: 'deactivate' | 'reactivate') {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/diaconia/inventory/categories/${id}/${action}/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
  })
  const data = await parseResponse(response)
  if (!response.ok) throwBusinessError(data)
  return data as InventoryCategory
}

export function deactivateInventoryCategory(id: number) {
  return runInventoryCategoryLifecycle(id, 'deactivate')
}

export function reactivateInventoryCategory(id: number) {
  return runInventoryCategoryLifecycle(id, 'reactivate')
}

export async function getInventoryLocations(filters?: InventoryFilters): Promise<InventoryLocation[]> {
  const response = await fetch(`/api/diaconia/inventory/locations/${inventoryQuery(filters)}`, { credentials: 'same-origin' })
  if (!response.ok) throw new DiaconiaHttpError(response.status, 'Nao foi possivel carregar locais de inventario.')
  return response.json() as Promise<InventoryLocation[]>
}

export async function createInventoryLocation(payload: CreateInventoryLocationInput): Promise<InventoryLocation> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/diaconia/inventory/locations/', {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (!response.ok) throwBusinessError(data)
  return data as InventoryLocation
}

export async function updateInventoryLocation(id: number, payload: UpdateInventoryLocationInput): Promise<InventoryLocation> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/diaconia/inventory/locations/${id}/`, {
    method: 'PATCH',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)
  if (response.status === 400) throw new DiaconiaApiValidationError(parseValidationErrors(data))
  if (!response.ok) throwBusinessError(data)
  return data as InventoryLocation
}

async function runInventoryLocationLifecycle(id: number, action: 'deactivate' | 'reactivate') {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/diaconia/inventory/locations/${id}/${action}/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
  })
  const data = await parseResponse(response)
  if (!response.ok) throwBusinessError(data)
  return data as InventoryLocation
}

export function deactivateInventoryLocation(id: number) {
  return runInventoryLocationLifecycle(id, 'deactivate')
}

export function reactivateInventoryLocation(id: number) {
  return runInventoryLocationLifecycle(id, 'reactivate')
}
