import { Link } from 'react-router-dom'
import {
  AlertCircle,
  ArrowRight,
  Building2,
  CalendarCheck2,
  CalendarClock,
  CalendarDays,
  CalendarX2,
  ClipboardList,
  RefreshCcw,
  ShieldCheck,
  UserCog,
  UserRound,
  UsersRound,
} from 'lucide-react'
import { useCurrentUser } from '../hooks/useAuth'
import { useMyDashboard } from '../hooks/useDashboard'
import type { Capability } from '../types/auth'
import type { DashboardDepartment, DashboardResponse } from '../types/dashboard'

const weekdays = ['DOM', 'SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB']
const months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

const adminShortcuts: Array<{
  capability: Capability
  label: string
  to: string
  icon: typeof UsersRound
}> = [
  { capability: 'PEOPLE_VIEW', label: 'Pessoas', to: '/pessoas', icon: UsersRound },
  { capability: 'DEPARTMENT_VIEW', label: 'Departamentos', to: '/departamentos', icon: Building2 },
  { capability: 'WORSHIP_SCHEDULE_VIEW', label: 'Agenda de Cultos', to: '/agenda-cultos', icon: CalendarClock },
  { capability: 'SCHEDULE_VIEW', label: 'Escalas', to: '/escalas', icon: CalendarDays },
  { capability: 'DISCIPLESHIP_CLASS_VIEW', label: 'Discipulado', to: '/discipulado', icon: CalendarCheck2 },
  { capability: 'MEMBERSHIP_VIEW', label: 'Membresia', to: '/membresia', icon: ShieldCheck },
  { capability: 'ACCESS_REQUEST_VIEW', label: 'Solicitacoes', to: '/solicitacoes-acesso', icon: ClipboardList },
  { capability: 'USER_VIEW', label: 'Usuarios', to: '/usuarios', icon: UserCog },
]

function initials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'UP'
}

function parseLocalDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  const [year, month, day] = value.split('-')
  return year && month && day ? `${day}/${month}/${year}` : value
}

function scheduleDateLabel(value: string, time: string) {
  const date = parseLocalDate(value)
  return `${weekdays[date.getDay()]} - ${String(date.getDate()).padStart(2, '0')} ${months[date.getMonth()]} - ${time}`
}

function periodLabel(item: DashboardResponse['unavailability']['next']) {
  if (!item) return ''
  const date = item.start_date === item.end_date
    ? formatDate(item.start_date)
    : `${formatDate(item.start_date)} a ${formatDate(item.end_date)}`
  if (item.is_full_day) return `${date} - periodo integral`
  return `${date} - ${item.start_time ?? ''} a ${item.end_time ?? ''}`
}

function churchStatusLabel(status?: string) {
  if (status === 'MEMBER') return 'Membro'
  if (status === 'INACTIVE_MEMBER') return 'Membro inativo'
  if (status === 'VISITOR') return 'Visitante'
  return 'Jornada ainda nao iniciada'
}

function departmentSummary(departments: DashboardDepartment[]) {
  if (departments.length === 0) return 'Sem departamento ativo'
  const first = departments[0]
  const extra = departments.length > 1 ? ` +${departments.length - 1} departamentos` : ''
  return `${first.role.name} - ${first.department.name}${extra}`
}

function IdentityCard({
  name,
  photoUrl,
  churchStatus,
  memberSince,
  departments,
}: {
  name: string
  photoUrl: string | null
  churchStatus?: string
  memberSince?: string | null
  departments: DashboardDepartment[]
}) {
  return (
    <section className="home-identity">
      <div className="home-identity__avatar" aria-hidden="true">
        {photoUrl ? <img src={photoUrl} alt="" /> : <span>{initials(name)}</span>}
      </div>
      <div className="home-identity__main">
        <span className="status-badge status-badge--active">{churchStatusLabel(churchStatus)}</span>
        <h2>{name}</h2>
        <p>{departmentSummary(departments)}</p>
        {memberSince ? <p>Membro desde {formatDate(memberSince)}</p> : null}
      </div>
      <Link className="button button--secondary" to="/meu-perfil">
        Ver meu perfil
        <ArrowRight size={17} aria-hidden="true" />
      </Link>
    </section>
  )
}

