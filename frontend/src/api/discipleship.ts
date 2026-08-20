import type {
  CreateDiscipleshipClassInput,
  CreateDiscipleshipEnrollmentInput,
  DiscipleshipClass,
  DiscipleshipEnrollment,
  DiscipleshipValidationErrors,
  UpdateDiscipleshipClassInput,
} from '../types/discipleship'
import { csrfJsonHeaders } from './http'

export class DiscipleshipApiValidationError extends Error {
  fieldErrors: DiscipleshipValidationErrors

  constructor(fieldErrors: DiscipleshipValidationErrors) {
    super('Nao foi possivel validar os dados da turma.')
    this.name = 'DiscipleshipApiValidationError'
    this.fieldErrors = fieldErrors
  }
}

export class DiscipleshipBusinessError extends Error {
  code: string

  constructor(code: string, message: string) {
    super(message)
    this.name = 'DiscipleshipBusinessError'
    this.code = code
  }
}

export class DiscipleshipHttpError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'DiscipleshipHttpError'
    this.status = status
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function parseValidationErrors(value: unknown): DiscipleshipValidationErrors {
  if (!isRecord(value)) {
    return {}
  }

  const errors: DiscipleshipValidationErrors = {}
  const fields: Array<keyof CreateDiscipleshipClassInput> = [
    'name',
    'teacher_id',
    'start_date',
    'expected_end_date',
    'planned_sessions',
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

async function parseResponse(response: Response) {
  return response.json().catch(() => null) as Promise<unknown>
}

function businessMessage(code: string) {
  if (code === 'DISCIPLESHIP_CLASS_ALREADY_IN_PROGRESS') {
    return 'Ja existe uma turma de discipulado em andamento.'
  }
  if (code === 'INVALID_DISCIPLESHIP_CLASS_TRANSITION') {
    return 'Esta acao nao esta disponivel para o status atual da turma.'
  }
  if (code === 'PERSON_NOT_IN_CHURCH_JOURNEY') {
    return 'Esta pessoa ainda nao esta na jornada da igreja.'
  }
  if (code === 'DISCIPLESHIP_CLASS_NOT_OPEN_FOR_ENROLLMENT') {
    return 'Esta turma nao esta aberta para matriculas.'
  }
  if (code === 'DISCIPLESHIP_ENROLLMENT_ALREADY_EXISTS') {
    return 'Esta pessoa ja possui matricula nesta turma.'
  }
  if (code === 'INVALID_DISCIPLESHIP_ENROLLMENT_TRANSITION') {
    return 'Esta matricula nao permite esta acao.'
  }
  return 'Nao foi possivel concluir a acao solicitada.'
}

function throwBusinessError(data: unknown): never {
  if (isRecord(data) && typeof data.code === 'string') {
    throw new DiscipleshipBusinessError(
      data.code,
      typeof data.message === 'string' ? data.message : businessMessage(data.code),
    )
  }

  throw new Error('Nao foi possivel concluir a acao solicitada.')
}

export async function getDiscipleshipClasses(): Promise<DiscipleshipClass[]> {
  const response = await fetch('/api/discipleship/classes/', {
    credentials: 'same-origin',
  })

  if (!response.ok) {
    throw new DiscipleshipHttpError(response.status, 'Nao foi possivel carregar as turmas.')
  }

  return response.json() as Promise<DiscipleshipClass[]>
}

export async function getDiscipleshipClass(id: number): Promise<DiscipleshipClass> {
  const response = await fetch(`/api/discipleship/classes/${id}/`, {
    credentials: 'same-origin',
  })

  if (response.status === 404) {
    throw new DiscipleshipHttpError(404, 'Turma nao encontrada.')
  }

  if (!response.ok) {
    throw new DiscipleshipHttpError(response.status, 'Nao foi possivel carregar a turma.')
  }

  return response.json() as Promise<DiscipleshipClass>
}

export async function createDiscipleshipClass(
  payload: CreateDiscipleshipClassInput,
): Promise<DiscipleshipClass> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/discipleship/classes/', {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)

  if (response.status === 400) {
    throw new DiscipleshipApiValidationError(parseValidationErrors(data))
  }

  if (!response.ok) {
    throwBusinessError(data)
  }

  return data as DiscipleshipClass
}

export async function updateDiscipleshipClass(
  id: number,
  payload: UpdateDiscipleshipClassInput,
): Promise<DiscipleshipClass> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/discipleship/classes/${id}/`, {
    method: 'PATCH',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)

  if (response.status === 400) {
    throw new DiscipleshipApiValidationError(parseValidationErrors(data))
  }

  if (response.status === 404) {
    throw new DiscipleshipHttpError(404, 'Turma nao encontrada.')
  }

  if (!response.ok) {
    throwBusinessError(data)
  }

  return data as DiscipleshipClass
}

async function runLifecycleAction(id: number, action: 'start' | 'complete' | 'cancel') {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/discipleship/classes/${id}/${action}/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
  })
  const data = await parseResponse(response)

  if (response.status === 404) {
    throw new DiscipleshipHttpError(404, 'Turma nao encontrada.')
  }

  if (!response.ok) {
    throwBusinessError(data)
  }

  return data as DiscipleshipClass
}

export function startDiscipleshipClass(id: number) {
  return runLifecycleAction(id, 'start')
}

export function completeDiscipleshipClass(id: number) {
  return runLifecycleAction(id, 'complete')
}

export function cancelDiscipleshipClass(id: number) {
  return runLifecycleAction(id, 'cancel')
}

export async function getDiscipleshipEnrollments(classId: number): Promise<DiscipleshipEnrollment[]> {
  const response = await fetch(`/api/discipleship/classes/${classId}/enrollments/`, {
    credentials: 'same-origin',
  })

  if (!response.ok) {
    throw new DiscipleshipHttpError(response.status, 'Nao foi possivel carregar as matriculas.')
  }

  return response.json() as Promise<DiscipleshipEnrollment[]>
}

export async function getDiscipleshipEnrollment(
  classId: number,
  enrollmentId: number,
): Promise<DiscipleshipEnrollment> {
  const response = await fetch(`/api/discipleship/classes/${classId}/enrollments/${enrollmentId}/`, {
    credentials: 'same-origin',
  })

  if (response.status === 404) {
    throw new DiscipleshipHttpError(404, 'Matricula nao encontrada.')
  }

  if (!response.ok) {
    throw new DiscipleshipHttpError(response.status, 'Nao foi possivel carregar a matricula.')
  }

  return response.json() as Promise<DiscipleshipEnrollment>
}

export async function createDiscipleshipEnrollment(
  classId: number,
  payload: CreateDiscipleshipEnrollmentInput,
): Promise<DiscipleshipEnrollment> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/discipleship/classes/${classId}/enrollments/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseResponse(response)

  if (response.status === 400) {
    throw new DiscipleshipApiValidationError({})
  }

  if (!response.ok) {
    throwBusinessError(data)
  }

  return data as DiscipleshipEnrollment
}

export async function withdrawDiscipleshipEnrollment(
  classId: number,
  enrollmentId: number,
): Promise<DiscipleshipEnrollment> {
  const headers = await csrfJsonHeaders()
  const response = await fetch(
    `/api/discipleship/classes/${classId}/enrollments/${enrollmentId}/withdraw/`,
    {
      method: 'POST',
      credentials: 'same-origin',
      headers,
    },
  )
  const data = await parseResponse(response)

  if (!response.ok) {
    throwBusinessError(data)
  }

  return data as DiscipleshipEnrollment
}
