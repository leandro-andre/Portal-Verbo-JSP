import { useState } from 'react'
import { ArrowLeft, Edit3, Play, RefreshCcw } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ApiHttpError } from '../api/people'
import PersonAvatar from '../components/people/PersonAvatar'
import PersonStatusBadge from '../components/people/PersonStatusBadge'
import AccessStatusBadge from '../components/users/AccessStatusBadge'
import { useCan } from '../hooks/useAuth'
import {
  useChurchJourney,
  usePerson,
  useStartChurchJourney,
  useUpdatePerson,
} from '../hooks/usePeople'
import type { ChurchJourney, Person, PersonStatus } from '../types/person'

function formatDate(value: string) {
  if (!value) {
    return '-'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    const [year, month, day] = value.split('-')
    return year && month && day ? `${day}/${month}/${year}` : value
  }

  return new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' }).format(date)
}

function getTodayInputValue() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function DetailItem({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="profile-detail">
      <dt>{label}</dt>
      <dd>{value || '-'}</dd>
    </div>
  )
}

function ProfileSection({
  children,
  title,
}: {
  children: ReactNode
  title: string
}) {
  const titleId = title.toLowerCase().replace(/\s+/g, '-')

  return (
    <section className="profile-section" aria-labelledby={`profile-section-${titleId}`}>
      <h2 id={`profile-section-${titleId}`}>{title}</h2>
      <dl className="profile-details">{children}</dl>
    </section>
  )
}

