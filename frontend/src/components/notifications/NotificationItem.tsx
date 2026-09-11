import { Circle } from 'lucide-react'
import type { PortalNotification } from '../../types/notifications'

function relativeNotificationTime(value: string) {
  const then = new Date(value).getTime()
  const now = Date.now()
  const diffMinutes = Math.max(0, Math.floor((now - then) / 60000))
  if (diffMinutes < 1) return 'agora'
  if (diffMinutes < 60) return `ha ${diffMinutes} min`
  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `ha ${diffHours} h`
  if (diffHours < 48) return 'ontem'
  const diffDays = Math.floor(diffHours / 24)
  return `ha ${diffDays} dias`
}

function formatNotificationDate(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
}

type NotificationItemProps = {
  notification: PortalNotification
  compact?: boolean
  onOpen?: (notification: PortalNotification) => void
}

function NotificationItem({ notification, compact = false, onOpen }: NotificationItemProps) {
  const content = (
    <>
      <span className="notification-item__status" aria-hidden="true">
        {!notification.is_read ? <Circle size={9} fill="currentColor" /> : null}
      </span>
      <span className="notification-item__body">
        <strong>{notification.title}</strong>
        <span>{notification.message}</span>
        <time dateTime={notification.created_at}>
          {compact ? relativeNotificationTime(notification.created_at) : formatNotificationDate(notification.created_at)}
        </time>
      </span>
    </>
  )

  if (onOpen) {
    return (
      <button
        className={`notification-item ${notification.is_read ? '' : 'notification-item--unread'}`}
        type="button"
        onClick={() => onOpen(notification)}
      >
        {content}
      </button>
    )
  }

  return (
    <div className={`notification-item ${notification.is_read ? '' : 'notification-item--unread'}`}>
      {content}
    </div>
  )
}

export default NotificationItem
