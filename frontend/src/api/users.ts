import type { PortalUser, UserAccessBusinessErrorResponse } from '../types/user'
import { csrfJsonHeaders } from './http'

export class UserAccessBusinessError extends Error {
  details: UserAccessBusinessErrorResponse

  constructor(details: UserAccessBusinessErrorResponse) {
    super(details.message)
    this.name = 'UserAccessBusinessError'
    this.details = details
  }
}

export class UserAccessHttpError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'UserAccessHttpError'
    this.status = status
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isUserAccessBusinessErrorResponse(
  value: unknown,
): value is UserAccessBusinessErrorResponse {
  return (
    isRecord(value) &&
    (
      value.code === 'CANNOT_DISABLE_OWN_ACCOUNT' ||
      value.code === 'CANNOT_DISABLE_SUPERUSER' ||
      value.code === 'USER_ACCESS_NOT_ACTIVE' ||
      value.code === 'USER_ACCESS_NOT_BLOCKED'
    )
  )
}

async function parseJson(response: Response): Promise<unknown> {
  return response.json().catch(() => null)
}

async function handleUserResponse(response: Response): Promise<unknown> {
  const data = await parseJson(response)

  if (response.status === 403) {
    throw new UserAccessHttpError(403, 'Voce nao tem permissao para administrar usuarios.')
  }

  if (response.status === 404) {
    throw new UserAccessHttpError(404, 'Usuario nao encontrado.')
  }

  if (response.status === 409 && isUserAccessBusinessErrorResponse(data)) {
    throw new UserAccessBusinessError(data)
  }

  if (!response.ok) {
    throw new Error('Nao foi possivel processar o acesso do usuario.')
  }

  return data
}

export async function getUsers(): Promise<PortalUser[]> {
  const response = await fetch('/api/users/', {
    credentials: 'same-origin',
  })
  return await handleUserResponse(response) as PortalUser[]
}

export async function getUser(id: number): Promise<PortalUser> {
  const response = await fetch(`/api/users/${id}/`, {
    credentials: 'same-origin',
  })
  return await handleUserResponse(response) as PortalUser
}

export async function disableUser(id: number): Promise<PortalUser> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/users/${id}/disable/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
  })
  return await handleUserResponse(response) as PortalUser
}

export async function enableUser(id: number): Promise<PortalUser> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/users/${id}/enable/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
  })
  return await handleUserResponse(response) as PortalUser
}
