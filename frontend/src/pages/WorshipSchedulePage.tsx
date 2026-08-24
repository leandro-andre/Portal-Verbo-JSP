import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { CalendarClock, ChevronLeft, ChevronRight, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useCan } from '../hooks/useAuth'
import { useWorshipServiceMutations, useWorshipServices, useWorshipTemplates } from '../hooks/useWorship'
import type { WorshipService, WorshipServiceInput } from '../types/worship'

const monthNames = [
  'Janeiro',
  'Fevereiro',
  'Marco',
  'Abril',
  'Maio',
  'Junho',
  'Julho',
  'Agosto',
  'Setembro',
  'Outubro',
  'Novembro',
  'Dezembro',
]

const weekdayNames = ['Domingo', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado']

function todayMonth() {
  const today = new Date()
  return { year: today.getFullYear(), month: today.getMonth() + 1 }
}

function shiftMonth(year: number, month: number, delta: number) {
  const next = new Date(year, month - 1 + delta, 1)
  return { year: next.getFullYear(), month: next.getMonth() + 1 }
}

function parseLocalDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function formatDate(value: string) {
  const date = parseLocalDate(value)
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  return `${day}/${month}`
}

function formatTime(value: string) {
  return value.slice(0, 5)
}

function monthTitle(year: number, month: number) {
  return `${monthNames[month - 1]} ${year}`
}

function dateHeading(value: string) {
  const date = parseLocalDate(value)
  return `${weekdayNames[date.getDay()]} - ${formatDate(value)}`
}

function serviceStatusClass(service: WorshipService) {
  return service.status === 'CANCELLED' ? 'access-status-badge--rejected' : 'lesson-status-badge--scheduled'
}

function emptyServiceInput(year: number, month: number): WorshipServiceInput {
  return {
    name: '',
    date: `${year}-${String(month).padStart(2, '0')}-01`,
    time: '19:00',
    notes: '',
  }
}

function ServiceForm({
  initial,
  isPending,
  onCancel,
  onSubmit,
  submitLabel,
}: {
  initial: WorshipServiceInput
  isPending: boolean
  onCancel?: () => void
  onSubmit: (payload: WorshipServiceInput) => void
  submitLabel: string
}) {
  const [form, setForm] = useState<WorshipServiceInput>(initial)

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit({ ...form, notes: form.notes ?? '' })
  }

  return (
    <form className="department-inline-form" onSubmit={handleSubmit}>
      <label className="field-group">
        <span>Nome *</span>
        <input
          required
          value={form.name}
          onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
        />
      </label>
      <label className="field-group">
        <span>Data *</span>
        <input
          required
          type="date"
          value={form.date}
          onChange={(event) => setForm((current) => ({ ...current, date: event.target.value }))}
        />
      </label>
      <label className="field-group">
        <span>Horario *</span>
        <input
          required
          type="time"
          value={form.time}
          onChange={(event) => setForm((current) => ({ ...current, time: event.target.value }))}
        />
      </label>
      <label className="field-group field-group--wide">
        <span>Observacoes</span>
        <textarea
          className="textarea-control"
          value={form.notes ?? ''}
          onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
        />
      </label>
      <div className="form-actions">
        {onCancel ? (
          <button className="button button--secondary" type="button" onClick={onCancel}>
            Cancelar
          </button>
        ) : null}
        <button className="button button--primary" disabled={isPending} type="submit">
          {submitLabel}
        </button>
      </div>
    </form>
  )
}

