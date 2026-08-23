import type {
  CreateDepartmentInput,
  Department,
  DepartmentValidationErrors,
  UpdateDepartmentInput,
} from '../types/department'
import { csrfJsonHeaders } from './http'

export class DepartmentApiValidationError extends Error {
  fieldErrors: DepartmentValidationErrors

  constructor(fieldErrors: DepartmentValidationErrors) {
    super('Nao foi possivel validar os dados do departamento.')
    this.name = 'DepartmentApiValidationError'
    this.fieldErrors = fieldErrors
  }
}

export class DepartmentBusinessError extends Error {
  code: string

  constructor(code: string, message: string) {
    super(message)
    this.name = 'DepartmentBusinessError'
    this.code = code
  }
}

export class DepartmentHttpError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'DepartmentHttpError'
    this.status = status
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function parseValidationErrors(value: unknown): DepartmentValidationErrors {
  if (!isRecord(value)) {
    return {}
  }

  const errors: DepartmentValidationErrors = {}
  const fields: Array<keyof CreateDepartmentInput> = ['nome', 'codigo', 'descricao']

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

async function parseResponse(response: Response) {
  return response.json().catch(() => null) as Promise<unknown>
}

function throwBusinessError(data: unknown): never {
  if (isRecord(data) && typeof data.code === 'string') {
    throw new DepartmentBusinessError(
      data.code,
      typeof data.message === 'string' ? data.message : 'Nao foi possivel concluir a acao.',
    )
  }

  throw new Error('Nao foi possivel concluir a acao.')
}

export async function getDepartments(): Promise<Department[]> {
  const response = await fetch('/api/departments/', {
    credentials: 'same-origin',
  })

  if (!response.ok) {
    throw new DepartmentHttpError(response.status, 'Nao foi possivel carregar os departamentos.')
  }

  return response.json() as Promise<Department[]>
}

export async function getDepartment(id: number): Promise<Department> {
  const response = await fetch(`/api/departments/${id}/`, {
    credentials: 'same-origin',
  })

  if (response.status === 404) {
    throw new DepartmentHttpError(404, 'Departamento nao encontrado.')
  }

  if (!response.ok) {
    throw new DepartmentHttpError(response.status, 'Nao foi possivel carregar o departamento.')
  }

  return response.json() as Promise<Department>
}

export async function createDepartment(payload: CreateDepartmentInput): Promise<Department> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/departments/', {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)

  if (response.status === 400) {
    throw new DepartmentApiValidationError(parseValidationErrors(data))
  }

  if (!response.ok) {
    throwBusinessError(data)
  }

  return data as Department
}

export async function updateDepartment(id: number, payload: UpdateDepartmentInput): Promise<Department> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/departments/${id}/`, {
    method: 'PATCH',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)

  if (response.status === 400) {
    throw new DepartmentApiValidationError(parseValidationErrors(data))
  }

  if (response.status === 404) {
    throw new DepartmentHttpError(404, 'Departamento nao encontrado.')
  }

  if (!response.ok) {
    throwBusinessError(data)
  }

  return data as Department
}

async function runDepartmentLifecycle(id: number, action: 'deactivate' | 'reactivate') {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/departments/${id}/${action}/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
  })
  const data = await parseResponse(response)

  if (response.status === 404) {
    throw new DepartmentHttpError(404, 'Departamento nao encontrado.')
  }

  if (!response.ok) {
    throwBusinessError(data)
  }

  return data as Department
}

export function deactivateDepartment(id: number) {
  return runDepartmentLifecycle(id, 'deactivate')
}

export function reactivateDepartment(id: number) {
  return runDepartmentLifecycle(id, 'reactivate')
}
