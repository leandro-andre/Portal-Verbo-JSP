import type {
  ApiValidationErrors,
  ChurchJourney,
  CreatePersonInput,
  EligibleMembershipPerson,
  Membership,
  MembershipStatus,
  MembershipStatusHistory,
  Person,
  PossibleDuplicateResponse,
  StartChurchJourneyInput,
  UpdatePersonInput,
} from '../types/person'
import { csrfJsonHeaders } from './http'

export class ApiValidationError extends Error {
  fieldErrors: ApiValidationErrors

  constructor(fieldErrors: ApiValidationErrors) {
    super('Nao foi possivel validar os dados da pessoa.')
    this.name = 'ApiValidationError'
    this.fieldErrors = fieldErrors
  }
}

export class PossibleDuplicateError extends Error {
  details: PossibleDuplicateResponse

  constructor(details: PossibleDuplicateResponse) {
    super(details.message)
    this.name = 'PossibleDuplicateError'
    this.details = details
  }
}

export class ApiHttpError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiHttpError'
    this.status = status
  }
}

export async function getPeople(search?: string): Promise<Person[]> {
  const params = search?.trim() ? `?q=${encodeURIComponent(search.trim())}` : ''
  const response = await fetch(`/api/people/${params}`, {
    credentials: 'same-origin',
  })

  if (!response.ok) {
    throw new ApiHttpError(response.status, 'Nao foi possivel carregar as pessoas.')
  }

  return response.json() as Promise<Person[]>
}

