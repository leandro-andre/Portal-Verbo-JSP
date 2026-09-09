import { useState, type ReactNode } from 'react'
import { ArrowLeft, ExternalLink, KeyRound, Lock, Mail, Send, ShieldCheck, Unlock, UserRound } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { UserAccessBusinessError, UserAccessHttpError } from '../api/users'
import PersonAvatar from '../components/people/PersonAvatar'
import PersonStatusBadge from '../components/people/PersonStatusBadge'
import AccessStatusBadge from '../components/users/AccessStatusBadge'
import {
  useDisableUser,
  useEnableUser,
  useResendUserActivation,
  useSendUserPasswordReset,
  useUserAdminProfile,
} from '../hooks/useUsers'

type AccessOperation = 'block' | 'unblock' | 'resend_activation' | 'password_reset'

function errorMessageFor(error: unknown) {
  if (error instanceof UserAccessBusinessError) {
    if (error.details.code === 'USER_EMAIL_CONFIGURATION_ERROR' || error.details.code === 'USER_EMAIL_DELIVERY_ERROR') {
      return 'Nao foi possivel enviar o e-mail.'
    }
    return error.details.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Nao foi possivel concluir a acao.'
}

function successMessageFor(operation: AccessOperation) {
  return {
    block: 'Acesso bloqueado.',
    unblock: 'Acesso desbloqueado.',
    resend_activation: 'E-mail de ativacao enviado.',
    password_reset: 'E-mail de recuperacao enviado.',
  }[operation]
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return null
  }
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'America/Sao_Paulo',
  }).format(new Date(value))
}

function yesNo(value: boolean) {
  return value ? 'Sim' : 'Nao'
}

function DetailItem({ label, value }: { label: string; value: ReactNode }) {
  const isEmpty = value === null || value === undefined || value === ''
  return (
    <div className="profile-detail">
      <dt>{label}</dt>
      <dd>{isEmpty ? '-' : value}</dd>
    </div>
  )
}

