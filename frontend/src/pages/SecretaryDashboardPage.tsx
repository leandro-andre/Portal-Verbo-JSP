import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertCircle,
  ArrowRight,
  ClipboardList,
  RefreshCcw,
  ShieldCheck,
  UserCheck,
  UserRoundX,
  UsersRound,
} from 'lucide-react'
import { SecretaryDashboardError } from '../api/secretaryDashboard'
import { useSecretaryDashboard } from '../hooks/useSecretaryDashboard'
import type {
  SecretaryAccessRequestItem,
  SecretaryActivationItem,
  SecretaryDashboardPerson,
  SecretaryDepartmentEligibilityItem,
  SecretaryIncompleteProfileItem,
  SecretaryInactiveMembershipItem,
  SecretaryMembershipApprovalItem,
  SecretaryWithoutPortalAccessItem,
} from '../types/secretaryDashboard'

function formatDate(value: string | null) {
  if (!value) return '-'
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [year, month, day] = value.split('-')
    return `${day}/${month}/${year}`
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    const [year, month, day] = value.split('-')
    return year && month && day ? `${day}/${month}/${year}` : value
  }
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(date)
}

function personName(person: SecretaryDashboardPerson | null, fallback = 'Pessoa nao vinculada') {
  return person?.display_name || fallback
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="secretary-metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
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
    <section className="secretary-section">
      <h2>{title}</h2>
      {children}
    </section>
  )
}

function EmptySection({ message }: { message: string }) {
  return <p className="secretary-empty">{message}</p>
}

function CardBlock({
  actionLabel = 'Abrir',
  children,
  count,
  icon,
  title,
  to,
}: {
  actionLabel?: string
  children: ReactNode
  count: number
  icon: React.ReactNode
  title: string
  to: string
}) {
  return (
    <article className="secretary-block">
      <div className="secretary-block__header">
        <div className="secretary-block__title">
          {icon}
          <h3>{title}</h3>
        </div>
        <strong>{count}</strong>
      </div>
      {children}
      <Link className="button button--secondary secretary-block__action" to={to}>
        {actionLabel}
        <ArrowRight size={16} aria-hidden="true" />
      </Link>
    </article>
  )
}

function AccessRequestItems({ items }: { items: SecretaryAccessRequestItem[] }) {
  if (!items.length) return <EmptySection message="Nenhuma solicitacao aguardando analise." />
  return (
    <ul className="secretary-item-list">
      {items.map((item) => (
        <li key={item.id}>
          <div>
            <strong>{item.full_name}</strong>
            <span>{item.email}</span>
            <small>Solicitado em {formatDate(item.created_at)}</small>
          </div>
          <Link to={item.review_url}>Analisar</Link>
        </li>
      ))}
    </ul>
  )
}

function MembershipItems({ items }: { items: SecretaryMembershipApprovalItem[] }) {
  if (!items.length) return <EmptySection message="Nenhuma membresia aguardando decisao." />
  return (
    <ul className="secretary-item-list">
      {items.map((item) => (
        <li key={item.person.id}>
          <div>
            <strong>{item.person.display_name}</strong>
            <span>{item.detail}</span>
            <small>Concluido em {formatDate(item.completed_at)}</small>
          </div>
          <Link to={item.resolution_url}>Ver pessoa</Link>
        </li>
      ))}
    </ul>
  )
}

function ActivationItems({ items }: { items: SecretaryActivationItem[] }) {
  if (!items.length) return <EmptySection message="Nenhuma conta aguardando ativacao." />
  return (
    <ul className="secretary-item-list">
      {items.map((item) => (
        <li key={item.user.id}>
          <div>
            <strong>{personName(item.person, item.user.username)}</strong>
            <span>{item.user.email || item.user.username}</span>
            <small>Conta criada em {formatDate(item.date_joined)}</small>
          </div>
          <Link to={item.resolution_url}>Ver usuario</Link>
        </li>
      ))}
    </ul>
  )
}