function HomePage() {
  const { data: currentUser } = useCurrentUser()
  const { data, isError, isLoading, refetch } = useMyDashboard()
  const capabilities = currentUser?.user?.capabilities ?? []
  const hasCapability = (capability: Capability) => capabilities.includes(capability)
  const displayName = data?.profile?.name || data?.account.display_name || currentUser?.user?.display_name || currentUser?.user?.username || 'Usuario'
  const adminLinks = adminShortcuts.filter((shortcut) => hasCapability(shortcut.capability)).slice(0, 8)
  const showContextualSchedule = Boolean(
    data?.contextual_access.can_manage_schedules && !hasCapability('SCHEDULE_VIEW'),
  )

  if (isLoading) {
    return <section className="dashboard-page"><div className="state-panel"><h1>Carregando pagina inicial...</h1></div></section>
  }

  if (isError || !data) {
    return (
      <section className="dashboard-page">
        <div className="state-panel state-panel--error">
          <h1>Nao foi possivel carregar sua pagina inicial.</h1>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            <RefreshCcw size={17} aria-hidden="true" />
            Tentar novamente
          </button>
        </div>
      </section>
    )
  }

  return (
    <section className="dashboard-page">
      <div className="home-greeting">
        <div>
          <h1>Ola, {displayName}!</h1>
          <p>Que bom ter voce por aqui.</p>
        </div>
      </div>

      {data.person_linked && data.profile ? (
        <IdentityCard
          name={data.profile.name}
          photoUrl={data.profile.photo_url}
          churchStatus={data.profile.church_status}
          memberSince={data.profile.member_since}
          departments={data.journey.departments}
        />
      ) : (
        <section className="state-panel state-panel--compact">
          <h2>Seu cadastro pessoal ainda nao esta vinculado ao seu acesso.</h2>
          <p>Procure a Secretaria para concluir a configuracao.</p>
        </section>
      )}

      <div className="home-card-grid">
        <article className="home-card">
          <div className="home-card__heading">
            <CalendarCheck2 size={19} aria-hidden="true" />
            <h2>Minha proxima escala</h2>
          </div>
          {data.next_schedule ? (
            <>
              <strong>{scheduleDateLabel(data.next_schedule.date, data.next_schedule.time)}</strong>
              <p>{data.next_schedule.worship_service.name}</p>
              <span>{data.next_schedule.department.name}</span>
              <span>{data.next_schedule.role.name}</span>
              {data.next_schedule.warnings.length > 0 ? (
                <div className="home-warning">
                  <AlertCircle size={16} aria-hidden="true" />
                  {data.next_schedule.warnings[0].message}
                </div>
              ) : null}
            </>
          ) : (
            <p>Voce nao possui proximas escalas.</p>
          )}
          <Link className="button button--secondary" to="/minhas-escalas">Ver minhas escalas</Link>
        </article>

        <article className="home-card home-card--metrics">
          <div className="home-card__heading">
            <CalendarDays size={19} aria-hidden="true" />
            <h2>Minhas Escalas</h2>
          </div>
          <div className="home-metrics">
            <div><strong>{data.schedules_summary.upcoming_count}</strong><span>Proximas escalas</span></div>
            <div><strong>{data.schedules_summary.month_count}</strong><span>Escalas neste mes</span></div>
          </div>
          <Link className="button button--secondary" to="/minhas-escalas">Ver todas</Link>
        </article>

        <article className="home-card">
          <div className="home-card__heading">
            <CalendarX2 size={19} aria-hidden="true" />
            <h2>Indisponibilidades</h2>
          </div>
          {data.unavailability.next ? (
            <>
              <strong>Proxima indisponibilidade</strong>
              <p>{periodLabel(data.unavailability.next)}</p>
            </>
          ) : (
            <p>Voce nao possui indisponibilidades futuras.</p>
          )}
          <Link className="button button--secondary" to="/minhas-indisponibilidades">Informar indisponibilidade</Link>
        </article>
      </div>

      <div className="home-bottom-grid">
        <section className="home-panel">
          <h2>Acesso rapido</h2>
          <div className="home-shortcuts">
            <Link to="/minhas-escalas"><CalendarCheck2 size={18} aria-hidden="true" />Minhas Escalas</Link>
            <Link to="/minhas-indisponibilidades"><CalendarX2 size={18} aria-hidden="true" />Minhas Indisponibilidades</Link>
            <Link to="/meu-perfil"><UserRound size={18} aria-hidden="true" />Meu Perfil</Link>
            {adminLinks.map((shortcut) => {
              const Icon = shortcut.icon
              return <Link key={shortcut.to} to={shortcut.to}><Icon size={18} aria-hidden="true" />{shortcut.label}</Link>
            })}
            {showContextualSchedule ? (
              <Link to="/escalas"><CalendarDays size={18} aria-hidden="true" />Gerenciar escalas</Link>
            ) : null}
          </div>
        </section>

        <section className="home-panel">
          <h2>Minha jornada</h2>
          <dl className="profile-details">
            <div className="profile-detail"><dt>Situacao</dt><dd>{churchStatusLabel(data.journey.church_status)}</dd></div>
            <div className="profile-detail"><dt>Discipulado</dt><dd>{data.journey.discipleship_completed ? 'Concluido' : 'Nao concluido'}</dd></div>
          </dl>
          {data.journey.departments.length > 0 ? (
            <div className="home-journey-list">
              {data.journey.departments.slice(0, 3).map((membership) => (
                <div key={membership.id}>
                  <strong>{membership.department.name}</strong>
                  <span>{membership.role.name}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="table-muted">Nenhum departamento ativo vinculado ao seu cadastro.</p>
          )}
        </section>
      </div>
    </section>
  )
}

export default HomePage