export async function getPerson(id: number): Promise<Person> {
  const response = await fetch(`/api/people/${id}/`, {
    credentials: 'same-origin',
  })

  if (response.status === 404) {
    throw new ApiHttpError(404, 'Pessoa nao encontrada.')
  }

  if (!response.ok) {
    throw new ApiHttpError(response.status, 'Nao foi possivel carregar os dados da pessoa.')
  }

  return response.json() as Promise<Person>
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function parseValidationErrors(value: unknown): ApiValidationErrors {
  if (!isRecord(value)) {
    return {}
  }

  const errors: ApiValidationErrors = {}
  const fields: Array<keyof CreatePersonInput> = [
    'full_name',
    'preferred_name',
    'birth_date',
    'email',
    'phone',
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

function isPossibleDuplicateResponse(value: unknown): value is PossibleDuplicateResponse {
  if (!isRecord(value)) {
    return false
  }

  return value.code === 'POSSIBLE_DUPLICATE' && Array.isArray(value.candidates)
}

export async function createPerson(payload: CreatePersonInput): Promise<Person> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/people/', {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })

  const data: unknown = await response.json().catch(() => null)

  if (response.status === 409 && isPossibleDuplicateResponse(data)) {
    throw new PossibleDuplicateError(data)
  }

  if (response.status === 400) {
    throw new ApiValidationError(parseValidationErrors(data))
  }

  if (!response.ok) {
    throw new Error('Nao foi possivel cadastrar a pessoa. Tente novamente.')
  }

  return data as Person
}

export async function updatePerson(id: number, payload: UpdatePersonInput): Promise<Person> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/people/${id}/`, {
    method: 'PATCH',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })

  const data: unknown = await response.json().catch(() => null)

  if (response.status === 409 && isPossibleDuplicateResponse(data)) {
    throw new PossibleDuplicateError(data)
  }

  if (response.status === 400) {
    throw new ApiValidationError(parseValidationErrors(data))
  }

  if (response.status === 404) {
    throw new ApiHttpError(404, 'Pessoa nao encontrada.')
  }

  if (!response.ok) {
    throw new Error('Nao foi possivel salvar as alteracoes. Tente novamente.')
  }

  return data as Person
}

export async function getChurchJourney(personId: number): Promise<ChurchJourney | null> {
  const response = await fetch(`/api/people/${personId}/church-journey/`, {
    credentials: 'same-origin',
  })

  if (response.status === 404) {
    return null
  }

  if (!response.ok) {
    throw new ApiHttpError(response.status, 'Nao foi possivel carregar a jornada da igreja.')
  }

  return response.json() as Promise<ChurchJourney>
}

export async function getMembership(personId: number): Promise<Membership | null> {
  const response = await fetch(`/api/people/${personId}/membership/`, {
    credentials: 'same-origin',
  })

  if (response.status === 404) {
    return null
  }

  if (!response.ok) {
    throw new ApiHttpError(response.status, 'Nao foi possivel carregar a membresia.')
  }

  return response.json() as Promise<Membership>
}

export async function approveMembership(personId: number): Promise<Membership> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/people/${personId}/membership/approve/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify({}),
  })

  const data: unknown = await response.json().catch(() => null)

  if (response.status === 409 && isRecord(data) && typeof data.code === 'string') {
    throw new ApiHttpError(409, data.message as string || 'Nao foi possivel aprovar a membresia.')
  }

  if (response.status === 403) {
    throw new ApiHttpError(403, 'Voce nao tem permissao para aprovar membresia.')
  }

  if (!response.ok) {
    throw new Error('Nao foi possivel aprovar a membresia.')
  }

  return data as Membership
}

async function postMembershipLifecycle(
  personId: number,
  action: 'deactivate' | 'reactivate',
  reason: string,
): Promise<Membership> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/people/${personId}/membership/${action}/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify({ reason }),
  })

  const data: unknown = await response.json().catch(() => null)

  if (response.status === 409 && isRecord(data) && typeof data.code === 'string') {
    throw new ApiHttpError(409, data.message as string || 'Nao foi possivel alterar a membresia.')
  }

  if (response.status === 403) {
    throw new ApiHttpError(403, 'Voce nao tem permissao para alterar membresia.')
  }

  if (!response.ok) {
    throw new Error('Nao foi possivel alterar a membresia.')
  }

  return data as Membership
}

export async function deactivateMembership(personId: number, reason: string): Promise<Membership> {
  return postMembershipLifecycle(personId, 'deactivate', reason)
}

export async function reactivateMembership(personId: number, reason: string): Promise<Membership> {
  return postMembershipLifecycle(personId, 'reactivate', reason)
}

export async function getMembershipHistory(personId: number): Promise<MembershipStatusHistory[]> {
  const response = await fetch(`/api/people/${personId}/membership/history/`, {
    credentials: 'same-origin',
  })

  if (response.status === 404) {
    return []
  }

  if (!response.ok) {
    throw new ApiHttpError(response.status, 'Nao foi possivel carregar o historico da membresia.')
  }

  return response.json() as Promise<MembershipStatusHistory[]>
}

export async function getMemberships(status?: MembershipStatus): Promise<Membership[]> {
  const params = status ? `?status=${status}` : ''
  const response = await fetch(`/api/memberships/${params}`, {
    credentials: 'same-origin',
  })

  if (!response.ok) {
    throw new ApiHttpError(response.status, 'Nao foi possivel carregar membresias.')
  }

  return response.json() as Promise<Membership[]>
}

export async function getEligibleMembershipPeople(): Promise<EligibleMembershipPerson[]> {
  const response = await fetch('/api/membership/eligible/', {
    credentials: 'same-origin',
  })

  if (!response.ok) {
    throw new ApiHttpError(response.status, 'Nao foi possivel carregar pessoas elegiveis.')
  }

  return response.json() as Promise<EligibleMembershipPerson[]>
}

export async function startChurchJourney(
  personId: number,
  payload: StartChurchJourneyInput,
): Promise<ChurchJourney> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/people/${personId}/church-journey/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })

  const data: unknown = await response.json().catch(() => null)

  if (response.status === 404) {
    throw new ApiHttpError(404, 'Pessoa nao encontrada.')
  }

  if (response.status === 409) {
    throw new ApiHttpError(409, 'Esta pessoa ja possui uma jornada eclesiastica.')
  }

  if (response.status === 400) {
    throw new ApiValidationError(parseValidationErrors(data))
  }

  if (!response.ok) {
    throw new Error('Nao foi possivel iniciar a jornada da igreja. Tente novamente.')
  }

  return data as ChurchJourney
}
