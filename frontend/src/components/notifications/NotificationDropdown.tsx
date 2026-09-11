import { CheckCheck, RefreshCcw } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { PortalNotification } from '../../types/notifications'
import NotificationItem from './NotificationItem'

type NotificationDropdownProps = {
  items: PortalNotification[]
  isError: boolean
  isLoading: boolean
  isMarkingAll: boolean
  onMarkAllRead: () => void
  onOpenNotification: (notification: PortalNotification) => void
  onRetry: () => void
}

function NotificationDropdown({
  items,
  isError,
  isLoading,
  isMarkingAll,
  onMarkAllRead,
  onOpenNotification,
  onRetry,
}: NotificationDropdownProps) {
  return (
    <section className="notifications-dropdown" aria-label="Notificacoes recentes">
      <div className="notifications-dropdown__header">
        <h2>Notificacoes</h2>
        <button
          className="notifications-dropdown__action"
          type="button"
          onClick={onMarkAllRead}
          disabled={isMarkingAll || items.length === 0}
        >
          <CheckCheck size={15} aria-hidden="true" />
          Marcar todas
        </button>
      </div>

      <div className="notifications-dropdown__content">
        {isLoading ? (
          <p className="notifications-dropdown__state">Carregando notificacoes...</p>
        ) : isError ? (
          <div className="notifications-dropdown__state notifications-dropdown__state--action">
            <span>Nao foi possivel carregar.</span>
            <button className="icon-button" type="button" onClick={onRetry} aria-label="Tentar novamente">
              <RefreshCcw size={16} aria-hidden="true" />
            </button>
          </div>
        ) : items.length === 0 ? (
          <p className="notifications-dropdown__state">Voce ainda nao possui notificacoes.</p>
        ) : (
          <div className="notifications-dropdown__list">
            {items.map((item) => (
              <NotificationItem
                compact
                key={item.id}
                notification={item}
                onOpen={onOpenNotification}
              />
            ))}
          </div>
        )}
      </div>

      <Link className="notifications-dropdown__footer" to="/notificacoes">
        Ver todas
      </Link>
    </section>
  )
}

export default NotificationDropdown
