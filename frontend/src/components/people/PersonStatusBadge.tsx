import type { PersonStatus } from '../../types/person'

type PersonStatusBadgeProps = {
  status: PersonStatus
}

function PersonStatusBadge({ status }: PersonStatusBadgeProps) {
  const isActive = status === 'ACTIVE'

  return (
    <span className={`status-badge${isActive ? ' status-badge--active' : ' status-badge--inactive'}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {isActive ? 'Ativo' : 'Inativo'}
    </span>
  )
}

export default PersonStatusBadge