function AccessActionDialog({
  displayName,
  isPending,
  operation,
  onClose,
  onConfirm,
}: {
  displayName: string
  isPending: boolean
  operation: AccessOperation
  onClose: () => void
  onConfirm: () => void
}) {
  const isBlock = operation === 'block'
  const isUnblock = operation === 'unblock'
  const title = isBlock
    ? `Bloquear acesso de ${displayName}?`
    : isUnblock ? `Desbloquear acesso de ${displayName}?` : ''
  const message = isBlock
    ? 'A pessoa nao conseguira acessar o Portal ate que sua conta seja desbloqueada.'
    : 'A conta voltara a seguir o estado real definido pelo backend.'
  const confirmLabel = isBlock ? 'Bloquear acesso' : 'Desbloquear acesso'

  if (!isBlock && !isUnblock) {
    return null
  }

  return (
    <div className="dialog-backdrop" role="presentation">
      <div className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="user-access-dialog-title">
        <h2 id="user-access-dialog-title">{title}</h2>
        <div className="dialog-copy">
          <p>{message}</p>
        </div>
        <div className="profile-actions">
          <button className="button button--secondary" type="button" disabled={isPending} onClick={onClose}>
            Cancelar
          </button>
          <button className="button button--primary" type="button" disabled={isPending} onClick={onConfirm}>
            {isPending ? 'Confirmando...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

function UserAccessPage() {
  const { id } = useParams()
  const userId = Number(id)
  const isValidId = Number.isInteger(userId) && userId > 0
  const { data: profile, error, isError, isLoading, refetch } = useUserAdminProfile(userId)
  const blockUser = useDisableUser(userId)
  const unblockUser = useEnableUser(userId)
  const resendActivation = useResendUserActivation(userId)
  const sendPasswordReset = useSendUserPasswordReset(userId)
  const [dialogOperation, setDialogOperation] = useState<AccessOperation | null>(null)
  const [operationMessage, setOperationMessage] = useState<string | null>(null)
  const [operationError, setOperationError] = useState<string | null>(null)
  const isForbidden = error instanceof UserAccessHttpError && error.status === 403
  const isNotFound = !isValidId || (error instanceof UserAccessHttpError && error.status === 404)
  const accountEmail = profile?.account.email || 'E-mail nao informado'
  const isOperationPending =
    blockUser.isPending ||
    unblockUser.isPending ||
    resendActivation.isPending ||
    sendPasswordReset.isPending

  const runOperation = async (operation: AccessOperation) => {
    setOperationMessage(null)
    setOperationError(null)
    try {
      if (operation === 'block') {
        await blockUser.mutateAsync()
      } else if (operation === 'unblock') {
        await unblockUser.mutateAsync()
      } else if (operation === 'resend_activation') {
        await resendActivation.mutateAsync()
      } else {
        await sendPasswordReset.mutateAsync()
      }
      setOperationMessage(successMessageFor(operation))
      setDialogOperation(null)
    } catch (caught) {
      setOperationError(errorMessageFor(caught))
    }
  }

  return (
    <section className="person-profile-page user-admin-page">
      {isLoading && isValidId ? (
        <div className="state-panel">
          <h1>Carregando usuario...</h1>
          <p>Aguarde enquanto os dados da conta sao carregados.</p>
        </div>
      ) : isNotFound ? (
        <div className="state-panel">
          <h1>Usuario nao encontrado</h1>
          <p>Nao encontramos o usuario solicitado.</p>
          <Link className="button button--secondary" to="/usuarios">
            <ArrowLeft size={17} aria-hidden="true" />
            Voltar para Usuarios
          </Link>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h1>{isForbidden ? 'Acesso negado' : 'Nao foi possivel carregar o usuario.'}</h1>
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
      ) : profile ? (
        <>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link to="/usuarios">Usuarios</Link>
            <span aria-hidden="true">/</span>
            <strong>{profile.account.username}</strong>
          </nav>

          <header className="profile-header user-admin-header">
            {profile.person?.photo_url ? (
              <img className="user-admin-photo" src={profile.person.photo_url} alt="" />
            ) : (
              <PersonAvatar name={profile.display_name} />
            )}
            <div className="profile-header__identity">
              <h1>{profile.display_name}</h1>
              <p>{accountEmail}</p>
              <AccessStatusBadge status={profile.access_status.value} />
            </div>
            <div className="profile-actions">
              {profile.actions.can_view_person_profile && profile.actions.person_profile_url ? (
                <Link className="button button--secondary" to={profile.actions.person_profile_url}>
                  <ExternalLink size={17} aria-hidden="true" />
                  Abrir Ficha 360
                </Link>
              ) : null}
            </div>
          </header>

          <div className="profile-content user-admin-content">
            <section className="profile-section">
              <h2>Conta</h2>
              <dl className="profile-details">
                <DetailItem label="Usuario" value={profile.account.username} />
                <DetailItem label="E-mail da conta" value={profile.account.email || 'E-mail nao informado'} />
                <DetailItem label="Criada em" value={formatDateTime(profile.account.date_joined)} />
                <DetailItem
                  label="Ultimo login"
                  value={formatDateTime(profile.account.last_login) || 'Nenhum acesso registrado.'}
                />
                <DetailItem label="Conta habilitada" value={yesNo(profile.account.is_active)} />
                <DetailItem label="Senha configurada" value={yesNo(profile.account.has_usable_password)} />
                <DetailItem
                  label="Person vinculada"
                  value={profile.account.person_linked ? 'Sim' : 'Esta conta ainda nao esta vinculada a uma pessoa.'}
                />
              </dl>
            </section>

            <section className="profile-section">
              <h2>Pessoa vinculada</h2>
              {profile.person ? (
                <div className="user-admin-linked-person">
                  {profile.person.photo_url ? (
                    <img className="user-admin-linked-person__photo" src={profile.person.photo_url} alt="" />
                  ) : (
                    <PersonAvatar name={profile.person.display_name} />
                  )}
                  <dl className="profile-details">
                    <DetailItem label="ID" value={profile.person.id} />
                    <DetailItem
                      label="Nome"
                      value={
                        profile.actions.can_view_person_profile && profile.actions.person_profile_url ? (
                          <Link className="person-name-link" to={profile.actions.person_profile_url}>
                            {profile.person.display_name}
                          </Link>
                        ) : (
                          profile.person.display_name
                        )
                      }
                    />
                    <DetailItem label="Nome completo" value={profile.person.full_name} />
                    <DetailItem label="Status da pessoa" value={<PersonStatusBadge status={profile.person.status} />} />
                  </dl>
                </div>
              ) : (
                <div className="user-admin-empty">
                  <UserRound size={22} aria-hidden="true" />
                  <p>Esta conta ainda nao esta vinculada a uma pessoa.</p>
                </div>
              )}
            </section>

            <section className="profile-section">
              <h2>Ativacao</h2>
              <div className="user-admin-readonly-card">
                <Mail size={20} aria-hidden="true" />
                <div>
                  <strong>{profile.activation.label}</strong>
                  <p>{profile.activation.message}</p>
                </div>
              </div>
            </section>

            <section className="profile-section">
              <h2>Seguranca e acesso</h2>
              {operationMessage ? (
                <div className="form-alert form-alert--success" role="status">
                  {operationMessage}
                </div>
              ) : null}
              {operationError ? (
                <div className="form-alert form-alert--error" role="alert">
                  {operationError}
                </div>
              ) : null}
              <dl className="profile-details">
                <DetailItem label="Status" value={<AccessStatusBadge status={profile.security.status} />} />
                <DetailItem label="Conta habilitada" value={yesNo(profile.security.is_active)} />
                <DetailItem label="Senha configurada" value={yesNo(profile.security.has_usable_password)} />
              </dl>
              <p className="page-heading__description user-admin-section-note">{profile.security.message}</p>
              <div className="profile-actions user-admin-security-actions">
                {profile.actions.can_send_password_reset ? (
                  <button
                    className="button button--secondary"
                    type="button"
                    disabled={isOperationPending}
                    onClick={() => void runOperation('password_reset')}
                  >
                    <KeyRound size={17} aria-hidden="true" />
                    {sendPasswordReset.isPending ? 'Enviando...' : 'Enviar recuperacao de senha'}
                  </button>
                ) : null}
                {profile.actions.can_resend_activation ? (
                  <button
                    className="button button--secondary"
                    type="button"
                    disabled={isOperationPending}
                    onClick={() => void runOperation('resend_activation')}
                  >
                    <Send size={17} aria-hidden="true" />
                    {resendActivation.isPending ? 'Enviando...' : 'Reenviar e-mail de ativacao'}
                  </button>
                ) : null}
                {profile.actions.can_unblock ? (
                  <button
                    className="button button--primary"
                    type="button"
                    disabled={isOperationPending}
                    onClick={() => setDialogOperation('unblock')}
                  >
                    <Unlock size={17} aria-hidden="true" />
                    Desbloquear acesso
                  </button>
                ) : null}
                {profile.actions.can_block ? (
                  <button
                    className="button button--secondary"
                    type="button"
                    disabled={isOperationPending}
                    onClick={() => setDialogOperation('block')}
                  >
                    <Lock size={17} aria-hidden="true" />
                    Bloquear acesso
                  </button>
                ) : null}
              </div>
            </section>

            {profile.access_request ? (
              <section className="profile-section">
                <h2>Solicitacao de acesso</h2>
                <dl className="profile-details">
                  <DetailItem
                    label="Solicitacao"
                    value={
                      <Link className="person-name-link" to={profile.access_request.detail_url}>
                        #{profile.access_request.id}
                      </Link>
                    }
                  />
                  <DetailItem label="Status" value={profile.access_request.status_label} />
                  <DetailItem label="Criada em" value={formatDateTime(profile.access_request.created_at)} />
                  <DetailItem label="Revisada em" value={formatDateTime(profile.access_request.reviewed_at) || 'Ainda nao revisada.'} />
                </dl>
              </section>
            ) : null}
          </div>

          <div className="person360-footer-actions profile-actions">
            <Link className="button button--secondary" to="/usuarios">
              <ArrowLeft size={17} aria-hidden="true" />
              Voltar para Usuarios
            </Link>
            {profile.actions.can_view_person_profile && profile.actions.person_profile_url ? (
              <Link className="button button--secondary" to={profile.actions.person_profile_url}>
                <ShieldCheck size={17} aria-hidden="true" />
                Ver Ficha 360
              </Link>
            ) : null}
          </div>

          {dialogOperation ? (
            <AccessActionDialog
              displayName={profile.display_name}
              isPending={isOperationPending}
              operation={dialogOperation}
              onClose={() => setDialogOperation(null)}
              onConfirm={() => void runOperation(dialogOperation)}
            />
          ) : null}
        </>
      ) : null}
    </section>
  )
}

export default UserAccessPage