function IncompleteProfileItems({ items }: { items: SecretaryIncompleteProfileItem[] }) {
  if (!items.length) return <EmptySection message="Nenhum cadastro incompleto encontrado." />
  return (
    <ul className="secretary-item-list">
      {items.map((item) => (
        <li key={item.person.id}>
          <div>
            <strong>{item.person.display_name}</strong>
            <span>
              {item.missing.map((missing) => missing === 'MISSING_EMAIL' ? 'Sem e-mail' : 'Sem WhatsApp').join(' - ')}
            </span>
          </div>
          <Link to={item.resolution_url}>Editar</Link>
        </li>
      ))}
    </ul>
  )
}

function DepartmentEligibilityItems({ items }: { items: SecretaryDepartmentEligibilityItem[] }) {
  if (!items.length) return <EmptySection message="Nenhum vinculo departamental inelegivel encontrado." />
  return (
    <ul className="secretary-item-list">
      {items.map((item) => (
        <li key={item.id}>
          <div>
            <strong>{item.person.display_name}</strong>
            <span>{item.department.name} - {item.role.name}</span>
            <small>{item.reasons.map((reason) => reason.message).join(' ')}</small>
          </div>
          <Link to={item.resolution_url}>Ver pessoa</Link>
        </li>
      ))}
    </ul>
  )
}

function WithoutPortalAccessItems({ items }: { items: SecretaryWithoutPortalAccessItem[] }) {
  if (!items.length) return <EmptySection message="Todas as pessoas listadas aqui possuem usuario vinculado." />
  return (
    <ul className="secretary-item-list">
      {items.map((item) => (
        <li key={item.person.id}>
          <div>
            <strong>{item.person.display_name}</strong>
            <span>{item.person.email || 'E-mail nao informado'}</span>
          </div>
          <Link to={item.resolution_url}>Ver pessoa</Link>
        </li>
      ))}
    </ul>
  )
}

function InactiveMembershipItems({ items }: { items: SecretaryInactiveMembershipItem[] }) {
  if (!items.length) return <EmptySection message="Nenhum membro atualmente inativo." />
  return (
    <ul className="secretary-item-list">
      {items.map((item) => (
        <li key={item.person.id}>
          <div>
            <strong>{item.person.display_name}</strong>
            <span>Membro desde {formatDate(item.member_since)}</span>
          </div>
          <Link to={item.resolution_url}>Ver pessoa</Link>
        </li>
      ))}
    </ul>
  )
}

