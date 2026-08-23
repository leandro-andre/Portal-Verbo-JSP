import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import { ApiHttpError } from '../api/people'
import { useEligibleMembershipPeople, useMemberships } from '../hooks/usePeople'
import type { MembershipStatus } from '../types/person'

type MembershipTab = 'PENDING' | MembershipStatus

const tabs: Array<{ label: string; value: MembershipTab }> = [
  { label: 'Pendentes', value: 'PENDING' },
  { label: 'Membros ativos', value: 'ACTIVE' },
  { label: 'Inativos', value: 'INACTIVE' },
]

function formatDate(value: string) {
  if (!value) {
    return '-'
  }

  const [year, month, day] = value.split('-')
  return year && month && day ? `${day}/${month}/${year}` : value
}

function MembershipPage() {
  const [tab, setTab] = useState<MembershipTab>('PENDING')
  const pendingQuery = useEligibleMembershipPeople()
  const membershipsQuery = useMemberships(tab === 'PENDING' ? undefined : tab)
  const isPendingTab = tab === 'PENDING'
  const isLoading = isPendingTab ? pendingQuery.isLoading : membershipsQuery.isLoading
  const isError = isPendingTab ? pendingQuery.isError : membershipsQuery.isError
  const error = isPendingTab ? pendingQuery.error : membershipsQuery.error
  const refetch = isPendingTab ? pendingQuery.refetch : membershipsQuery.refetch
  const isForbidden = error instanceof ApiHttpError && error.status === 403
  const pendingPeople = pendingQuery.data ?? []
  const memberships = membershipsQuery.data ?? []

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Membresia</h1>
          <p className="page-heading__description">Acompanhe aprovacoes e situacao das membresias.</p>
        </div>
      </div>

      <div className="segmented-filter" aria-label="Filtrar membresia">
        {tabs.map((item) => (
          <button
            className={`segmented-filter__button${tab === item.value ? ' segmented-filter__button--active' : ''}`}
            key={item.value}
            type="button"
            onClick={() => setTab(item.value)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="state-panel">
          <h2>Carregando membresia...</h2>
          <p>Aguarde enquanto buscamos os dados.</p>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <ShieldCheck size={26} aria-hidden="true" />
          <h2>{isForbidden ? 'Acesso negado' : 'Nao foi possivel carregar membresia.'}</h2>
          <p>
            {isForbidden
              ? 'Sua sessao atual nao possui permissao para visualizar membresia.'
              : 'Verifique a conexao com o backend e tente novamente.'}
          </p>
          {!isForbidden ? (
            <button className="button button--secondary" type="button" onClick={() => void refetch()}>
              Tentar novamente
            </button>
          ) : null}
        </div>
      ) : isPendingTab ? (
        pendingPeople.length === 0 ? (
          <div className="state-panel">
            <h2>Nenhuma pendencia</h2>
            <p>Nao ha pessoas elegiveis aguardando aprovacao de membresia.</p>
          </div>
        ) : (
          <div className="table-shell">
            <table className="people-table">
              <thead>
                <tr>
                  <th>Pessoa</th>
                  <th>Discipulado concluido em</th>
                  <th aria-label="Acao" />
                </tr>
              </thead>
              <tbody>
                {pendingPeople.map((person) => (
                  <tr key={person.id}>
                    <td>
                      <Link className="person-name-link" to={`/pessoas/${person.id}`}>
                        {person.display_name}
                      </Link>
                      <span className="table-muted">{person.full_name}</span>
                    </td>
                    <td>{formatDate(person.completed_at)}</td>
                    <td>
                      <Link className="button button--secondary" to={`/pessoas/${person.id}`}>
                        Ver pessoa
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : memberships.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhum registro</h2>
          <p>Nao ha membresias nesta situacao.</p>
        </div>
      ) : (
        <div className="table-shell">
          <table className="people-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Membro desde</th>
                <th>Status</th>
                <th aria-label="Acao" />
              </tr>
            </thead>
            <tbody>
              {memberships.map((membership) => (
                <tr key={membership.id}>
                  <td>
                    <Link className="person-name-link" to={`/pessoas/${membership.person_id}`}>
                      {membership.person?.display_name || `Pessoa ${membership.person_id}`}
                    </Link>
                  </td>
                  <td>{formatDate(membership.member_since)}</td>
                  <td>{membership.status === 'ACTIVE' ? 'Ativo' : 'Inativo'}</td>
                  <td>
                    <Link className="button button--secondary" to={`/pessoas/${membership.person_id}`}>
                      Ver pessoa
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default MembershipPage
