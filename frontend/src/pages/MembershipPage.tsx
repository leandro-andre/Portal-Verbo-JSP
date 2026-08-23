import { Link } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import { ApiHttpError } from '../api/people'
import { useEligibleMembershipPeople } from '../hooks/usePeople'

function formatDate(value: string) {
  if (!value) {
    return '-'
  }

  const [year, month, day] = value.split('-')
  return year && month && day ? `${day}/${month}/${year}` : value
}

function MembershipPage() {
  const { data: people = [], error, isError, isLoading, refetch } = useEligibleMembershipPeople()
  const isForbidden = error instanceof ApiHttpError && error.status === 403

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Membresia</h1>
          <p className="page-heading__description">Pessoas elegiveis aguardando aprovacao de membresia.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="state-panel">
          <h2>Carregando pendencias...</h2>
          <p>Aguarde enquanto buscamos pessoas elegiveis.</p>
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
      ) : people.length === 0 ? (
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
              {people.map((person) => (
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
      )}
    </section>
  )
}

export default MembershipPage