function SecretaryDashboardPage() {
  const { data, error, isError, isLoading, refetch } = useSecretaryDashboard()
  const isForbidden = error instanceof SecretaryDashboardError && error.status === 403

  if (isLoading) {
    return <section className="secretary-page"><div className="state-panel"><h1>Carregando Central da Secretaria...</h1></div></section>
  }

  if (isError || !data) {
    return (
      <section className="secretary-page">
        <div className="state-panel state-panel--error">
          <h1>{isForbidden ? 'Acesso nao autorizado.' : 'Nao foi possivel carregar a Central da Secretaria.'}</h1>
          <p>{isForbidden ? 'Sua sessao atual nao possui permissao administrativa para esta central.' : 'Verifique a conexao e tente novamente.'}</p>
          {!isForbidden ? (
            <button className="button button--secondary" type="button" onClick={() => void refetch()}>
              <RefreshCcw size={17} aria-hidden="true" />
              Tentar novamente
            </button>
          ) : null}
        </div>
      </section>
    )
  }

  const hasNoWork =
    data.summary.action_required === 0 &&
    data.summary.pending_activation === 0 &&
    data.summary.incomplete_profiles === 0 &&
    data.pending.department_eligibility.count === 0

  return (
    <section className="secretary-page">
      <div className="page-heading">
        <div>
          <h1>Central da Secretaria</h1>
          <p className="page-heading__description">Pendencias administrativas e visao operacional para resolver agora.</p>
        </div>
      </div>

      <div className="secretary-metrics">
        <MetricCard label="Precisam de acao" value={data.summary.action_required} />
        <MetricCard label="Aguardando ativacao" value={data.summary.pending_activation} />
        <MetricCard label="Cadastros incompletos" value={data.summary.incomplete_profiles} />
        <MetricCard label="Pessoas cadastradas" value={data.summary.people_total} />
      </div>

      {hasNoWork ? (
        <section className="state-panel state-panel--compact">
          <h2>Nenhuma pendencia administrativa no momento.</h2>
          <p>A Central sera atualizada quando houver novos itens derivados dos cadastros, acessos e departamentos.</p>
        </section>
      ) : null}

      <Section title="Precisam de acao">
        <div className="secretary-block-grid">
          <CardBlock
            count={data.action_required.access_requests.count}
            icon={<ClipboardList size={19} aria-hidden="true" />}
            title="Solicitacoes de acesso"
            to={data.action_required.access_requests.list_url}
            actionLabel="Ver solicitacoes"
          >
            <AccessRequestItems items={data.action_required.access_requests.items} />
          </CardBlock>
          <CardBlock
            count={data.action_required.membership_approvals.count}
            icon={<ShieldCheck size={19} aria-hidden="true" />}
            title="Membresias aguardando analise"
            to={data.action_required.membership_approvals.list_url}
            actionLabel="Ver membresia"
          >
            <MembershipItems items={data.action_required.membership_approvals.items} />
          </CardBlock>
        </div>
      </Section>

      <Section title="Pendencias">
        <div className="secretary-block-grid">
          <CardBlock count={data.pending.activation.count} icon={<UserCheck size={19} aria-hidden="true" />} title="Contas aguardando ativacao" to={data.pending.activation.list_url} actionLabel="Ver usuarios">
            <ActivationItems items={data.pending.activation.items} />
          </CardBlock>
          <CardBlock count={data.pending.incomplete_profiles.count} icon={<AlertCircle size={19} aria-hidden="true" />} title="Cadastros incompletos" to={data.pending.incomplete_profiles.list_url} actionLabel="Ver pessoas">
            <p className="secretary-breakdown">
              {data.pending.incomplete_profiles.missing_email_count} sem e-mail - {data.pending.incomplete_profiles.missing_whatsapp_count} sem WhatsApp
            </p>
            <IncompleteProfileItems items={data.pending.incomplete_profiles.items} />
          </CardBlock>
          <CardBlock count={data.pending.department_eligibility.count} icon={<UsersRound size={19} aria-hidden="true" />} title="Vinculos departamentais" to={data.pending.department_eligibility.list_url} actionLabel="Ver departamentos">
            <DepartmentEligibilityItems items={data.pending.department_eligibility.items} />
          </CardBlock>
        </div>
      </Section>

      <Section title="Acompanhamento">
        <div className="secretary-block-grid">
          <CardBlock count={data.monitoring.without_portal_access.count} icon={<UserRoundX size={19} aria-hidden="true" />} title="Pessoas sem acesso ao Portal" to={data.monitoring.without_portal_access.list_url} actionLabel="Ver pessoas">
            <WithoutPortalAccessItems items={data.monitoring.without_portal_access.items} />
          </CardBlock>
          <CardBlock count={data.monitoring.inactive_memberships.count} icon={<ShieldCheck size={19} aria-hidden="true" />} title="Membros atualmente inativos" to={data.monitoring.inactive_memberships.list_url} actionLabel="Ver membresia">
            <InactiveMembershipItems items={data.monitoring.inactive_memberships.items} />
          </CardBlock>
        </div>
      </Section>

      <Section title="Visao geral">
        <div className="secretary-overview">
          <MetricCard label="Visitantes" value={data.overview.visitors} />
          <MetricCard label="Membros ativos" value={data.overview.active_members} />
          <MetricCard label="Membros inativos" value={data.overview.inactive_members} />
          <MetricCard label="Contas ativas" value={data.overview.active_portal_accounts} />
          <MetricCard label="Aguardando ativacao" value={data.overview.pending_activation_accounts} />
        </div>
      </Section>
    </section>
  )
}

export default SecretaryDashboardPage