function WorshipSchedulePage() {
  const initialMonth = todayMonth()
  const [year, setYear] = useState(initialMonth.year)
  const [month, setMonth] = useState(initialMonth.month)
  const [showExtraordinaryForm, setShowExtraordinaryForm] = useState(false)
  const [editingService, setEditingService] = useState<WorshipService | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const canManage = useCan('WORSHIP_SCHEDULE_MANAGE')
  const { data: services = [], isError, isLoading, refetch } = useWorshipServices(year, month)
  const { data: templates = [], isLoading: isLoadingTemplates } = useWorshipTemplates()
  const mutations = useWorshipServiceMutations(year, month)
  const hasActiveTemplates = templates.some((template) => template.active)

  const groupedServices = useMemo(() => {
    const groups = new Map<string, WorshipService[]>()
    services.forEach((service) => {
      const group = groups.get(service.date) ?? []
      group.push(service)
      groups.set(service.date, group)
    })
    return Array.from(groups.entries())
  }, [services])

  const goToMonth = (delta: number) => {
    const next = shiftMonth(year, month, delta)
    setYear(next.year)
    setMonth(next.month)
    setMessage(null)
    setError(null)
    setEditingService(null)
    setShowExtraordinaryForm(false)
  }

  const handleGenerate = async () => {
    if (!hasActiveTemplates) {
      setMessage(null)
      setError('Nao existem cultos padrao ativos para gerar.')
      return
    }

    const confirmed = window.confirm(
      `Gerar os cultos padrao de ${monthTitle(year, month)}?\n\nApenas cultos ainda inexistentes serao criados. Extraordinarios e alteracoes existentes serao preservados.`,
    )
    if (!confirmed) {
      return
    }
    setError(null)
    setMessage(null)
    try {
      const result = await mutations.generate.mutateAsync()
      setMessage(`Agenda gerada: ${result.created_count} criados, ${result.existing_count} ja existentes.`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Nao foi possivel gerar a agenda.')
    }
  }

  const handleCreateExtraordinary = async (payload: WorshipServiceInput) => {
    setError(null)
    setMessage(null)
    try {
      await mutations.createExtraordinary.mutateAsync(payload)
      setShowExtraordinaryForm(false)
      setMessage('Culto extraordinario criado.')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Nao foi possivel criar o culto extraordinario.')
    }
  }

  const handleUpdate = async (payload: WorshipServiceInput) => {
    if (!editingService) {
      return
    }
    setError(null)
    setMessage(null)
    try {
      await mutations.update.mutateAsync({ id: editingService.id, payload })
      setEditingService(null)
      setMessage('Culto atualizado.')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Nao foi possivel atualizar o culto.')
    }
  }

  const handleLifecycle = async (service: WorshipService) => {
    const isCancel = service.status === 'SCHEDULED'
    if (isCancel) {
      const confirmed = window.confirm(
        'Cancelar este culto?\n\nO culto continuara no historico e nao devera ser usado para novas escalas.',
      )
      if (!confirmed) {
        return
      }
    }
    setError(null)
    setMessage(null)
    try {
      if (isCancel) {
        await mutations.cancel.mutateAsync(service.id)
        setMessage('Culto cancelado.')
      } else {
        await mutations.reactivate.mutateAsync(service.id)
        setMessage('Culto reativado.')
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Nao foi possivel alterar o culto.')
    }
  }

  const selectedForEdit = editingService
    ? {
        name: editingService.name,
        date: editingService.date,
        time: formatTime(editingService.time),
        notes: editingService.notes,
      }
    : null

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Agenda de Cultos</h1>
          <p className="page-heading__description">Agenda mensal oficial da igreja.</p>
        </div>
        {canManage ? (
          <div className="profile-actions">
            <Link className="button button--secondary" to="/agenda-cultos/padroes">
              Cultos padrao
            </Link>
            <button className="button button--primary" type="button" onClick={() => setShowExtraordinaryForm(true)}>
              <Plus size={17} aria-hidden="true" />
              Culto extraordinario
            </button>
          </div>
        ) : null}
      </div>

      {message ? <div className="form-alert form-alert--success">{message}</div> : null}
      {error ? <div className="form-alert form-alert--error">{error}</div> : null}

      <div className="people-toolbar">
        <button className="button button--secondary" type="button" onClick={() => goToMonth(-1)}>
          <ChevronLeft size={17} aria-hidden="true" />
          {monthTitle(shiftMonth(year, month, -1).year, shiftMonth(year, month, -1).month)}
        </button>
        <strong className="people-summary">{monthTitle(year, month)}</strong>
        <button className="button button--secondary" type="button" onClick={() => goToMonth(1)}>
          {monthTitle(shiftMonth(year, month, 1).year, shiftMonth(year, month, 1).month)}
          <ChevronRight size={17} aria-hidden="true" />
        </button>
      </div>

      {canManage ? (
        <div className="profile-content">
          <section className="profile-section">
            <div className="section-heading-row">
              <div>
                <h2>Geracao mensal</h2>
                <p className="page-heading__description">A geracao cria somente cultos padrao ainda inexistentes.</p>
              </div>
              <button
                className="button button--primary"
                disabled={mutations.generate.isPending || isLoadingTemplates}
                type="button"
                onClick={() => void handleGenerate()}
              >
                Gerar cultos padrao deste mes
              </button>
            </div>
            {!hasActiveTemplates && !isLoadingTemplates ? (
              <div className="form-alert form-alert--error">
                Nao existem cultos padrao ativos para gerar. <Link to="/agenda-cultos/padroes">Configurar cultos padrao</Link>
              </div>
            ) : null}
          </section>
          {showExtraordinaryForm ? (
            <section className="profile-section">
              <h2>Culto extraordinario</h2>
              <ServiceForm
                initial={emptyServiceInput(year, month)}
                isPending={mutations.createExtraordinary.isPending}
                submitLabel="Criar culto extraordinario"
                onCancel={() => setShowExtraordinaryForm(false)}
                onSubmit={(payload) => void handleCreateExtraordinary(payload)}
              />
            </section>
          ) : null}
          {selectedForEdit ? (
            <section className="profile-section">
              <h2>Alteracao pontual</h2>
              <ServiceForm
                initial={selectedForEdit}
                isPending={mutations.update.isPending}
                submitLabel="Salvar culto"
                onCancel={() => setEditingService(null)}
                onSubmit={(payload) => void handleUpdate(payload)}
              />
            </section>
          ) : null}
        </div>
      ) : null}

      {isLoading ? (
        <div className="state-panel">
          <h2>Carregando agenda...</h2>
          <p>Aguarde enquanto buscamos os cultos do mes.</p>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <CalendarClock size={26} aria-hidden="true" />
          <h2>Nao foi possivel carregar a agenda.</h2>
          <p>Verifique sua permissao e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            Tentar novamente
          </button>
        </div>
      ) : groupedServices.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhum culto neste mes</h2>
          <p>
            {hasActiveTemplates
              ? 'Use a geracao mensal ou cadastre um culto extraordinario.'
              : 'Cadastre os cultos padrao da igreja e depois gere a agenda deste mes, ou cadastre um culto extraordinario.'}
          </p>
          {canManage && !hasActiveTemplates ? (
            <Link className="button button--primary" to="/agenda-cultos/padroes">
              Configurar cultos padrao
            </Link>
          ) : null}
        </div>
      ) : (
        <div className="profile-content">
          {groupedServices.map(([date, items]) => (
            <section className="profile-section" key={date}>
              <h2>{dateHeading(date)}</h2>
              <div className="table-shell table-shell--section">
                <table className="people-table">
                  <thead>
                    <tr>
                      <th>Horario</th>
                      <th>Culto</th>
                      <th>Tipo</th>
                      <th>Status</th>
                      <th>Origem</th>
                      <th className="people-table__actions-header">Acoes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((service) => (
                      <tr key={service.id}>
                        <td>{formatTime(service.time)}</td>
                        <td>
                          <strong>{service.name}</strong>
                          {service.notes ? <span className="table-muted">{service.notes}</span> : null}
                        </td>
                        <td>{service.kind === 'REGULAR' ? 'Regular' : 'Extraordinario'}</td>
                        <td>
                          <span className={`status-badge ${serviceStatusClass(service)}`}>
                            <span className="status-badge__dot" aria-hidden="true" />
                            {service.status === 'CANCELLED' ? 'Cancelado' : 'Agendado'}
                          </span>
                        </td>
                        <td>{service.template ? service.template.name : '-'}</td>
                        <td>
                          {canManage ? (
                            <div className="table-actions">
                              <button className="button button--secondary" type="button" onClick={() => setEditingService(service)}>
                                Editar
                              </button>
                              <button className="button button--secondary" type="button" onClick={() => void handleLifecycle(service)}>
                                {service.status === 'SCHEDULED' ? 'Cancelar' : 'Reativar'}
                              </button>
                            </div>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ))}
        </div>
      )}
    </section>
  )
}

export default WorshipSchedulePage
