import { useState, type ReactNode } from 'react'
import { ArrowLeft, RefreshCcw, ShieldOff, UserCheck } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { ApiHttpError } from '../api/people'
import { UserAccessBusinessError, UserAccessHttpError } from '../api/users'
import AccessStatusBadge from '../components/users/AccessStatusBadge'
import PersonAvatar from '../components/people/PersonAvatar'
import { useCan } from '../hooks/useAuth'
import { usePerson } from '../hooks/usePeople'
import { useDisableUser, useEnableUser, useUser } from '../hooks/useUsers'
import type { PortalUser } from '../types/user'

function formatDate(value?: string | null) {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeZone: 'America/Sao_Paulo',
  }).format(new Date(value))
}

function DetailItem({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="profile-detail">
      <dt>{label}</dt>
      <dd>{value || '-'}</dd>
    </div>
  )
}

function AccessDialog({
  error,
  isOpen,
  isPending,
  mode,
  onClose,
  onConfirm,
  user,
}: {
  error: string | null
  isOpen: boolean
  isPending: boolean
  mode: 'disable' | 'enable'
  onClose: () => void
  onConfirm: () => void
  user: PortalUser
}) {
  if (!isOpen) {
    return null
  }

  const displayName = user.person?.display_name || user.username
  const isDisable = mode === 'disable'

  return (
    <div className="dialog-backdrop" role="presentation">
      <div
        className="confirm-dialog"
        role="dialog"
        aria-labelledby="access-lifecycle-dialog-title"
        aria-describedby="access-lifecycle-dialog-description"
        aria-modal="true"
      >
        <h2 id="access-lifecycle-dialog-title">
          {isDisable ? `Bloquear acesso de ${displayName}?` : `Reativar acesso de ${displayName}?`}
        </h2>
        <p id="access-lifecycle-dialog-description">
          {isDisable
            ? 'Essa pessoa nao podera entrar no Portal, mas seu cadastro e historico serao preservados.'
            : 'A conta voltara a poder autenticar com a senha ja definida.'}
        </p>

        {error ? (
          <div className="form-alert form-alert--error" role="alert">
            {error}
          </div>
        ) : null}

        <div className="form-actions">
          <button className="button button--secondary" type="button" disabled={isPending} onClick={onClose} autoFocus>
            Cancelar
          </button>
          <button className="button button--primary" type="button" disabled={isPending} onClick={onConfirm}>
            {isDisable ? <ShieldOff size={17} aria-hidden="true" /> : <UserCheck size={17} aria-hidden="true" />}
            {isPending
              ? isDisable ? 'Bloqueando...' : 'Reativando...'
              : isDisable ? 'Bloquear acesso' : 'Reativar acesso'}
          </button>
        </div>
      </div>
    </div>
  )
}

