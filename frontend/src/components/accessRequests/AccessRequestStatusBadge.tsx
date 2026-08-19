import type { AccessRequestStatus } from '../../types/accessRequest'

type AccessRequestStatusBadgeProps = {
  status: AccessRequestStatus
}

const labels: Record<AccessRequestStatus, string> = {
  PENDING: 'Pendente',
  APPROVED: 'Aprovada',
  REJECTED: 'Rejeitada',
}

function AccessRequestStatusBadge({ status }: AccessRequestStatusBadgeProps) {
  return (
    <span className={`status-badge access-status-badge access-status-badge--${status.toLowerCase()}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {labels[status]}
    </span>
  )
}

export default AccessRequestStatusBadge
