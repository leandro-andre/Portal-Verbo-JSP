import type { MonthlySchedule, ScheduleAssignment, ScheduleCandidate, ScheduleCreateInput, ScheduleDetail, ScheduleSummary } from '../types/scheduling'
import type { Department } from '../types/department'
import { csrfJsonHeaders } from './http'

export class SchedulingHttpError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'SchedulingHttpError'
    this.status = status
  }
}

async function parseResponse(response: Response) {
  return response.json().catch(() => null) as Promise<unknown>
}

function getMessage(data: unknown, fallback: string) {
  if (typeof data === 'object' && data !== null && 'message' in data && typeof data.message === 'string') {
    return data.message
  }
  if (typeof data === 'object' && data !== null && 'detail' in data && typeof data.detail === 'string') {
    return data.detail
  }
  return fallback
}

async function requestJson<T>(url: string, options: RequestInit = {}, fallback = 'Nao foi possivel concluir a acao.') {
  const response = await fetch(url, { credentials: 'same-origin', ...options })
  const data = await parseResponse(response)
  if (!response.ok) {
    throw new SchedulingHttpError(response.status, getMessage(data, fallback))
  }
  return data as T
}

export function getSchedules(params: { year: number; month: number; departmentId?: string; status?: string }) {
  const query = new URLSearchParams({
    year: String(params.year),
    month: String(params.month),
  })
  if (params.departmentId) {
    query.set('department_id', params.departmentId)
  }
  if (params.status) {
    query.set('status', params.status)
  }
  return requestJson<ScheduleSummary[]>(`/api/scheduling/schedules/?${query.toString()}`, {}, 'Nao foi possivel carregar as escalas.')
}

export function getSchedulingDepartments() {
  return requestJson<Array<Pick<Department, 'id' | 'nome' | 'codigo' | 'ativo'>>>(
    '/api/scheduling/departments/',
    {},
    'Nao foi possivel carregar departamentos de escala.',
  )
}

export function getMonthlySchedule(year: number, month: number, departmentId: string) {
  const query = new URLSearchParams({
    year: String(year),
    month: String(month),
    department_id: departmentId,
  })
  return requestJson<MonthlySchedule>(
    `/api/scheduling/monthly/?${query.toString()}`,
    {},
    'Nao foi possivel carregar a montagem mensal.',
  )
}

export async function createSchedule(payload: ScheduleCreateInput) {
  const headers = await csrfJsonHeaders()
  return requestJson<ScheduleSummary>(
    '/api/scheduling/schedules/',
    { method: 'POST', headers, body: JSON.stringify(payload) },
    'Nao foi possivel criar a escala.',
  )
}

export function getSchedule(id: number) {
  return requestJson<ScheduleDetail>(`/api/scheduling/schedules/${id}/`, {}, 'Nao foi possivel carregar a escala.')
}

export async function runScheduleLifecycle(id: number, action: 'publish' | 'reopen' | 'cancel' | 'reactivate') {
  const headers = await csrfJsonHeaders()
  return requestJson<ScheduleDetail>(
    `/api/scheduling/schedules/${id}/${action}/`,
    { method: 'POST', headers },
    'Nao foi possivel alterar a escala.',
  )
}

export function getScheduleCandidates(id: number, roleId?: number) {
  const query = roleId ? `?role_id=${roleId}` : ''
  return requestJson<ScheduleCandidate[]>(`/api/scheduling/schedules/${id}/eligible-members/${query}`, {}, 'Nao foi possivel carregar os candidatos.')
}

export async function addScheduleAssignment(scheduleId: number, departmentMembershipId: number) {
  const headers = await csrfJsonHeaders()
  return requestJson<ScheduleAssignment>(
    `/api/scheduling/schedules/${scheduleId}/assignments/`,
    { method: 'POST', headers, body: JSON.stringify({ department_membership_id: departmentMembershipId }) },
    'Nao foi possivel adicionar a pessoa.',
  )
}

export async function deleteScheduleAssignment(scheduleId: number, assignmentId: number) {
  const headers = await csrfJsonHeaders()
  const response = await fetch(`/api/scheduling/schedules/${scheduleId}/assignments/${assignmentId}/`, {
    method: 'DELETE',
    credentials: 'same-origin',
    headers,
  })
  if (!response.ok) {
    const data = await parseResponse(response)
    throw new SchedulingHttpError(response.status, getMessage(data, 'Nao foi possivel remover a pessoa.'))
  }
}
