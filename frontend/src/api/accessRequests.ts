import type {
  AccessRequest,
  AccessRequestBusinessErrorResponse,
  AccessRequestResponse,
  AccessRequestStatus,
  AccessRequestValidationErrors,
  ApproveAccessRequestInput,
  ApproveAccessRequestResponse,
  CreateAccessRequestInput,
  PendingAccessRequestExistsResponse,
  RejectAccessRequestInput,
} from '../types/accessRequest'
import { csrfJsonHeaders } from './http'

export class AccessRequestValidationError extends Error {
  fieldErrors: AccessRequestValidationErrors

  constructor(fieldErrors: AccessRequestValidationErrors) {
    super('Nao foi possivel validar a solicitacao.')
    this.name = 'AccessRequestValidationError'
    this.fieldErrors = fieldErrors
  }
}

export class PendingAccessRequestExistsError extends Error {
  details: PendingAccessRequestExistsResponse

  constructor(details: PendingAccessRequestExistsResponse) {
    super(details.message)
    this.name = 'PendingAccessRequestExistsError'
    this.details = details
  }
}

export class AccessRequestBusinessError extends Error {
  details: AccessRequestBusinessErrorResponse

  constructor(details: AccessRequestBusinessErrorResponse) {
    super(details.message)
    this.name = 'AccessRequestBusinessError'
    this.details = details
  }
}

export class AccessRequestHttpError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'AccessRequestHttpError'
    this.status = status
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function parseValidationErrors(value: unknown): AccessRequestValidationErrors {
  if (!isRecord(value)) {
    return {}
  }

  const errors: AccessRequestValidationErrors = {}
  const fields: Array<keyof CreateAccessRequestInput> = [
    'full_name',
    'birth_date',
    'email',
    'phone',
    'username',
    'password',
    'password_confirm',
  ]

  fields.forEach((field) => {
    const fieldValue = value[field]

    if (isStringArray(fieldValue)) {
      errors[field] = fieldValue
    } else if (typeof fieldValue === 'string') {
      errors[field] = [fieldValue]
    }
  })

  return errors
}

function isPendingAccessRequestExistsResponse(
  value: unknown,
): value is PendingAccessRequestExistsResponse {
  return (
    isRecord(value) &&
    (value.code === 'PENDING_ACCESS_REQUEST_EXISTS' || value.code === 'USERNAME_ALREADY_EXISTS')
  )
}

function isAccessRequestBusinessErrorResponse(
  value: unknown,
): value is AccessRequestBusinessErrorResponse {
  return (
    isRecord(value) &&
    (
      value.code === 'PERSON_ALREADY_HAS_USER' ||
      value.code === 'ACCESS_REQUEST_NOT_PENDING' ||
      value.code === 'PERSON_NOT_FOUND' ||
      value.code === 'INVALID_WHATSAPP' ||
      value.code === 'ACCESS_REQUEST_APPROVAL_INTEGRITY_ERROR' ||
      value.code === 'USERNAME_ALREADY_EXISTS'
    )
  )
}

export async function createAccessRequest(
  payload: CreateAccessRequestInput,
): Promise<AccessRequestResponse> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/access-requests/', {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })

  const data: unknown = await response.json().catch(() => null)

  if (response.status === 409 && isPendingAccessRequestExistsResponse(data)) {
    throw new PendingAccessRequestExistsError(data)
  }

  if (response.status === 400) {
    throw new AccessRequestValidationError(parseValidationErrors(data))
  }

  if (!response.ok) {
    throw new Error('Nao foi possivel enviar sua solicitacao. Tente novamente.')
  }

  return data as AccessRequestResponse
}

async function parseJson(response: Response): Promise<unknown> {
  return response.json().catch(() => null)
}

async function handleAdminResponse(response: Response): Promise<unknown> {
  const data = await parseJson(response)

  if (response.status === 403) {
    throw new AccessRequestHttpError(403, 'Voce nao tem permissao para revisar solicitacoes.')
  }

  if (response.status === 404) {
    throw new AccessRequestHttpError(404, 'Solicitacao nao encontrada.')
  }

  if ((response.status === 400 || response.status === 409) && isAccessRequestBusinessErrorResponse(data)) {
    throw new AccessRequestBusinessError(data)
  }

  if (response.status === 400) {
    throw new AccessRequestValidationError(parseValidationErrors(data))
  }

  if (!response.ok) {
    throw new Error('Nao foi possivel processar a solicitacao. Tente novamente.')
  }

  return data
}

export async function getAccessRequests(status: AccessRequestStatus): Promise<AccessRequest[]> {
  const response = await fetch(`/api/access-requests/admin/?status=${status}`, {
    credentials: 'same-origin',
  })
  return await handleAdminResponse(response) as AccessRequest[]
}

export async function getAccessRequest(id: number): Promise<AccessRequest> {
  const response = await fetch(`/api/access-requests/admin/${id}/`, {
    credentials: 'same-origin',
  })
  return await handleAdminResponse(response) as AccessRequest
}

export async function approveAccessRequest(
  id: number,
  payload: ApproveAccessRequestInput,
): Promise<ApproveAccessRequestResponse> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/access-requests/admin/${id}/approve/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  return await handleAdminResponse(response) as ApproveAccessRequestResponse
}

export async function rejectAccessRequest(
  id: number,
  payload: RejectAccessRequestInput,
): Promise<AccessRequest> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/access-requests/admin/${id}/reject/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  return await handleAdminResponse(response) as AccessRequest
}
