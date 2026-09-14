import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, MapPinned, Save } from 'lucide-react'
import { DiaconiaApiValidationError, DiaconiaBusinessError } from '../api/diaconia'
import { useCountingEnvironments, useCreateAttendanceCount } from '../hooks/useDiaconiaStock'
import type { AttendanceCount, AttendanceShift } from '../types/diaconia'

const shiftOptions: Array<{ value: AttendanceShift; label: string }> = [
  { value: 'MORNING', label: 'Manha' },
  { value: 'AFTERNOON', label: 'Tarde' },
  { value: 'EVENING', label: 'Noite' },
]

function todayInputValue() {
  const date = new Date()
  const timezoneOffset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - timezoneOffset).toISOString().slice(0, 10)
}

function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `${day}/${month}/${year}`
}

function DiaconiaCountingCreatePage() {
  const { data: environments = [], isError, isLoading, refetch } = useCountingEnvironments({ status: 'ACTIVE' })
  const createAttendanceCount = useCreateAttendanceCount()
  const [date, setDate] = useState(todayInputValue)
  const [shift, setShift] = useState<AttendanceShift>('MORNING')
  const [notes, setNotes] = useState('')
  const [quantities, setQuantities] = useState<Record<number, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [createdCount, setCreatedCount] = useState<AttendanceCount | null>(null)

  const total = useMemo(
    () =>
      environments.reduce((sum, environment) => {
        const value = Number.parseInt(quantities[environment.id] || '0', 10)
        return sum + (Number.isFinite(value) && value > 0 ? value : 0)
      }, 0),
    [environments, quantities],
  )

  const isSubmitting = createAttendanceCount.isPending

  const handleQuantityChange = (environmentId: number, value: string) => {
    const sanitized = value.replace(/[^\d]/g, '')
    setQuantities((current) => ({ ...current, [environmentId]: sanitized || '0' }))
    setCreatedCount(null)
    setError(null)
  }

  const handleSubmit = async () => {
    setError(null)
    setCreatedCount(null)
    try {
      const created = await createAttendanceCount.mutateAsync({
        date,
        shift,
        notes,
        entries: environments.map((environment) => ({
          environment_id: environment.id,
          quantity: Number.parseInt(quantities[environment.id] || '0', 10),
        })),
      })
      setCreatedCount(created)
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
      setError('Nao foi possivel registrar a contagem.')
    }
  }

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/contagens">Contagens</Link>
        <span aria-hidden="true">/</span>
        <strong>Nova contagem</strong>
      </nav>

      <div className="page-heading">
        <div>
          <h1>Nova contagem</h1>
          <p className="page-heading__description">Informe data, turno e quantidade de pessoas por ambiente ativo.</p>
        </div>
      </div>

      {createdCount ? (
        <div className="form-alert form-alert--success" role="status">
          <CheckCircle2 size={18} aria-hidden="true" />
          Contagem registrada com sucesso: {formatDate(createdCount.date)}, {createdCount.shift_label}, {createdCount.total_people} pessoas.
        </div>
      ) : null}
      {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

      {isLoading ? (
        <div className="state-panel"><h2>Carregando ambientes...</h2></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar ambientes.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : environments.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhum ambiente ativo foi cadastrado.</h2>
          <p>Cadastre ou reative ambientes antes de registrar uma contagem.</p>
          <Link className="button button--primary" to="/diaconia/contagens/ambientes">
            <MapPinned size={17} aria-hidden="true" />
            Gerenciar ambientes
          </Link>
        </div>
      ) : (
        <>
          <div className="diaconia-counting-form">
            <div className="form-grid">
              <div className="field-group">
                <label htmlFor="attendance-date">Data</label>
                <input id="attendance-date" type="date" value={date} onChange={(event) => setDate(event.target.value)} />
              </div>
              <div className="field-group">
                <label htmlFor="attendance-shift">Turno</label>
                <select id="attendance-shift" value={shift} onChange={(event) => setShift(event.target.value as AttendanceShift)}>
                  {shiftOptions.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
              <div className="field-group field-group--wide">
                <label htmlFor="attendance-notes">Observacao</label>
                <textarea
                  id="attendance-notes"
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  rows={3}
                  placeholder="Culto especial, sala fechada, contagem realizada depois do inicio..."
                />
              </div>
            </div>

            <div className="diaconia-counting-total" aria-live="polite">
              <span>Total</span>
              <strong>{total} pessoas</strong>
            </div>

            <div className="diaconia-counting-entry-list">
              {environments.map((environment) => (
                <label className="diaconia-counting-entry" key={environment.id} htmlFor={`environment-${environment.id}`}>
                  <span>{environment.name}</span>
                  <small>Pessoas</small>
                  <input
                    id={`environment-${environment.id}`}
                    type="number"
                    inputMode="numeric"
                    min="0"
                    step="1"
                    value={quantities[environment.id] ?? '0'}
                    onChange={(event) => handleQuantityChange(environment.id, event.target.value)}
                  />
                </label>
              ))}
            </div>
          </div>

          <div className="form-actions">
            <button className="button button--primary" type="button" disabled={isSubmitting} onClick={() => void handleSubmit()}>
              <Save size={17} aria-hidden="true" />
              Registrar contagem
            </button>
            <Link className="button button--secondary" to="/diaconia/contagens">Voltar para Contagens</Link>
            {createdCount ? (
              <Link className="button button--secondary" to={`/diaconia/contagens/${createdCount.id}`}>Ver contagem</Link>
            ) : null}
          </div>
        </>
      )}
    </section>
  )
}

export default DiaconiaCountingCreatePage
