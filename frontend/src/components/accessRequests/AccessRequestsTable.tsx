import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { AccessRequest } from '../../types/accessRequest'
import { formatBrazilianMobile } from '../../utils/phone'
import AccessRequestStatusBadge from './AccessRequestStatusBadge'

type AccessRequestsTableProps = {
  accessRequests: AccessRequest[]
}

function formatDate(value: string) {
  if (!value) {
    return '-'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    const [year, month, day] = value.split('-')
    return year && month && day ? `${day}/${month}/${year}` : value
  }

  return new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' }).format(date)
}

function AccessRequestsTable({ accessRequests }: AccessRequestsTableProps) {
  return (
    <div className="table-shell">
      <table className="people-table">
        <thead>
          <tr>
            <th scope="col">Nome</th>
            <th scope="col">Contato</th>
            <th scope="col">Nascimento</th>
            <th scope="col">Solicitado em</th>
            <th scope="col">Status</th>
            <th scope="col" className="people-table__actions-header">
              Acao
            </th>
          </tr>
        </thead>
        <tbody>
          {accessRequests.map((accessRequest) => (
            <tr key={accessRequest.id}>
              <td>
                <Link className="person-name-link" to={`/solicitacoes-acesso/${accessRequest.id}`}>
                  {accessRequest.full_name}
                </Link>
              </td>
              <td>
                <div className="contact-cell">
                  <span>{accessRequest.email}</span>
                  <span>{formatBrazilianMobile(accessRequest.phone) || '-'}</span>
                </div>
              </td>
              <td>{formatDate(accessRequest.birth_date)}</td>
              <td>{formatDate(accessRequest.created_at)}</td>
              <td>
                <AccessRequestStatusBadge status={accessRequest.status} />
              </td>
              <td>
                <Link
                  className="icon-button icon-button--table"
                  to={`/solicitacoes-acesso/${accessRequest.id}`}
                  aria-label={`Abrir solicitacao de ${accessRequest.full_name}`}
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

export default AccessRequestsTable
