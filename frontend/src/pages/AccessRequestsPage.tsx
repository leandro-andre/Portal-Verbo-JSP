import { useState } from 'react'
import AccessRequestsTable from '../components/accessRequests/AccessRequestsTable'
import { AccessRequestHttpError } from '../api/accessRequests'
import { useAccessRequests } from '../hooks/useAccessRequests'
import type { AccessRequestStatus } from '../types/accessRequest'

const filters: Array<{ label: string; value: AccessRequestStatus }> = [
  { label: 'Pendentes', value: 'PENDING' },
  { label: 'Aprovadas', value: 'APPROVED' },
  { label: 'Rejeitadas', value: 'REJECTED' },
]

function AccessRequestsPage() {
  const [statusFilter, setStatusFilter] = useState<AccessRequestStatus>('PENDING')
  const { data: accessRequests = [], error, isError, isLoading, refetch } = useAccessRequests(statusFilter)
  const isForbidden = error instanceof AccessRequestHttpError && error.status === 403

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Solicitacoes de acesso</h1>
          <p className="page-heading__description">
            Analise as solicitacoes de acesso enviadas ao Portal.
          </p>
        </div>
      </div>

      <div className="segmented-filter" aria-label="Filtrar solicitacoes por status">
        {filters.map((filter) => (
          <button
            className={`segmented-filter__button${statusFilter === filter.value ? ' segmented-filter__button--active' : ''}`}
            key={filter.value}
            type="button"
            onClick={() => setStatusFilter(filter.value)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="state-panel">
          <h2>Carregando solicitacoes...</h2>
          <p>Aguarde enquanto os dados sao carregados.</p>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>{isForbidden ? 'Acesso nao autorizado.' : 'Nao foi possivel carregar as solicitacoes.'}</h2>
          <p>
            {isForbidden
              ? 'Sua sessao atual nao possui permissao para revisar solicitacoes de acesso.'
              : 'Verifique a conexao com o backend e tente novamente.'}
          </p>
          {!isForbidden ? (
            <button className="button button--secondary" type="button" onClick={() => void refetch()}>
              Tentar novamente
            </button>
          ) : null}
        </div>
      ) : accessRequests.length > 0 ? (
        <AccessRequestsTable accessRequests={accessRequests} />
      ) : (
        <div className="state-panel">
          <h2>Nenhuma solicitacao encontrada.</h2>
          <p>Quando houver solicitacoes neste status, elas aparecerao aqui.</p>
        </div>
      )}
    </section>
  )
}

export default AccessRequestsPage
