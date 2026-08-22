import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { PortalUser } from '../../types/user'
import AccessStatusBadge from './AccessStatusBadge'

function formatDate(value?: string | null) {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeZone: 'America/Sao_Paulo',
  }).format(new Date(value))
}

function UsersTable({ users }: { users: PortalUser[] }) {
  return (
    <div className="table-shell">
      <table className="people-table">
        <thead>
          <tr>
            <th>Pessoa</th>
            <th>Usuario</th>
            <th>Status do acesso</th>
            <th>Ultimo login</th>
            <th>Criado em</th>
            <th aria-label="Acao" />
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>
                <strong>{user.person?.display_name || '-'}</strong>
              </td>
              <td>{user.username}</td>
              <td>
                <AccessStatusBadge status={user.access_status} />
              </td>
              <td>{formatDate(user.last_login)}</td>
              <td>{formatDate(user.date_joined)}</td>
              <td>
                <Link
                  className="icon-button icon-button--table"
                  to={`/usuarios/${user.id}`}
                  aria-label={`Gerenciar usuario ${user.username}`}
                >
                  <ChevronRight size={18} aria-hidden="true" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default UsersTable
