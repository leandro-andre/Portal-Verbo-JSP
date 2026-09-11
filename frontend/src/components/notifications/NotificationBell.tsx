import { Bell } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useNotificationMutations, useRecentNotifications } from '../../hooks/useNotifications'
import type { PortalNotification } from '../../types/notifications'
import NotificationDropdown from './NotificationDropdown'

function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false)
  const wrapperRef = useRef<HTMLDivElement | null>(null)
  const navigate = useNavigate()
  const { data, isError, isLoading, refetch } = useRecentNotifications()
  const { markRead, markAllRead } = useNotificationMutations()
  const unreadCount = data?.unread_count ?? 0
  const badgeLabel = unreadCount > 99 ? '99+' : String(unreadCount)

  useEffect(() => {
    if (!isOpen) return

    const handlePointerDown = (event: PointerEvent) => {
      if (!wrapperRef.current?.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    void refetch()
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, refetch])

  const handleOpenNotification = async (notification: PortalNotification) => {
    await markRead.mutateAsync(notification.id)
    setIsOpen(false)
    if (notification.target_url) {
      navigate(notification.target_url)
    }
  }

  return (
    <div className="notification-bell" ref={wrapperRef}>
      <button
        className="icon-button notification-bell__button"
        type="button"
        aria-label={unreadCount > 0 ? `Notificacoes, ${unreadCount} nao lidas` : 'Notificacoes'}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        onClick={() => setIsOpen((current) => !current)}
      >
        <Bell size={18} aria-hidden="true" />
        {unreadCount > 0 ? <span className="notification-bell__badge">{badgeLabel}</span> : null}
      </button>
      {isOpen ? (
        <NotificationDropdown
          items={data?.items ?? []}
          isError={isError}
          isLoading={isLoading}
          isMarkingAll={markAllRead.isPending}
          onMarkAllRead={() => void markAllRead.mutateAsync()}
          onOpenNotification={(notification) => void handleOpenNotification(notification)}
          onRetry={() => void refetch()}
        />
      ) : null}
    </div>
  )
}

export default NotificationBell
