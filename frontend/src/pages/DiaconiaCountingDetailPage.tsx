import { Link, useParams } from 'react-router-dom'
import { Pencil } from 'lucide-react'
import { useCan } from '../hooks/useAuth'
import { useAttendanceCount } from '../hooks/useDiaconiaStock'

function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `${day}/${month}/${year}`
}

function DiaconiaCountingDetailPage() {
  const { id } = useParams()
  const countId = Number(id)
  const { data: count, isError, isLoading, refetch } = useAttendanceCount(countId)
  const canManage = useCan('DIACONIA_COUNTING_MANAGE')

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/contagens">Contagens</Link>
        <span aria-hidden="true">/</span>
        <strong>Contagem</strong>
      </nav>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando contagem...</h2></div>
      ) : isError || !count ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar a contagem.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : (
        <>
          <div className="page-heading">
            <div>
              <h1>Contagem</h1>
              <p className="page-heading__description">
                {formatDate(count.date)} - {count.shift_label} - registrada por {count.created_by.display_name}
              </p>
            </div>
            <div className="diaconia-stock-actions">
              {canManage ? (
                <Link className="button button--primary" to={`/diaconia/contagens/${count.id}/editar`}>
                  <Pencil size={17} aria-hidden="true" />
                  Editar contagem
                </Link>
              ) : null}
              <Link className="button button--secondary" to="/diaconia/contagens">Voltar</Link>
            </div>
          </div>

          <div className="diaconia-counting-total">
            <span>Total registrado</span>
            <strong>{count.total_people} pessoas</strong>
          </div>

          {count.notes ? (
            <div className="diaconia-stock-readonly">
              <span>Observacao</span>
              <strong>{count.notes}</strong>
            </div>
          ) : null}

          <div className="diaconia-counting-info-grid">
            <div className="diaconia-stock-readonly">
              <span>Responsavel</span>
              <strong>{count.created_by.display_name}</strong>
            </div>
            <div className="diaconia-stock-readonly">
              <span>Criado em</span>
              <strong>{new Date(count.created_at).toLocaleString('pt-BR')}</strong>
            </div>
            <div className="diaconia-stock-readonly">
              <span>Atualizado em</span>
              <strong>{new Date(count.updated_at).toLocaleString('pt-BR')}</strong>
            </div>
          </div>

          <div className="diaconia-counting-entry-list">
            {count.entries.map((entry) => (
              <div className="diaconia-counting-entry" key={entry.id}>
                <span>{entry.environment.name}</span>
                <small>Pessoas</small>
                <strong>{entry.quantity}</strong>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  )
}

export default DiaconiaCountingDetailPage
