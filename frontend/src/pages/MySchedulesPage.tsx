import { useMemo, useState } from 'react'
import { CalendarDays, Clock, RefreshCcw } from 'lucide-react'
import { useMySchedules } from '../hooks/useScheduling'
import type { MyScheduleItem, MySchedulesScope } from '../types/scheduling'

const weekdays = ['Domingo', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado']
const months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

function currentMonthInput() {
  const today = new Date()
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`
}

function parseLocalDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function formatHeadingDate(value: string) {
  const date = parseLocalDate(value)
  return `${weekdays[date.getDay()]}, ${String(date.getDate()).padStart(2, '0')}/${String(date.getMonth() + 1).padStart(2, '0')}`
}

function compactDate(value: string) {
  const date = parseLocalDate(value)
  return { day: String(date.getDate()).padStart(2, '0'), month: months[date.getMonth()] }
}

function statusLabel(item: MyScheduleItem) {
  if (item.schedule_status === 'CANCELLED') return 'Escala cancelada'
  if (item.worship_service.status === 'CANCELLED') return 'Culto cancelado'
  return 'Historica'
}

function ScheduleCard({ item, scope }: { item: MyScheduleItem; scope: MySchedulesScope }) {
  const date = compactDate(item.worship_service.date)
  const showStatus = scope !== 'upcoming' || item.schedule_status === 'CANCELLED' || item.worship_service.status === 'CANCELLED'

  return (
    <article className="profile-section">
      <div className="section-heading-row">
        <div className="profile-header__identity">
          <div className="status-badge status-badge--active">
            <span>{date.day}</span>
            <span>{date.month}</span>
          </div>
          <div>
            <h2>{item.worship_service.name}</h2>
            <p className="page-heading__description">
              {formatHeadingDate(item.worship_service.date)} - {item.worship_service.time}
            </p>
          </div>
        </div>
        {item.worship_service.kind === 'EXTRAORDINARY' ? (
          <span className="status-badge lesson-status-badge--scheduled">
            <span className="status-badge__dot" aria-hidden="true" />
            Extraordinario
          </span>
        ) : null}
      </div>

      <div className="profile-details">
        <div className="profile-detail">
          <dt>Departamento</dt>
          <dd>{item.department.name}</dd>
        </div>
        <div className="profile-detail">
          <dt>Cargo</dt>
          <dd>{item.role.name}</dd>
        </div>
        {showStatus ? (
          <div className="profile-detail">
            <dt>Situacao</dt>
            <dd>{statusLabel(item)}</dd>
          </div>
        ) : null}
      </div>

      {item.warnings.length > 0 ? (
        <div className="form-alert form-alert--error">
          {item.warnings.map((warning) => <p key={warning.code}>{warning.message}</p>)}
        </div>
      ) : null}
    </article>
  )
}

function groupByDate(items: MyScheduleItem[]) {
  return items.reduce<Record<string, MyScheduleItem[]>>((groups, item) => {
    const key = item.worship_service.date
    groups[key] = groups[key] ? [...groups[key], item] : [item]
    return groups
  }, {})
}

function MySchedulesPage() {
  const [scope, setScope] = useState<MySchedulesScope>('upcoming')
  const [historyMonth, setHistoryMonth] = useState(currentMonthInput())
  const [year, month] = historyMonth.split('-').map(Number)
  const { data, isError, isLoading, refetch } = useMySchedules(
    scope,
    scope === 'history' ? year : undefined,
    scope === 'history' ? month : undefined,
  )
  const grouped = useMemo(() => groupByDate(data?.items ?? []), [data?.items])
  const groupedDates = Object.keys(grouped)
  const hasItems = groupedDates.length > 0

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Minhas Escalas</h1>
          <p className="page-heading__description">Veja quando voce vai servir, em qual culto, departamento e cargo.</p>
        </div>
      </div>

      <div className="people-toolbar">
        <button className={`button ${scope === 'upcoming' ? 'button--primary' : 'button--secondary'}`} type="button" onClick={() => setScope('upcoming')}>
          <CalendarDays size={17} aria-hidden="true" />
          Proximas
        </button>
        <button className={`button ${scope === 'history' ? 'button--primary' : 'button--secondary'}`} type="button" onClick={() => setScope('history')}>
          <Clock size={17} aria-hidden="true" />
          Historico
        </button>
        {scope === 'history' ? (
          <label className="status-filter">
            Mes
            <input type="month" value={historyMonth} onChange={(event) => setHistoryMonth(event.target.value)} />
          </label>
        ) : null}
      </div>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando suas escalas...</h2></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar suas escalas.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            <RefreshCcw size={17} aria-hidden="true" />
            Tentar novamente
          </button>
        </div>
      ) : data && !data.person_linked ? (
        <div className="state-panel">
          <h2>Seu acesso ainda nao esta vinculado a uma pessoa.</h2>
          <p>Procure a Secretaria para revisar seu cadastro.</p>
        </div>
      ) : !hasItems ? (
        <div className="state-panel">
          <h2>{scope === 'upcoming' ? 'Voce nao possui proximas escalas.' : 'Voce ainda nao possui escalas registradas neste periodo.'}</h2>
          <p>Se precisar informar alguma mudanca, procure sua lideranca.</p>
        </div>
      ) : (
        <div className="profile-content">
          {groupedDates.map((date) => (
            <section className="profile-section" key={date}>
              <h2>{formatHeadingDate(date)}</h2>
              <div className="profile-content">
                {grouped[date].map((item) => <ScheduleCard item={item} key={item.id} scope={scope} />)}
              </div>
            </section>
          ))}
        </div>
      )}
    </section>
  )
}

export default MySchedulesPage
