import type {
  ApiValidationErrors,
  CreatePersonInput,
  Person,
  PossibleDuplicateResponse,
} from '../types/person'

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

export async function getPeople(): Promise<Person[]> {
  const response = await fetch('/api/people/')

  if (!response.ok) {
    throw new Error('Nao foi possivel carregar as pessoas.')
  }

  return response.json() as Promise<Person[]>
}

export async function getPerson(id: number): Promise<Person> {
  const response = await fetch(`/api/people/${id}/`)

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
  const response = await fetch('/api/people/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
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
