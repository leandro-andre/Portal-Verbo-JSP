import { useState, type ReactNode } from 'react'
import { ArrowLeft, Edit3, ExternalLink, ShieldCheck } from 'lucide-react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ApiHttpError } from '../api/people'
import PersonAvatar from '../components/people/PersonAvatar'
import PersonStatusBadge from '../components/people/PersonStatusBadge'
import AccessStatusBadge from '../components/users/AccessStatusBadge'
import { useCan } from '../hooks/useAuth'
import { usePerson360 } from '../hooks/usePeople'
import type { Person360, Person360DepartmentMembership, Person360PendingItem } from '../types/person'
import { formatBrazilianMobile } from '../utils/phone'

type Person360Tab = 'summary' | 'journey' | 'departments' | 'access'

const tabs: Array<{ id: Person360Tab; label: string }> = [
  { id: 'summary', label: 'Resumo' },
  { id: 'journey', label: 'Jornada' },
  { id: 'departments', label: 'Departamentos' },
  { id: 'access', label: 'Acesso' },
]

function formatDate(value: string | null) {
  if (!value) {
    return null
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    const [year, month, day] = value.split('-')
    return year && month && day ? `${day}/${month}/${year}` : value
  }
  return new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' }).format(date)
}

function formatDateTime(value: string | null) {
  if (!value) {
    return null
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return formatDate(value)
  }
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(date)
}

function DetailItem({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="profile-detail">
      <dt>{label}</dt>
      <dd>{value || '-'}</dd>
    </div>
  )
}