function UserAccessPage() {
  const { id } = useParams()
  const personId = Number(id)
  const isValidId = Number.isInteger(personId) && personId > 0
  const { data: person, error: personError, isError: isPersonError, isLoading: isPersonLoading } = usePerson(personId)
  const userId = person?.portal_user?.id ?? 0
  const { data: user, error: userError, isError: isUserError, isLoading: isUserLoading, refetch } = useUser(userId)
  const disableUser = useDisableUser(userId)
  const enableUser = useEnableUser(userId)
  const [dialogMode, setDialogMode] = useState<'disable' | 'enable' | null>(null)
  const [dialogError, setDialogError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const canDisableUser = useCan('USER_DISABLE')
  const canEnableUser = useCan('USER_ENABLE')
  const isNotFound = !isValidId || (personError instanceof ApiHttpError && personError.status === 404)
  const isForbidden = userError instanceof UserAccessHttpError && userError.status === 403

  const handleBusinessError = (error: unknown) => {
    if (error instanceof UserAccessBusinessError) {
      if (error.details.code === 'CANNOT_DISABLE_OWN_ACCOUNT') {
        setDialogError('Voce nao pode bloquear sua propria conta.')
        return
      }
      if (error.details.code === 'CANNOT_DISABLE_SUPERUSER') {
        setDialogError('Contas superuser nao podem ser bloqueadas por este fluxo.')
        return
      }
      if (error.details.code === 'USER_ACCESS_NOT_BLOCKED') {
        setDialogError('Esta conta nao esta bloqueada.')
        return
      }
      if (error.details.code === 'USER_ACCESS_NOT_ACTIVE') {
        setDialogError('Esta conta nao esta ativa.')
        return
      }
    }

    setDialogError('Nao foi possivel alterar o acesso.')
  }

  const handleDisable = async () => {
    setDialogError(null)
    try {
      await disableUser.mutateAsync()
      setDialogMode(null)
      setSuccessMessage('Acesso bloqueado com sucesso.')
    } catch (error) {
      handleBusinessError(error)
    }
  }

  const handleEnable = async () => {
    setDialogError(null)
    try {
      await enableUser.mutateAsync()
      setDialogMode(null)
      setSuccessMessage('Acesso reativado com sucesso.')
    } catch (error) {
      handleBusinessError(error)
    }
  }

  return (
    <section className="person-profile-page">
      {isPersonLoading && isValidId ? (
        <div className="state-panel">
          <h1>Carregando acesso...</h1>
          <p>Aguarde enquanto os dados sao carregados.</p>
        </div>
      ) : isNotFound ? (
        <div className="state-panel">
          <h1>Pessoa nao encontrada</h1>
          <p>Nao encontramos a pessoa solicitada.</p>
          <Link className="button button--secondary" to="/usuarios">
            <ArrowLeft size={17} aria-hidden="true" />
            Voltar para Usuarios
          </Link>
        </div>
      ) : person && !person.portal_user ? (
        <div className="state-panel">
          <h1>Sem acesso ao Portal</h1>
          <p>Esta pessoa ainda nao possui uma conta de usuario vinculada.</p>
          <Link className="button button--secondary" to={`/pessoas/${person.id}`}>
            Voltar para perfil
          </Link>
        </div>
      ) : isUserLoading ? (
        <div className="state-panel">
          <h1>Carregando usuario...</h1>
          <p>Aguarde enquanto os dados da conta sao carregados.</p>
        </div>
      ) : isPersonError || isUserError ? (
        <div className="state-panel state-panel--error">
          <h1>{isForbidden ? 'Acesso negado' : 'Nao foi possivel carregar o acesso.'}</h1>
          <p>
            {isForbidden
              ? 'Sua sessao atual nao possui permissao para administrar usuarios.'
              : 'Verifique a conexao com o backend e tente novamente.'}
          </p>
          {!isForbidden ? (
            <button className="button button--secondary" type="button" onClick={() => void refetch()}>
              Tentar novamente
            </button>
          ) : null}
        </div>
      ) : person && user ? (
        <>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link to="/usuarios">Usuarios</Link>
            <span aria-hidden="true">/</span>
            <strong>{person.display_name}</strong>
          </nav>

          <header className="profile-header">
            <PersonAvatar name={person.display_name} />
            <div className="profile-header__identity">
              <h1>{person.display_name}</h1>
              <p>{user.username}</p>
              <AccessStatusBadge status={user.access_status} />
            </div>
            <div className="profile-actions">
              <Link className="button button--secondary" to={`/pessoas/${person.id}`}>
                Ver perfil
              </Link>
              {user.access_status === 'ACTIVE' && canDisableUser ? (
                <button
                  className="button button--primary"
                  type="button"
                  onClick={() => {
                    setDialogError(null)
                    setDialogMode('disable')
                  }}
                >
                  <ShieldOff size={17} aria-hidden="true" />
                  Bloquear acesso
                </button>
              ) : null}
              {user.access_status === 'BLOCKED' && canEnableUser ? (
                <button
                  className="button button--primary"
                  type="button"
                  onClick={() => {
                    setDialogError(null)
                    setDialogMode('enable')
                  }}
                >
                  <RefreshCcw size={17} aria-hidden="true" />
                  Reativar acesso
                </button>
              ) : null}
            </div>
          </header>

          {successMessage ? (
            <div className="form-alert form-alert--success" role="status">
              {successMessage}
            </div>
          ) : null}

          <div className="profile-content">
            <section className="profile-section">
              <h2>Pessoa</h2>
              <dl className="profile-details">
                <DetailItem label="Nome" value={person.display_name} />
                <DetailItem label="Status da pessoa" value={person.status === 'ACTIVE' ? 'Ativa' : 'Inativa'} />
              </dl>
            </section>

            <section className="profile-section">
              <h2>Acesso</h2>
              <dl className="profile-details">
                <DetailItem label="Usuario" value={user.username} />
                <DetailItem label="Status" value={<AccessStatusBadge status={user.access_status} />} />
                <DetailItem label="Ultimo login" value={formatDate(user.last_login)} />
                <DetailItem label="Criado em" value={formatDate(user.date_joined)} />
              </dl>
            </section>
          </div>

          {user.access_status === 'PENDING_ACTIVATION' ? (
            <div className="form-alert form-alert--success" role="status">
              Esta conta aguarda ativacao inicial. Reativar acesso nao define senha nem substitui a ativacao.
            </div>
          ) : null}

          <AccessDialog
            error={dialogError}
            isOpen={dialogMode !== null}
            isPending={disableUser.isPending || enableUser.isPending}
            mode={dialogMode ?? 'disable'}
            onClose={() => setDialogMode(null)}
            onConfirm={dialogMode === 'enable' ? () => void handleEnable() : () => void handleDisable()}
            user={user}
          />
        </>
      ) : null}
    </section>
  )
}

export default UserAccessPage
