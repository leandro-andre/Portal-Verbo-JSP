import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Save } from 'lucide-react'
import { DiaconiaApiValidationError, DiaconiaBusinessError } from '../api/diaconia'
import { useAttendanceCount, useUpdateAttendanceCount } from '../hooks/useDiaconiaStock'
import type { AttendanceCount, AttendanceShift } from '../types/diaconia'

const shiftOptions: Array<{ value: AttendanceShift; label: string }> = [
  { value: 'MORNING', label: 'Manha' },
  { value: 'AFTERNOON', label: 'Tarde' },
  { value: 'EVENING', label: 'Noite' },
]

function AttendanceCountEditForm({ count }: { count: AttendanceCount }) {
  const navigate = useNavigate()
  const updateAttendanceCount = useUpdateAttendanceCount(count.id)
  const [date, setDate] = useState(count.date)
  const [shift, setShift] = useState<AttendanceShift>(count.shift)
  const [notes, setNotes] = useState(count.notes)
  const [quantities, setQuantities] = useState<Record<number, string>>(
    Object.fromEntries(count.entries.map((entry) => [entry.environment.id, String(entry.quantity)])),
  )
  const [error, setError] = useState<string | null>(null)

  const total = useMemo(
    () =>
      count.entries.reduce((sum, entry) => {
        const value = Number.parseInt(quantities[entry.environment.id] || '0', 10)
        return sum + (Number.isFinite(value) && value > 0 ? value : 0)
      }, 0),
    [count, quantities],
  )

  const handleQuantityChange = (environmentId: number, value: string) => {
    const sanitized = value.replace(/[^\d]/g, '')
    setQuantities((current) => ({ ...current, [environmentId]: sanitized || '0' }))
    setError(null)
  }

  const handleSubmit = async () => {
    setError(null)
    try {
      const updated = await updateAttendanceCount.mutateAsync({
        date,
        shift,
        notes,
        entries: count.entries.map((entry) => ({
          environment_id: entry.environment.id,
          quantity: Number.parseInt(quantities[entry.environment.id] || '0', 10),
        })),
      })
      navigate(`/diaconia/contagens/${updated.id}`)
    } catch (submitError) {
      if (submitError instanceof DiaconiaApiValidationError) {
        const firstMessage = Object.values(submitError.fieldErrors).flat()[0]
        setError(firstMessage ?? 'Confira os dados da contagem.')
        return
      }
      if (submitError instanceof DiaconiaBusinessError) {
        setError(submitError.message)
        return
      }
      setError('Nao foi possivel editar a contagem.')
    }
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Editar contagem</h1>
          <p className="page-heading__description">Ajuste os dados registrados nesta contagem.</p>
        </div>
      </div>

      {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

      <div className="diaconia-counting-form">
        <div className="form-grid">
          <div className="field-group">
            <label htmlFor="attendance-edit-date">Data</label>
            <input id="attendance-edit-date" type="date" value={date} onChange={(event) => setDate(event.target.value)} />
          </div>
          <div className="field-group">
            <label htmlFor="attendance-edit-shift">Turno</label>
            <select id="attendance-edit-shift" value={shift} onChange={(event) => setShift(event.target.value as AttendanceShift)}>
              {shiftOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          <div className="field-group field-group--wide">
            <label htmlFor="attendance-edit-notes">Observacao</label>
            <textarea id="attendance-edit-notes" value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} />
          </div>
        </div>

        <div className="diaconia-counting-total" aria-live="polite">
          <span>Total corrigido</span>
          <strong>{total} pessoas</strong>
        </div>

        <div className="diaconia-counting-entry-list">
          {count.entries.map((entry) => (
            <label className="diaconia-counting-entry" key={entry.id} htmlFor={`entry-${entry.id}`}>
              <span>{entry.environment.name}</span>
              <small>{entry.environment.is_active ? 'Pessoas' : 'Pessoas - ambiente inativo'}</small>
              <input
                id={`entry-${entry.id}`}
                type="number"
                inputMode="numeric"
                min="0"
                step="1"
                value={quantities[entry.environment.id] ?? '0'}
                onChange={(event) => handleQuantityChange(entry.environment.id, event.target.value)}
              />
            </label>
          ))}
        </div>
      </div>

      <div className="form-actions">
        <button className="button button--primary" type="button" disabled={updateAttendanceCount.isPending} onClick={() => void handleSubmit()}>
          <Save size={17} aria-hidden="true" />
          Salvar correcao
        </button>
        <Link className="button button--secondary" to={`/diaconia/contagens/${count.id}`}>Cancelar</Link>
      </div>
    </>
  )
}

function DiaconiaCountingEditPage() {
  const { id } = useParams()
  const countId = Number(id)
  const { data: count, isError, isLoading, refetch } = useAttendanceCount(countId)

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/contagens">Contagens</Link>
        <span aria-hidden="true">/</span>
        <strong>Editar contagem</strong>
      </nav>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando contagem...</h2></div>
      ) : isError || !count ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar a contagem.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : (
        <AttendanceCountEditForm key={count.id} count={count} />
      )}
    </section>
  )
}

export default DiaconiaCountingEditPage