function StatusBadge({
  tone = 'neutral',
  children,
}: {
  tone?: 'success' | 'warning' | 'danger' | 'neutral'
  children: ReactNode
}) {
  return (
    <span className={`status-badge person360-badge person360-badge--${tone}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {children}
    </span>
  )
}

function accessBadge(profile: Person360) {
  if (!profile.access.has_user || profile.access.status === 'NO_ACCESS') {
    return <StatusBadge>Sem acesso ao Portal</StatusBadge>
  }
  return <AccessStatusBadge status={profile.access.status} />
}

function PendingItem({ item }: { item: Person360PendingItem }) {
  return (
    <li className={`person360-pending-item person360-pending-item--${item.severity}`}>
      <span>{item.label}</span>
    </li>
  )
}

function Section({
  children,
  title,
}: {
  children: ReactNode
  title: string
}) {
  return (
    <section className="profile-section person360-section">
      <h2>{title}</h2>
      {children}
    </section>
  )
}

function SummaryTab({ profile }: { profile: Person360 }) {
  const departmentPreview = profile.departments.active.slice(0, 4)

  return (
    <div className="person360-grid">
      <Section title="Situacao na igreja">
        <dl className="profile-details">
          <DetailItem label="Status" value={profile.church.label} />
          <DetailItem label="Jornada iniciada em" value={formatDate(profile.church.started_at) || 'Jornada nao iniciada'} />
          <DetailItem label="Membro desde" value={formatDate(profile.membership.member_since) || 'Sem membresia'} />
        </dl>
      </Section>

      <Section title="Discipulado">
        <dl className="profile-details">
          <DetailItem label="Status" value={profile.discipleship.label} />
          <DetailItem label="Turma" value={profile.discipleship.class?.name || 'Nenhum discipulado registrado'} />
          <DetailItem label="Conclusao" value={formatDate(profile.discipleship.completed_at) || 'Nao concluido'} />
        </dl>
      </Section>

      <Section title="Acesso ao Portal">
        <dl className="profile-details">
          <DetailItem label="Status" value={profile.access.label} />
          <DetailItem label="Usuario" value={profile.access.username || 'Esta pessoa ainda nao possui acesso ao Portal.'} />
        </dl>
      </Section>

      <Section title="Departamentos">
        <p className="page-heading__description">
          {profile.summary.active_departments_count === 1
            ? '1 departamento ativo'
            : `${profile.summary.active_departments_count} departamentos ativos`}
        </p>
        {departmentPreview.length ? (
          <ul className="person360-compact-list">
            {departmentPreview.map((membership) => (
              <li key={membership.id}>
                <strong>{membership.department.name}</strong>
                <span>{membership.role.name}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="page-heading__description">Esta pessoa ainda nao participa de departamentos.</p>
        )}
      </Section>

      <section className="profile-section person360-section person360-section--wide">
        <h2>Pendencias</h2>
        {profile.pending_items.length ? (
          <ul className="person360-pending-list">
            {profile.pending_items.map((item) => (
              <PendingItem item={item} key={item.code + item.label} />
            ))}
          </ul>
        ) : (
          <p className="page-heading__description">Nenhuma pendencia identificada.</p>
        )}
      </section>
    </div>
  )
}

function JourneyTab({ profile }: { profile: Person360 }) {
  return (
    <div className="person360-grid">
      <Section title="Situacao atual">
        <dl className="profile-details">
          <DetailItem label="ChurchStatus" value={profile.church.status} />
          <DetailItem label="Label" value={profile.church.label} />
          <DetailItem label="Inicio da jornada" value={formatDate(profile.church.started_at) || 'Jornada nao iniciada'} />
        </dl>
      </Section>

      <Section title="Discipulado">
        <dl className="profile-details">
          <DetailItem label="Status" value={profile.discipleship.label} />
          <DetailItem label="Turma" value={profile.discipleship.class?.name || 'Nenhum discipulado registrado'} />
          <DetailItem label="Matricula" value={formatDate(profile.discipleship.enrolled_at) || 'Nao iniciada'} />
          <DetailItem label="Conclusao" value={formatDate(profile.discipleship.completed_at) || 'Nao concluido'} />
        </dl>
      </Section>

      <Section title="Membresia">
        <dl className="profile-details">
          <DetailItem label="Status" value={profile.membership.label} />
          <DetailItem label="Membro desde" value={formatDate(profile.membership.member_since) || 'Sem membresia'} />
          <DetailItem label="Aprovado em" value={formatDateTime(profile.membership.approved_at) || '-'} />
          <DetailItem label="Aprovado por" value={profile.membership.approved_by?.display_name || '-'} />
          <DetailItem
            label="Elegibilidade"
            value={profile.discipleship.membership_can_create ? 'Elegivel para membresia' : 'Nao elegivel para nova membresia'}
          />
        </dl>
      </Section>
    </div>
  )
}

function DepartmentTable({
  items,
  title,
}: {
  items: Person360DepartmentMembership[]
  title: string
}) {
  return (
    <Section title={title}>
      {items.length ? (
        <div className="table-shell table-shell--section">
          <table className="people-table person360-department-table">
            <thead>
              <tr>
                <th>Departamento</th>
                <th>Funcao</th>
                <th>Status</th>
                <th>Elegibilidade</th>
                <th>Entrada</th>
              </tr>
            </thead>
            <tbody>
              {items.map((membership) => (
                <tr key={membership.id}>
                  <td>
                    <Link className="person-name-link" to={`/departamentos/${membership.department.id}`}>
                      {membership.department.name}
                    </Link>
                  </td>
                  <td>{membership.role.name}</td>
                  <td>{membership.status === 'ACTIVE' ? 'Ativo' : 'Inativo'}</td>
                  <td>
                    {membership.operationally_eligible ? (
                      <StatusBadge tone="success">Elegivel</StatusBadge>
                    ) : (
                      <div className="person360-eligibility">
                        <StatusBadge tone="warning">Inelegivel</StatusBadge>
                        <span>{membership.eligibility.reasons.map((reason) => reason.message).join(' ')}</span>
                      </div>
                    )}
                  </td>
                  <td>{formatDate(membership.joined_at) || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="page-heading__description">
          {title === 'Ativos'
            ? 'Esta pessoa ainda nao participa de departamentos.'
            : 'Nenhum vinculo historico ou inativo registrado.'}
        </p>
      )}
    </Section>
  )
}

function DepartmentsTab({ profile }: { profile: Person360 }) {
  return (
    <>
      <DepartmentTable items={profile.departments.active} title="Ativos" />
      <DepartmentTable items={profile.departments.inactive} title="Historico/Inativos" />
    </>
  )
}

function AccessTab({ profile, canViewUsers }: { profile: Person360; canViewUsers: boolean }) {
  return (
    <Section title="Acesso ao Portal">
      {profile.access.has_user ? (
        <div className="portal-access-summary">
          <dl className="profile-details">
            <DetailItem label="Possui usuario?" value="Sim" />
            <DetailItem label="Username" value={profile.access.username} />
            <DetailItem label="E-mail da conta" value={profile.access.email || '-'} />
            <DetailItem label="Status" value={accessBadge(profile)} />
            <DetailItem label="Conta ativa?" value={profile.access.is_active ? 'Sim' : 'Nao'} />
            <DetailItem label="Ultimo login" value={formatDateTime(profile.access.last_login) || 'Sem login registrado'} />
            <DetailItem label="Criada em" value={formatDateTime(profile.access.date_joined) || '-'} />
          </dl>
          {canViewUsers && profile.actions.manage_access_url ? (
            <Link className="button button--secondary" to={profile.actions.manage_access_url}>
              <ShieldCheck size={17} aria-hidden="true" />
              Gerenciar acesso
            </Link>
          ) : null}
        </div>
      ) : (
        <p className="page-heading__description">Esta pessoa ainda nao possui acesso ao Portal.</p>
      )}
    </Section>
  )
}

function Person360Header({
  canChangePeople,
  profile,
  successMessage,
}: {
  canChangePeople: boolean
  profile: Person360
  successMessage: string | null
}) {
  const person = profile.person
  const birthDate = formatDate(person.birth_date)
  const ageLabel = person.age === null ? null : `${person.age} anos`
  const hasDifferentFullName = person.full_name !== person.display_name

  return (
    <>
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/pessoas">Pessoas</Link>
        <span aria-hidden="true">/</span>
        <strong>{person.display_name}</strong>
      </nav>

      <header className="profile-header person360-header">
        {person.photo_url ? (
          <img className="person360-photo" src={person.photo_url} alt="" />
        ) : (
          <PersonAvatar name={person.display_name} />
        )}
        <div className="profile-header__identity person360-header__identity">
          <h1>{person.display_name}</h1>
          {hasDifferentFullName ? <p>{person.full_name}</p> : null}
          <div className="person360-badges" aria-label="Status da pessoa">
            <PersonStatusBadge status={person.status} />
            <StatusBadge tone={profile.church.status === 'MEMBER' ? 'success' : 'neutral'}>
              {profile.church.label}
            </StatusBadge>
            <StatusBadge tone={profile.discipleship.status === 'COMPLETED' ? 'success' : 'neutral'}>
              {profile.discipleship.label}
            </StatusBadge>
            {accessBadge(profile)}
            {profile.summary.active_departments_count ? (
              <StatusBadge>{profile.summary.active_departments_count} departamentos</StatusBadge>
            ) : null}
          </div>
          <div className="person360-contact-line">
            <span>{[ageLabel, birthDate].filter(Boolean).join(' - ') || 'Data de nascimento nao informada'}</span>
            <span>{person.phone ? formatBrazilianMobile(person.phone) : 'Celular/WhatsApp nao informado'}</span>
            <span>{person.email || profile.access.email || 'E-mail nao informado'}</span>
          </div>
        </div>
        {canChangePeople ? (
          <div className="profile-actions">
            <Link className="button button--primary" to={profile.actions.edit_person_url}>
              <Edit3 size={17} aria-hidden="true" />
              Editar pessoa
            </Link>
          </div>
        ) : null}
      </header>

      {successMessage ? (
        <div className="form-alert form-alert--success" role="status">
          {successMessage}
        </div>
      ) : null}
    </>
  )
}

function PersonProfilePage() {
  const { id } = useParams()
  const location = useLocation()
  const personId = Number(id)
  const isValidId = Number.isInteger(personId) && personId > 0
  const { data: profile, error, isError, isLoading, refetch } = usePerson360(personId)
  const canChangePeople = useCan('PEOPLE_CHANGE')
  const canViewUsers = useCan('USER_VIEW')
  const [activeTab, setActiveTab] = useState<Person360Tab>('summary')
  const navigationState = location.state as { successMessage?: string } | null
  const isNotFound = !isValidId || (error instanceof ApiHttpError && error.status === 404)

  const renderTab = () => {
    if (!profile) {
      return null
    }
    if (activeTab === 'journey') {
      return <JourneyTab profile={profile} />
    }
    if (activeTab === 'departments') {
      return <DepartmentsTab profile={profile} />
    }
    if (activeTab === 'access') {
      return <AccessTab canViewUsers={canViewUsers} profile={profile} />
    }
    return <SummaryTab profile={profile} />
  }

  return (
    <section className="person-profile-page">
      {isLoading && isValidId ? (
        <div className="state-panel">
          <h1>Carregando ficha 360...</h1>
          <p>Aguarde enquanto reunimos os dados da pessoa.</p>
        </div>
      ) : isNotFound ? (
        <div className="state-panel">
          <h1>Pessoa nao encontrada</h1>
          <p>Nao encontramos a pessoa solicitada.</p>
          <Link className="button button--secondary" to="/pessoas">
            <ArrowLeft size={17} aria-hidden="true" />
            Voltar para Pessoas
          </Link>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h1>Nao foi possivel carregar a ficha 360.</h1>
          <p>Verifique sua permissao e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            Tentar novamente
          </button>
        </div>
      ) : profile ? (
        <>
          <Person360Header
            canChangePeople={canChangePeople}
            profile={profile}
            successMessage={navigationState?.successMessage ?? null}
          />

          <div className="person360-tabs" role="tablist" aria-label="Secoes da ficha 360">
            {tabs.map((tab) => (
              <button
                className={`person360-tab${activeTab === tab.id ? ' person360-tab--active' : ''}`}
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="profile-content person360-content">{renderTab()}</div>

          <div className="person360-footer-actions">
            <Link className="button button--secondary" to="/pessoas">
              <ArrowLeft size={17} aria-hidden="true" />
              Voltar
            </Link>
            {profile.actions.manage_access_url && canViewUsers ? (
              <Link className="button button--secondary" to={profile.actions.manage_access_url}>
                <ExternalLink size={17} aria-hidden="true" />
                Abrir acesso
              </Link>
            ) : null}
          </div>
        </>
      ) : null}
    </section>
  )
}

export default PersonProfilePage
