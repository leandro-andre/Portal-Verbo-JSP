import { CheckCheck, RefreshCcw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import NotificationItem from '../components/notifications/NotificationItem'
import { useNotificationMutations, useNotifications } from '../hooks/useNotifications'
import type { PortalNotification } from '../types/notifications'

function NotificationsPage() {
  const navigate = useNavigate()
  const { data, isError, isLoading, refetch } = useNotifications()
  const { markRead, markAllRead } = useNotificationMutations()
  const notifications = data ?? []

  const handleOpenNotification = async (notification: PortalNotification) => {
    await markRead.mutateAsync(notification.id)
    if (notification.target_url) {
      navigate(notification.target_url)
    }
  }

  return (
    <section className="people-page notifications-page">
      <div className="page-heading">
        <div>
          <h1>Notificacoes</h1>
          <p className="page-heading__description">Acompanhe avisos internos do Portal.</p>
        </div>
        <button
          className="button button--secondary"
          type="button"
          onClick={() => void markAllRead.mutateAsync()}
          disabled={markAllRead.isPending || notifications.length === 0}
        >
          <CheckCheck size={17} aria-hidden="true" />
          Marcar todas como lidas
        </button>
      </div>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando notificacoes...</h2></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar notificacoes.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            <RefreshCcw size={17} aria-hidden="true" />
            Tentar novamente
          </button>
        </div>
      ) : notifications.length === 0 ? (
        <div className="state-panel">
          <h2>Voce ainda nao possui notificacoes.</h2>
        </div>
      ) : (
        <div className="notifications-page__list">
          {notifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onOpen={(item) => void handleOpenNotification(item)}
            />
          ))}
        </div>
      )}
    </section>
  )
}

export default NotificationsPage
