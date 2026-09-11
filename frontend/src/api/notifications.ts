import type { PortalNotification, RecentNotificationsResponse } from '../types/notifications'
import { csrfJsonHeaders } from './http'

class NotificationsHttpError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'NotificationsHttpError'
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
    throw new NotificationsHttpError(response.status, getMessage(data, fallback))
  }
  return data as T
}

export function getNotifications() {
  return requestJson<PortalNotification[]>('/api/notifications/', {}, 'Nao foi possivel carregar notificacoes.')
}

export function getRecentNotifications() {
  return requestJson<RecentNotificationsResponse>(
    '/api/notifications/recent/',
    {},
    'Nao foi possivel carregar notificacoes recentes.',
  )
}

export async function markNotificationRead(id: number) {
  const headers = await csrfJsonHeaders()
  return requestJson<PortalNotification>(
    `/api/notifications/${id}/read/`,
    { method: 'POST', headers },
    'Nao foi possivel marcar a notificacao como lida.',
  )
}

export async function markAllNotificationsRead() {
  const headers = await csrfJsonHeaders()
  return requestJson<{ marked_count: number; unread_count: number }>(
    '/api/notifications/read-all/',
    { method: 'POST', headers },
    'Nao foi possivel marcar notificacoes como lidas.',
  )
}