function LifecycleDialog({
  error,
  isOpen,
  isPending,
  onClose,
  onConfirm,
  person,
}: {
  error: string | null
  isOpen: boolean
  isPending: boolean
  onClose: () => void
  onConfirm: () => void
  person: Person
}) {
  if (!isOpen) {
    return null
  }

  const isActive = person.status === 'ACTIVE'
  const actionLabel = isActive ? 'Inativar pessoa' : 'Reativar pessoa'
  const pendingLabel = isActive ? 'Inativando...' : 'Reativando...'

  return (
    <div className="dialog-backdrop" role="presentation">
      <div
        className="confirm-dialog"
        role="dialog"
        aria-labelledby="lifecycle-dialog-title"
        aria-describedby="lifecycle-dialog-description"
        aria-modal="true"
        onKeyDown={(event) => {
          if (event.key === 'Escape' && !isPending) {
            onClose()
          }
        }}
      >
        <h2 id="lifecycle-dialog-title">
          {isActive ? `Inativar ${person.display_name}?` : `Reativar ${person.display_name}?`}
        </h2>
        <p id="lifecycle-dialog-description">
          {isActive
            ? 'A pessoa continuara cadastrada e seu historico sera preservado.'
            : 'A pessoa voltara a aparecer como ativa no cadastro.'}
        </p>

        {error ? (
          <div className="form-alert form-alert--error" role="alert">
            {error}
          </div>
        ) : null}

        <div className="form-actions">
          <button
            className="button button--secondary"
            type="button"
            disabled={isPending}
            onClick={onClose}
            autoFocus
          >
            Cancelar
          </button>
          <button className="button button--primary" type="button" disabled={isPending} onClick={onConfirm}>
            <RefreshCcw size={17} aria-hidden="true" />
            {isPending ? pendingLabel : actionLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

function StartChurchJourneyDialog({
  error,
  isOpen,
  isPending,
  onClose,
  onConfirm,
  person,
  startedAt,
  onStartedAtChange,
}: {
  error: string | null
  isOpen: boolean
  isPending: boolean
  onClose: () => void
  onConfirm: () => void
  person: Person
  startedAt: string
  onStartedAtChange: (value: string) => void
}) {
  if (!isOpen) {
    return null
  }

  return (
    <div className="dialog-backdrop" role="presentation">
      <div
        className="confirm-dialog"
        role="dialog"
        aria-labelledby="church-journey-dialog-title"
        aria-describedby="church-journey-dialog-description"
        aria-modal="true"
        onKeyDown={(event) => {
          if (event.key === 'Escape' && !isPending) {
            onClose()
          }
        }}
      >
        <h2 id="church-journey-dialog-title">Iniciar jornada de {person.display_name}?</h2>
        <p id="church-journey-dialog-description">
          Ao iniciar a jornada, esta pessoa passara a ser considerada Visitante da igreja.
        </p>

        <label className="field-group">
          <span>Data de inicio</span>
          <input
            type="date"
            value={startedAt}
            disabled={isPending}
            onChange={(event) => onStartedAtChange(event.target.value)}
          />
        </label>

        {error ? (
          <div className="form-alert form-alert--error" role="alert">
            {error}
          </div>
        ) : null}

        <div className="form-actions">
          <button
            className="button button--secondary"
            type="button"
            disabled={isPending}
            onClick={onClose}
            autoFocus
          >
            Cancelar
          </button>
          <button className="button button--primary" type="button" disabled={isPending} onClick={onConfirm}>
            <Play size={17} aria-hidden="true" />
            {isPending ? 'Iniciando...' : 'Iniciar jornada'}
          </button>
        </div>
      </div>
    </div>
  )
}

function churchStatusLabel(status: ChurchJourney['church_status']) {
  if (status === 'VISITOR') {
    return 'Visitante'
  }
  if (status === 'MEMBER') {
    return 'Membro'
  }
  return 'Indefinida'
}

function PersonProfile({
  canChangePeople,
  canCreateChurchJourney,
  canViewChurchJourney,
  canViewUsers,
  churchJourney,
  churchJourneyError,
  churchJourneyLoading,
  onLifecycleClick,
  onStartChurchJourneyClick,
  person,
  successMessage,
}: {
  canChangePeople: boolean
  canCreateChurchJourney: boolean
  canViewChurchJourney: boolean
  canViewUsers: boolean
  churchJourney: ChurchJourney | null | undefined
  churchJourneyError: boolean
  churchJourneyLoading: boolean
  onLifecycleClick: () => void
  onStartChurchJourneyClick: () => void
  person: Person
  successMessage: string | null
}) {
  const hasDifferentFullName = person.full_name !== person.display_name
  const lifecycleLabel = person.status === 'ACTIVE' ? 'Inativar pessoa' : 'Reativar pessoa'

  return (
    <>
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/pessoas">Pessoas</Link>
        <span aria-hidden="true">/</span>
        <strong>{person.display_name}</strong>
      </nav>

      <header className="profile-header">
        <PersonAvatar name={person.display_name} />
        <div className="profile-header__identity">
          <h1>{person.display_name}</h1>
          {hasDifferentFullName ? <p>{person.full_name}</p> : null}
          <PersonStatusBadge status={person.status} />
        </div>
        {canChangePeople ? (
          <div className="profile-actions">
            <Link className="button button--primary" to={`/pessoas/${person.id}/editar`}>
              <Edit3 size={17} aria-hidden="true" />
              Editar pessoa
            </Link>
            <button className="button button--secondary" type="button" onClick={onLifecycleClick}>
              <RefreshCcw size={17} aria-hidden="true" />
              {lifecycleLabel}
            </button>
          </div>
        ) : null}
      </header>

      {successMessage ? (
        <div className="form-alert form-alert--success" role="status">
          {successMessage}
        </div>
      ) : null}

      <div className="profile-content">
        <ProfileSection title="Dados pessoais">
          <DetailItem label="Nome completo" value={person.full_name} />
          <DetailItem label="Nome preferido" value={person.preferred_name || '-'} />
          <DetailItem label="Data de nascimento" value={formatDate(person.birth_date)} />
        </ProfileSection>

        <ProfileSection title="Contato">
          <DetailItem label="E-mail" value={person.email || '-'} />
          <DetailItem label="Telefone" value={person.phone || '-'} />
        </ProfileSection>

        <ProfileSection title="Controle">
          <DetailItem label="Status" value={<PersonStatusBadge status={person.status} />} />
          <DetailItem label="Criado em" value={formatDate(person.created_at)} />
          <DetailItem label="Atualizado em" value={formatDate(person.updated_at)} />
        </ProfileSection>

        <section className="profile-section">
          <h2>Acesso ao Portal</h2>
          {person.portal_user ? (
            <div className="portal-access-summary">
              <dl className="profile-details">
                <DetailItem label="Usuario" value={person.portal_user.username} />
                <DetailItem
                  label="Status do acesso"
                  value={<AccessStatusBadge status={person.portal_user.access_status} />}
                />
              </dl>
              {canViewUsers ? (
                <Link className="button button--secondary" to={`/pessoas/${person.id}/acesso`}>
                  Gerenciar acesso
                </Link>
              ) : null}
            </div>
          ) : (
            <p className="page-heading__description">Sem acesso ao Portal</p>
          )}
        </section>

        {canViewChurchJourney ? (
          <section className="profile-section">
            <h2>Jornada na igreja</h2>
            {churchJourneyLoading ? (
              <p className="page-heading__description">Carregando jornada...</p>
            ) : churchJourneyError ? (
              <p className="page-heading__description">Nao foi possivel carregar a jornada da igreja.</p>
            ) : churchJourney ? (
              <dl className="profile-details">
                <DetailItem label="Situacao" value={churchStatusLabel(churchJourney.church_status)} />
                <DetailItem label="Inicio" value={formatDate(churchJourney.started_at)} />
              </dl>
            ) : (
              <div className="church-journey-empty">
                <p className="page-heading__description">
                  Esta pessoa ainda nao esta na jornada eclesiastica.
                </p>
                {canCreateChurchJourney ? (
                  <button className="button button--primary" type="button" onClick={onStartChurchJourneyClick}>
                    <Play size={17} aria-hidden="true" />
                    Iniciar jornada
                  </button>
                ) : null}
              </div>
            )}
          </section>
        ) : null}
      </div>
    </>
  )
}

function PersonProfilePage() {
  const { id } = useParams()
  const location = useLocation()
  const personId = Number(id)
  const isValidId = Number.isInteger(personId) && personId > 0
  const { data: person, error, isError, isLoading, refetch } = usePerson(personId)
  const updatePerson = useUpdatePerson(personId)
  const canChangePeople = useCan('PEOPLE_CHANGE')
  const canViewUsers = useCan('USER_VIEW')
  const canViewChurchJourney = useCan('CHURCH_JOURNEY_VIEW')
  const canCreateChurchJourney = useCan('CHURCH_JOURNEY_CREATE')
  const {
    data: churchJourney,
    isError: isChurchJourneyError,
    isLoading: isChurchJourneyLoading,
  } = useChurchJourney(personId, canViewChurchJourney && isValidId)
  const startChurchJourney = useStartChurchJourney(personId)
  const [isLifecycleDialogOpen, setIsLifecycleDialogOpen] = useState(false)
  const [lifecycleError, setLifecycleError] = useState<string | null>(null)
  const [lifecycleSuccessMessage, setLifecycleSuccessMessage] = useState<string | null>(null)
  const [isStartJourneyDialogOpen, setIsStartJourneyDialogOpen] = useState(false)
  const [startJourneyError, setStartJourneyError] = useState<string | null>(null)
  const [startedAt, setStartedAt] = useState(getTodayInputValue)
  const navigationState = location.state as { successMessage?: string } | null
  const successMessage = lifecycleSuccessMessage ?? navigationState?.successMessage ?? null
  const isNotFound = !isValidId || (error instanceof ApiHttpError && error.status === 404)

  const handleLifecycleConfirm = async () => {
    if (!person) {
      return
    }

    const nextStatus: PersonStatus = person.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'
    setLifecycleError(null)

    try {
      await updatePerson.mutateAsync({ status: nextStatus })
      setIsLifecycleDialogOpen(false)
      setLifecycleSuccessMessage(
        nextStatus === 'ACTIVE'
          ? 'Pessoa reativada com sucesso.'
          : 'Pessoa inativada com sucesso.',
      )
    } catch {
      setLifecycleError('Nao foi possivel alterar o status da pessoa.')
    }
  }

  const handleStartJourneyConfirm = async () => {
    setStartJourneyError(null)

    try {
      await startChurchJourney.mutateAsync({ started_at: startedAt })
      setIsStartJourneyDialogOpen(false)
      setLifecycleSuccessMessage('Jornada na igreja iniciada com sucesso.')
    } catch {
      setStartJourneyError('Nao foi possivel iniciar a jornada da igreja.')
    }
  }

  return (
    <section className="person-profile-page">
      {isLoading && isValidId ? (
        <div className="state-panel">
          <h1>Carregando pessoa...</h1>
          <p>Aguarde enquanto os dados sao carregados.</p>
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
          <h1>Nao foi possivel carregar os dados da pessoa.</h1>
          <p>Verifique a conexao com o backend e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            Tentar novamente
          </button>
        </div>
      ) : person ? (
        <>
          <PersonProfile
            canChangePeople={canChangePeople}
            canCreateChurchJourney={canCreateChurchJourney}
            canViewChurchJourney={canViewChurchJourney}
            canViewUsers={canViewUsers}
            churchJourney={churchJourney}
            churchJourneyError={isChurchJourneyError}
            churchJourneyLoading={isChurchJourneyLoading}
            onLifecycleClick={() => {
              setLifecycleError(null)
              setIsLifecycleDialogOpen(true)
            }}
            onStartChurchJourneyClick={() => {
              setStartJourneyError(null)
              setStartedAt(getTodayInputValue())
              setIsStartJourneyDialogOpen(true)
            }}
            person={person}
            successMessage={successMessage}
          />
          <LifecycleDialog
            error={lifecycleError}
            isOpen={isLifecycleDialogOpen}
            isPending={updatePerson.isPending}
            onClose={() => setIsLifecycleDialogOpen(false)}
            onConfirm={() => void handleLifecycleConfirm()}
            person={person}
          />
          <StartChurchJourneyDialog
            error={startJourneyError}
            isOpen={isStartJourneyDialogOpen}
            isPending={startChurchJourney.isPending}
            onClose={() => setIsStartJourneyDialogOpen(false)}
            onConfirm={() => void handleStartJourneyConfirm()}
            onStartedAtChange={setStartedAt}
            person={person}
            startedAt={startedAt}
          />
        </>
      ) : null}
    </section>
  )
}

export default PersonProfilePage
