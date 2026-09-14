import { useMemo, useState } from 'react'
import { Eye, MapPinned, Pencil, Plus, RotateCcw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useCan } from '../hooks/useAuth'
import { useAttendanceCounts } from '../hooks/useDiaconiaStock'
import type { AttendanceShift } from '../types/diaconia'

const shiftOptions: Array<{ value: '' | AttendanceShift; label: string }> = [
  { value: '', label: 'Todos' },
  { value: 'MORNING', label: 'Manha' },
  { value: 'AFTERNOON', label: 'Tarde' },
  { value: 'EVENING', label: 'Noite' },
]

function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `${day}/${month}/${year}`
}

function DiaconiaCountingPage() {
  const canManage = useCan('DIACONIA_COUNTING_MANAGE')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [shift, setShift] = useState<'' | AttendanceShift>('')
  const filters = useMemo(() => ({ dateFrom, dateTo, shift }), [dateFrom, dateTo, shift])
  const { data: counts = [], isError, isLoading, refetch } = useAttendanceCounts(filters)
  const hasFilters = Boolean(dateFrom || dateTo || shift)

  const clearFilters = () => {
    setDateFrom('')
    setDateTo('')
    setShift('')
  }

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <strong>Contagens</strong>
      </nav>

      <div className="page-heading">
        <div>
          <h1>Contagens</h1>
          <p className="page-heading__description">Historico de publico por data, turno e ambiente.</p>
        </div>
        <div className="diaconia-stock-actions">
          {canManage ? (
            <Link className="button button--primary" to="/diaconia/contagens/nova">
              <Plus size={17} aria-hidden="true" />
              Nova contagem
            </Link>
          ) : null}
          <Link className="button button--secondary" to="/diaconia/contagens/ambientes">
            <MapPinned size={17} aria-hidden="true" />
            Gerenciar ambientes
          </Link>
        </div>
      </div>

      <div className="people-toolbar diaconia-stock-filters">
        <label className="status-filter" htmlFor="counting-date-from">
          <span>Data inicial</span>
          <input id="counting-date-from" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
        </label>
        <label className="status-filter" htmlFor="counting-date-to">
          <span>Data final</span>
          <input id="counting-date-to" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
        </label>
        <label className="status-filter" htmlFor="counting-shift">
          <span>Turno</span>
          <select id="counting-shift" value={shift} onChange={(event) => setShift(event.target.value as '' | AttendanceShift)}>
            {shiftOptions.map((option) => (
              <option key={option.label} value={option.value}>{option.label}</option>
            ))}
          </select>
        </label>
        {hasFilters ? (
          <button className="button button--secondary" type="button" onClick={clearFilters}>
            <RotateCcw size={17} aria-hidden="true" />
            Limpar filtros
          </button>
        ) : null}
      </div>

      <div className="diaconia-counting-result-count">
        {counts.length} {counts.length === 1 ? 'contagem encontrada' : 'contagens encontradas'}
      </div>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando contagens...</h2></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar contagens.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : counts.length === 0 ? (
        <div className="state-panel">
          <h2>{hasFilters ? 'Nenhuma contagem encontrada para os filtros selecionados.' : 'Nenhuma contagem registrada.'}</h2>
          <p>{hasFilters ? 'Limpe os filtros para ver outros registros.' : 'Registre a primeira contagem para iniciar o historico.'}</p>
          {hasFilters ? (
            <button className="button button--secondary" type="button" onClick={clearFilters}>
              <RotateCcw size={17} aria-hidden="true" />
              Limpar filtros
            </button>
          ) : canManage ? (
            <Link className="button button--primary" to="/diaconia/contagens/nova">
              <Plus size={17} aria-hidden="true" />
              Registrar primeira contagem
            </Link>
          ) : null}
        </div>
      ) : (
        <>
          <div className="table-shell diaconia-counting-table">
            <table className="people-table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Turno</th>
                  <th>Total</th>
                  <th>Responsavel</th>
                  <th aria-label="Acoes" />
                </tr>
              </thead>
              <tbody>
                {counts.map((count) => (
                  <tr key={count.id}>
                    <td>{formatDate(count.date)}</td>
                    <td>{count.shift_label}</td>
                    <td><strong>{count.total_people} pessoas</strong></td>
                    <td>{count.created_by.display_name}</td>
                    <td>
                      <div className="table-actions">
                        <Link className="button button--secondary" to={`/diaconia/contagens/${count.id}`}>
                          <Eye size={17} aria-hidden="true" />
                          Ver
                        </Link>
                        {canManage ? (
                          <Link className="button button--secondary" to={`/diaconia/contagens/${count.id}/editar`}>
                            <Pencil size={17} aria-hidden="true" />
                            Editar
                          </Link>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="diaconia-counting-card-list">
            {counts.map((count) => (
              <article className="diaconia-counting-history-card" key={count.id}>
                <div>
                  <h2>{formatDate(count.date)} · {count.shift_label}</h2>
                  <p>{count.total_people} pessoas</p>
                  <span>Registrado por {count.created_by.display_name}</span>
                </div>
                <div className="diaconia-stock-actions">
                  <Link className="button button--secondary" to={`/diaconia/contagens/${count.id}`}>
                    <Eye size={17} aria-hidden="true" />
                    Ver detalhes
                  </Link>
                  {canManage ? (
                    <Link className="button button--secondary" to={`/diaconia/contagens/${count.id}/editar`}>
                      <Pencil size={17} aria-hidden="true" />
                      Editar
                    </Link>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  )
}

export default DiaconiaCountingPage
