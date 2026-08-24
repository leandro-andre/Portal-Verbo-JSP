import { useState } from 'react'
import type { FormEvent } from 'react'
import { Plus, RefreshCcw } from 'lucide-react'
import { useMyUnavailability, useMyUnavailabilityMutations } from '../hooks/usePeople'
import type { PersonUnavailability, PersonUnavailabilityInput } from '../types/person'

function todayInput() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  return year && month && day ? `${day}/${month}/${year}` : value
}

function formatTime(value: string | null) {
  return value ? value.slice(0, 5) : null
}

function periodLabel(unavailability: PersonUnavailability) {
  const dateLabel = unavailability.start_date === unavailability.end_date
    ? formatDate(unavailability.start_date)
    : `${formatDate(unavailability.start_date)} a ${formatDate(unavailability.end_date)}`
  const startTime = formatTime(unavailability.start_time)
  const endTime = formatTime(unavailability.end_time)
  return startTime && endTime ? `${dateLabel}, ${startTime} a ${endTime}` : `${dateLabel}, periodo integral`
}

function UnavailabilityForm({
  initial,
  isPending,
  onSubmit,
}: {
  initial?: PersonUnavailability | null
  isPending: boolean
  onSubmit: (payload: PersonUnavailabilityInput) => void
}) {
  const [startDate, setStartDate] = useState(initial?.start_date ?? todayInput())
  const [endDate, setEndDate] = useState(initial?.end_date ?? initial?.start_date ?? todayInput())
  const [hasTime, setHasTime] = useState(Boolean(initial?.start_time && initial?.end_time))
  const [startTime, setStartTime] = useState(formatTime(initial?.start_time ?? null) ?? '')
  const [endTime, setEndTime] = useState(formatTime(initial?.end_time ?? null) ?? '')
  const [reason, setReason] = useState(initial?.reason ?? '')

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit({
      start_date: startDate,
      end_date: hasTime ? startDate : endDate,
      start_time: hasTime ? startTime : null,
      end_time: hasTime ? endTime : null,
      reason,
    })
    if (!initial) {
      setStartDate(todayInput())
      setEndDate(todayInput())
      setHasTime(false)
      setStartTime('')
      setEndTime('')
      setReason('')
    }
  }

  return (
    <form className="department-inline-form" onSubmit={handleSubmit}>
      <label className="form-field">
        <span>Data inicial</span>
        <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} required />
      </label>
      {!hasTime ? (
        <label className="form-field">
          <span>Data final</span>
          <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} required />
        </label>
      ) : null}
      <label className="checkbox-field">
        <input
          type="checkbox"
          checked={hasTime}
          onChange={(event) => {
            setHasTime(event.target.checked)
            if (event.target.checked) {
              setEndDate(startDate)
            }
          }}
        />
        <span>Informar horario especifico</span>
      </label>
      {hasTime ? (
        <>
          <label className="form-field">
            <span>Hora inicial</span>
            <input type="time" value={startTime} onChange={(event) => setStartTime(event.target.value)} required />
          </label>
          <label className="form-field">
            <span>Hora final</span>
            <input type="time" value={endTime} onChange={(event) => setEndTime(event.target.value)} required />
          </label>
        </>
      ) : null}
      <label className="form-field">
        <span>Motivo</span>
        <input value={reason} placeholder="Opcional" onChange={(event) => setReason(event.target.value)} />
      </label>
      <button className="button button--primary" type="submit" disabled={isPending}>
        <Plus size={17} aria-hidden="true" />
        {isPending ? 'Salvando...' : 'Salvar indisponibilidade'}
      </button>
    </form>
  )
}

function MyUnavailabilityPage() {
  const { data: unavailabilities = [], isError, isLoading, refetch } = useMyUnavailability()
  const mutations = useMyUnavailabilityMutations()
  const [editing, setEditing] = useState<PersonUnavailability | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const isPending = mutations.create.isPending || mutations.update.isPending

  const runAction = async (action: () => Promise<unknown>, success: string) => {
    setError(null)
    try {
      await action()
      setMessage(success)
      setEditing(null)
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : 'Nao foi possivel concluir a acao.')
    }
  }

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Minhas indisponibilidades</h1>
          <p className="page-heading__description">Registre os periodos em que voce nao podera servir.</p>
        </div>
      </div>

      {message ? <div className="form-alert form-alert--success" role="status">{message}</div> : null}
      {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

      <section className="profile-section">
        <h2>{editing ? 'Editar indisponibilidade' : 'Nova indisponibilidade'}</h2>
        <UnavailabilityForm
          key={editing?.id ?? 'new'}
          initial={editing}
          isPending={isPending}
          onSubmit={(payload) =>
            void runAction(
              () => editing
                ? mutations.update.mutateAsync({ id: editing.id, payload })
                : mutations.create.mutateAsync(payload),
              editing ? 'Indisponibilidade atualizada.' : 'Indisponibilidade cadastrada.',
            )
          }
        />
        {editing ? (
          <button className="button button--secondary" type="button" onClick={() => setEditing(null)}>
            Cancelar edicao
          </button>
        ) : null}
      </section>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando indisponibilidades...</h2></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar suas indisponibilidades.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            Tentar novamente
          </button>
        </div>
      ) : (
        <div className="table-shell">
          <table className="people-table">
            <thead>
              <tr>
                <th>Periodo</th>
                <th>Status</th>
                <th>Motivo</th>
                <th className="people-table__actions-header">Acao</th>
              </tr>
            </thead>
            <tbody>
              {unavailabilities.map((item) => (
                <tr key={item.id}>
                  <td>{periodLabel(item)}</td>
                  <td>{item.status === 'ACTIVE' ? 'Ativa' : 'Inativa'}</td>
                  <td>{item.reason || '-'}</td>
                  <td>
                    <div className="table-actions">
                      {item.status === 'ACTIVE' ? (
                        <button className="button button--secondary" type="button" onClick={() => setEditing(item)}>
                          Editar
                        </button>
                      ) : null}
                      <button
                        className="button button--secondary"
                        type="button"
                        onClick={() =>
                          void runAction(
                            () => item.status === 'ACTIVE'
                              ? mutations.deactivate.mutateAsync(item.id)
                              : mutations.reactivate.mutateAsync(item.id),
                            item.status === 'ACTIVE' ? 'Indisponibilidade inativada.' : 'Indisponibilidade reativada.',
                          )
                        }
                      >
                        <RefreshCcw size={16} aria-hidden="true" />
                        {item.status === 'ACTIVE' ? 'Inativar' : 'Reativar'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {unavailabilities.length === 0 ? (
                <tr><td colSpan={4} className="table-muted">Nenhuma indisponibilidade cadastrada.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default MyUnavailabilityPage
