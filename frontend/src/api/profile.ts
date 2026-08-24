import type { MyProfileResponse, MyProfileUpdateInput } from '../types/person'
import { csrfJsonHeaders, ensureCsrfCookie, getCsrfToken } from './http'

export class MyProfileError extends Error {
  status: number
  fieldErrors: Record<string, string[]>

  constructor(status: number, message: string, fieldErrors: Record<string, string[]> = {}) {
    super(message)
    this.name = 'MyProfileError'
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function parseStringErrors(data: unknown) {
  if (!isRecord(data)) return {}
  return Object.fromEntries(
    Object.entries(data).flatMap(([field, value]) => {
      if (Array.isArray(value) && value.every((item) => typeof item === 'string')) {
        return [[field, value]]
      }
      if (typeof value === 'string') {
        return [[field, [value]]]
      }
      return []
    }),
  )
}

async function parseResponse(response: Response) {
  return response.json().catch(() => null) as Promise<unknown>
}

function messageFrom(data: unknown, fallback: string) {
  if (isRecord(data) && typeof data.message === 'string') return data.message
  if (isRecord(data) && typeof data.detail === 'string') return data.detail
  return fallback
}

async function requestProfile(url: string, options: RequestInit = {}, fallback = 'Nao foi possivel carregar seu perfil.') {
  const response = await fetch(url, { credentials: 'same-origin', ...options })
  const data = await parseResponse(response)
  if (!response.ok) {
    throw new MyProfileError(response.status, messageFrom(data, fallback), parseStringErrors(data))
  }
  return data as MyProfileResponse
}

export function getMyProfile() {
  return requestProfile('/api/me/profile/')
}

export async function updateMyProfile(payload: MyProfileUpdateInput) {
  const headers = await csrfJsonHeaders()
  return requestProfile(
    '/api/me/profile/',
    { method: 'PATCH', headers, body: JSON.stringify(payload) },
    'Nao foi possivel salvar seu perfil.',
  )
}

export async function uploadMyProfilePhoto(photo: File) {
  await ensureCsrfCookie()
  const formData = new FormData()
  formData.append('photo', photo)
  return requestProfile(
    '/api/me/profile/photo/',
    {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrfToken() },
      body: formData,
    },
    'Nao foi possivel atualizar sua foto.',
  )
}

export async function deleteMyProfilePhoto() {
  await ensureCsrfCookie()
  return requestProfile(
    '/api/me/profile/photo/',
    { method: 'DELETE', headers: { 'X-CSRFToken': getCsrfToken() } },
    'Nao foi possivel remover sua foto.',
  )
}
