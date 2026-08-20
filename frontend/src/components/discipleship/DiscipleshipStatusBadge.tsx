import type { DiscipleshipClassStatus } from '../../types/discipleship'
import { discipleshipStatusLabel } from '../../utils/discipleship'

function DiscipleshipStatusBadge({ status }: { status: DiscipleshipClassStatus }) {
  return (
    <span className={`status-badge discipleship-status-badge--${status.toLowerCase().replace('_', '-')}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {discipleshipStatusLabel(status)}
    </span>
  )
}

export default DiscipleshipStatusBadge
