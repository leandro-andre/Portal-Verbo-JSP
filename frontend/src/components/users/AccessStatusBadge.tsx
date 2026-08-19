import type { AccessStatus } from '../../types/user'

const labels: Record<AccessStatus, string> = {
  PENDING_ACTIVATION: 'Aguardando ativacao',
  ACTIVE: 'Ativo',
  BLOCKED: 'Bloqueado',
}

function AccessStatusBadge({ status }: { status: AccessStatus }) {
  return (
    <span className={`status-badge user-status-badge--${status.toLowerCase().replace('_', '-')}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {labels[status]}
    </span>
  )
}

export default AccessStatusBadge
