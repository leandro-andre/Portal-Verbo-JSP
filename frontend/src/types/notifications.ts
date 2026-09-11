export type NotificationType =
  | 'SCHEDULE_PUBLISHED'
  | 'SCHEDULE_ASSIGNMENT_ADDED'
  | 'SCHEDULE_ASSIGNMENT_REMOVED'
  | 'SCHEDULE_CANCELLED'

export type PortalNotification = {
  id: number
  type: NotificationType | string
  title: string
  message: string
  target_url: string
  source_app: string
  source_type: string
  source_id: string
  created_at: string
  read_at: string | null
  is_read: boolean
}

export type RecentNotificationsResponse = {
  unread_count: number
  items: PortalNotification[]
}
