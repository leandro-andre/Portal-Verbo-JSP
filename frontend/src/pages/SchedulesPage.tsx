import { useEffect, useState } from 'react'
import { CalendarDays, ChevronLeft, ChevronRight, Plus } from 'lucide-react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useCan } from '../hooks/useAuth'
import { useCreateSchedule, useMonthlySchedule, useSchedulingDepartments } from '../hooks/useScheduling'
import type { MonthlyScheduleItem, ScheduleStatus } from '../types/scheduling'

const months = ['Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
const weekdays = ['Domingo', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado']

function initialMonth() {
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
  return `${weekdays[date.getDay()]}, ${String(date.getDate()).padStart(2, '0')}/${String(date.getMonth() + 1).padStart(2, '0')}/${date.getFullYear()}`
}

function formatTime(value: string) {
  return value.slice(0, 5)
}

function monthTitle(year: number, month: number) {
  return `${months[month - 1]} ${year}`
}

function statusLabel(status: ScheduleStatus | null) {
  if (status === 'DRAFT') return 'Rascunho'
  if (status === 'PUBLISHED') return 'Publicada'
  if (status === 'CANCELLED') return 'Cancelada'
  return 'Sem escala'
}

function statusClass(status: ScheduleStatus | null) {
  if (status === 'PUBLISHED') return 'status-badge--active'
  if (status === 'CANCELLED') return 'access-status-badge--rejected'
  if (status === 'DRAFT') return 'lesson-status-badge--scheduled'
  return 'status-badge--inactive'
}

function isPastService(date: string) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return parseLocalDate(date) < today
}

function ScheduleCard({
  canManage,
  contextQuery,
  isPending,
  item,
  onCreate,
}: {
  canManage: boolean
  contextQuery: string
  isPending: boolean
  item: MonthlyScheduleItem
  onCreate: (worshipServiceId: number) => void
}) {
  const { worship_service: service, schedule } = item
  const disabled = service.status === 'CANCELLED' || isPastService(service.date)

  return (
    <section className="profile-section">
      <div className="section-heading-row">
        <div>
          <h2>{formatDate(service.date)}</h2>
          <p className="page-heading__description">{formatTime(service.time)} - {service.name}</p>
        </div>
        <div className="table-actions">
          <span className={`status-badge ${service.status === 'CANCELLED' ? 'access-status-badge--rejected' : 'status-badge--active'}`}>
            <span className="status-badge__dot" aria-hidden="true" />
            Culto {service.status === 'CANCELLED' ? 'cancelado' : 'agendado'}
          </span>
          <span className={`status-badge ${statusClass(schedule?.status ?? null)}`}>
            <span className="status-badge__dot" aria-hidden="true" />
            {statusLabel(schedule?.status ?? null)}
          </span>
          <span className="status-badge status-badge--inactive">{service.kind === 'EXTRAORDINARY' ? 'Extraordinario' : 'Regular'}</span>
        </div>
      </div>

      {schedule ? (
        <div className="section-heading-row">
          <p className="page-heading__description">{schedule.assignments_count} pessoas escaladas</p>
          <Link className="button button--primary" to={`/escalas/${schedule.id}?${contextQuery}`}>
            {schedule.permissions.can_manage ? 'Editar escala' : 'Ver escala'}
          </Link>
        </div>
      ) : (
        <div className="section-heading-row">
          <p className="page-heading__description">
            {disabled ? 'Nao e possivel montar escala para culto cancelado ou passado.' : 'Nenhuma escala criada para este departamento.'}
          </p>
          {canManage && !disabled ? (
            <button className="button button--primary" disabled={isPending} type="button" onClick={() => onCreate(service.id)}>
              <Plus size={17} aria-hidden="true" />
              Montar escala
            </button>
          ) : null}
        </div>
      )}
    </section>
  )
}

function SchedulesPage() {
  const initial = initialMonth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [year, setYear] = useState(Number(searchParams.get('year')) || initial.year)
  const [month, setMonth] = useState(Number(searchParams.get('month')) || initial.month)
  const [departmentId, setDepartmentId] = useState(searchParams.get('department') ?? '')
  const [onlyPending, setOnlyPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const canOpenWorshipSchedule = useCan('WORSHIP_SCHEDULE_VIEW')
  const { data: departments = [], isLoading: departmentsLoading } = useSchedulingDepartments()
  const selectedDepartmentId = departmentId || (departments[0]?.id ? String(departments[0].id) : '')
  const { data: monthly, isError, isLoading, refetch } = useMonthlySchedule(year, month, selectedDepartmentId)
  const createMutation = useCreateSchedule(year, month, selectedDepartmentId, '')
  const contextQuery = new URLSearchParams({ year: String(year), month: String(month), department: selectedDepartmentId }).toString()

  useEffect(() => {
    const params = new URLSearchParams({ year: String(year), month: String(month) })
    if (selectedDepartmentId) {
      params.set('department', selectedDepartmentId)
    }
    setSearchParams(params, { replace: true })
  }, [year, month, selectedDepartmentId, setSearchParams])

  const goToMonth = (delta: number) => {
    const next = shiftMonth(year, month, delta)
    setYear(next.year)
    setMonth(next.month)
    setError(null)
  }

  const handleCreate = async (worshipServiceId: number) => {
    setError(null)
    try {
      const schedule = await createMutation.mutateAsync({
        department_id: Number(selectedDepartmentId),
        worship_service_id: worshipServiceId,
      })
      navigate(`/escalas/${schedule.id}?${contextQuery}`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Nao foi possivel montar a escala.')
    }
  }

  const items = (monthly?.items ?? []).filter((item) => {
    if (!onlyPending) return true
    return item.worship_service.status !== 'CANCELLED' && item.schedule?.status !== 'PUBLISHED'
  })
  const ready = monthly ? `${monthly.summary.published} / ${monthly.summary.operational_services}` : '0 / 0'

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Escalas</h1>
          <p className="page-heading__description">Montagem mensal por culto, departamento, cargo e pessoa.</p>
        </div>
      </div>

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

      <div className="people-toolbar">
        <label className="status-filter">
          Departamento
          <select value={selectedDepartmentId} onChange={(event) => setDepartmentId(event.target.value)} disabled={departmentsLoading}>
            {departments.map((department) => <option key={department.id} value={department.id}>{department.nome}</option>)}
          </select>
        </label>
        <label className="checkbox-field">
          <input type="checkbox" checked={onlyPending} onChange={(event) => setOnlyPending(event.target.checked)} />
          <span>Somente pendentes</span>
        </label>
      </div>

      {monthly ? (
        <div className="people-toolbar">
          <span className="people-summary">{monthly.summary.services} cultos</span>
          <span className="people-summary">Prontas {ready}</span>
          <span className="people-summary">{monthly.summary.published} publicadas</span>
          <span className="people-summary">{monthly.summary.draft} rascunhos</span>
          <span className="people-summary">{monthly.summary.without_schedule} sem escala</span>
        </div>
      ) : null}

      {!selectedDepartmentId ? (
        <div className="state-panel">
          <h2>Nenhum departamento disponivel</h2>
          <p>Sua sessao nao possui departamentos disponiveis para montagem de escalas.</p>
        </div>
      ) : isLoading ? (
        <div className="state-panel"><h2>Carregando mes...</h2><p>Aguarde enquanto buscamos os cultos e escalas.</p></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <CalendarDays size={26} aria-hidden="true" />
          <h2>Nao foi possivel carregar o mes.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : items.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhum culto cadastrado neste mes.</h2>
          <p>A Secretaria precisa cadastrar ou gerar os cultos na Agenda de Cultos antes da montagem das escalas.</p>
          {canOpenWorshipSchedule ? <Link className="button button--primary" to="/agenda-cultos">Ir para Agenda de Cultos</Link> : null}
        </div>
      ) : (
        <div className="profile-content">
          {items.map((item) => (
            <ScheduleCard
              canManage={Boolean(monthly?.permissions.can_manage)}
              contextQuery={contextQuery}
              isPending={createMutation.isPending}
              item={item}
              key={item.worship_service.id}
              onCreate={(worshipServiceId) => void handleCreate(worshipServiceId)}
            />
          ))}
        </div>
      )}
    </section>
  )
}

export default SchedulesPage
