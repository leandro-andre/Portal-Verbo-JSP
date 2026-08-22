import { useState, type ReactNode } from 'react'
import { ArrowLeft, Link2, RefreshCcw, Search, ShieldOff, Unlink } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { UserAccessBusinessError, UserAccessHttpError } from '../api/users'
import PersonStatusBadge from '../components/people/PersonStatusBadge'
import AccessStatusBadge from '../components/users/AccessStatusBadge'
import { usePeopleSearch } from '../hooks/usePeople'
import {
  useDisableUser,
  useEnableUser,
  useLinkUserPerson,
  useUnlinkUserPerson,
  useUser,
} from '../hooks/useUsers'
import type { Person } from '../types/person'

type DialogMode = 'disable' | 'enable' | 'link' | 'unlink'

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

function ConfirmationDialog({
  children,
  confirmLabel,
  error,
  isOpen,
  isPending,
  onClose,
  onConfirm,
  title,
}: {
  children: ReactNode
  confirmLabel: string
  error: string | null
  isOpen: boolean
  isPending: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
}) {
  if (!isOpen) {
    return null
  }

  return (
    <div className="dialog-backdrop" role="presentation">
      <div className="confirm-dialog" role="dialog" aria-labelledby="user-dialog-title" aria-modal="true">
        <h2 id="user-dialog-title">{title}</h2>
        <div className="dialog-copy">{children}</div>
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
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

function PersonSearchPanel({
  currentPersonId,
  onConfirm,
}: {
  currentPersonId?: number
  onConfirm: (person: Person) => void
}) {
  const [searchTerm, setSearchTerm] = useState('')
  const { data: people = [], isFetching } = usePeopleSearch(searchTerm)
  const candidates = people.filter((person) => person.id !== currentPersonId)

  return (
    <div className="link-person-panel">
      <label className="search-field">
        <Search className="search-field__icon" size={18} aria-hidden="true" />
        <span className="sr-only">Pesquisar pessoa</span>
        <input
          type="search"
          placeholder="Buscar por nome, nome preferido ou e-mail"
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
        />
      </label>
      {searchTerm.trim().length < 2 ? (
        <p className="page-heading__description">Digite ao menos 2 caracteres para pesquisar.</p>
      ) : isFetching ? (
        <p className="page-heading__description">Buscando pessoas...</p>
      ) : candidates.length === 0 ? (
        <p className="page-heading__description">Nenhuma pessoa encontrada.</p>
      ) : (
        <div className="identity-options">
          {candidates.map((person) => (
            <button
              className="identity-option identity-option--button"
              key={person.id}
              type="button"
              onClick={() => onConfirm(person)}
            >
              <span>
                <strong>{person.display_name}</strong>
                <span>{person.full_name}</span>
                <span>{person.email || '-'}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function UserAccessPage() {
  const { id } = useParams()
  const userId = Number(id)
  const isValidId = Number.isInteger(userId) && userId > 0
  const { data: user, error, isError, isLoading, refetch } = useUser(userId)
  const disableUser = useDisableUser(userId)
  const enableUser = useEnableUser(userId)
  const linkUserPerson = useLinkUserPerson(userId)
  const unlinkUserPerson = useUnlinkUserPerson(userId)
  const [dialogMode, setDialogMode] = useState<DialogMode | null>(null)
  const [dialogError, setDialogError] = useState<string | null>(null)
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const isForbidden = error instanceof UserAccessHttpError && error.status === 403
  const isNotFound = !isValidId || (error instanceof UserAccessHttpError && error.status === 404)
  const isMutating =
    disableUser.isPending ||
    enableUser.isPending ||
    linkUserPerson.isPending ||
    unlinkUserPerson.isPending

  const closeDialog = () => {
    setDialogMode(null)
    setDialogError(null)
    setSelectedPerson(null)
  }

  const openDialog = (mode: DialogMode) => {
    setDialogError(null)
    setSelectedPerson(null)
    setDialogMode(mode)
  }

  const handleBusinessError = (mutationError: unknown) => {
    if (mutationError instanceof UserAccessBusinessError) {
      if (mutationError.details.code === 'CANNOT_DISABLE_OWN_ACCOUNT') {
        setDialogError('Voce nao pode bloquear sua propria conta.')
        return
      }
      if (mutationError.details.code === 'CANNOT_DISABLE_SUPERUSER') {
        setDialogError('Contas superuser nao podem ser bloqueadas por este fluxo.')
        return
      }
      if (mutationError.details.code === 'USER_ACCESS_NOT_BLOCKED') {
        setDialogError('Esta conta nao esta bloqueada.')
        return
      }
      if (mutationError.details.code === 'USER_ACCESS_NOT_ACTIVE') {
        setDialogError('Esta conta nao esta ativa.')
        return
      }
      if (mutationError.details.code === 'PERSON_ALREADY_HAS_USER') {
        setDialogError('Esta pessoa ja possui outro usuario vinculado.')
        return
      }
      if (mutationError.details.code === 'PERSON_NOT_FOUND') {
        setDialogError('Pessoa selecionada nao encontrada.')
        return
      }
    }
    setDialogError('Nao foi possivel processar a operacao.')
  }

  const handleDisable = async () => {
    setDialogError(null)
    try {
      await disableUser.mutateAsync()
      closeDialog()
      setSuccessMessage('Acesso bloqueado com sucesso.')
    } catch (mutationError) {
      handleBusinessError(mutationError)
    }
  }

  const handleEnable = async () => {
    setDialogError(null)
    try {
      await enableUser.mutateAsync()
      closeDialog()
      setSuccessMessage('Acesso desbloqueado com sucesso.')
    } catch (mutationError) {
      handleBusinessError(mutationError)
    }
  }

  const handleLink = async () => {
    if (!selectedPerson) {
      return
    }
    setDialogError(null)
    try {
      await linkUserPerson.mutateAsync({ person_id: selectedPerson.id })
      closeDialog()
      setSuccessMessage('Vinculo atualizado com sucesso.')
    } catch (mutationError) {
      handleBusinessError(mutationError)
    }
  }

  const handleUnlink = async () => {
    setDialogError(null)
    try {
      await unlinkUserPerson.mutateAsync()
      closeDialog()
      setSuccessMessage('Vinculo removido com sucesso.')
    } catch (mutationError) {
      handleBusinessError(mutationError)
    }
  }

  return (
    <section className="person-profile-page">
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
      ) : user ? (
        <>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link to="/usuarios">Usuarios</Link>
            <span aria-hidden="true">/</span>
            <strong>{user.username}</strong>
          </nav>

          <header className="profile-header">
            <div className="profile-header__identity">
              <h1>{user.username}</h1>
              <p>{user.person?.display_name || 'Nenhuma pessoa vinculada'}</p>
              <AccessStatusBadge status={user.access_status} />
            </div>
            <div className="profile-actions">
              {user.person ? (
                <Link className="button button--secondary" to={`/pessoas/${user.person.id}`}>
                  Ver pessoa
                </Link>
              ) : null}
              <button className="button button--secondary" type="button" onClick={() => openDialog('link')}>
                <Link2 size={17} aria-hidden="true" />
                {user.person ? 'Alterar vinculo' : 'Vincular pessoa'}
              </button>
              {user.person ? (
                <button className="button button--secondary" type="button" onClick={() => openDialog('unlink')}>
                  <Unlink size={17} aria-hidden="true" />
                  Remover vinculo
                </button>
              ) : null}
              {user.access_status === 'ACTIVE' ? (
                <button className="button button--primary" type="button" onClick={() => openDialog('disable')}>
                  <ShieldOff size={17} aria-hidden="true" />
                  Bloquear acesso
                </button>
              ) : null}
              {user.access_status === 'BLOCKED' ? (
                <button className="button button--primary" type="button" onClick={() => openDialog('enable')}>
                  <RefreshCcw size={17} aria-hidden="true" />
                  Desbloquear acesso
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
              <h2>Identidade</h2>
              <dl className="profile-details">
                <DetailItem label="Usuario" value={user.username} />
                <DetailItem
                  label="Pessoa vinculada"
                  value={
                    user.person ? (
                      <Link className="person-name-link" to={`/pessoas/${user.person.id}`}>
                        {user.person.display_name}
                      </Link>
                    ) : (
                      'Nenhuma pessoa vinculada'
                    )
                  }
                />
                {user.person ? <DetailItem label="E-mail da pessoa" value={user.person.email || '-'} /> : null}
              </dl>
            </section>

            {user.person ? (
              <section className="profile-section">
                <h2>Pessoa</h2>
                <dl className="profile-details">
                  <DetailItem label="Nome" value={user.person.display_name} />
                  <DetailItem label="Nome completo" value={user.person.full_name} />
                  <DetailItem label="Status da pessoa" value={<PersonStatusBadge status={user.person.status} />} />
                </dl>
              </section>
            ) : null}

            <section className="profile-section">
              <h2>Acesso</h2>
              <dl className="profile-details">
                <DetailItem label="Status" value={<AccessStatusBadge status={user.access_status} />} />
                <DetailItem label="Ultimo login" value={formatDate(user.last_login)} />
                <DetailItem label="Criado em" value={formatDate(user.date_joined)} />
              </dl>
            </section>

            <section className="profile-section">
              <h2>Senha</h2>
              <p className="page-heading__description">
                Senhas nao podem ser visualizadas. A redefinicao segura ainda depende de infraestrutura propria de recuperacao.
              </p>
            </section>
          </div>

          <ConfirmationDialog
            confirmLabel={dialogMode === 'enable' ? 'Desbloquear acesso' : 'Bloquear acesso'}
            error={dialogError}
            isOpen={dialogMode === 'disable' || dialogMode === 'enable'}
            isPending={isMutating}
            onClose={closeDialog}
            onConfirm={dialogMode === 'enable' ? () => void handleEnable() : () => void handleDisable()}
            title={dialogMode === 'enable' ? `Desbloquear ${user.username}?` : `Bloquear ${user.username}?`}
          >
            <p>
              {dialogMode === 'enable'
                ? 'A conta voltara a poder autenticar com a senha ja definida.'
                : 'Este usuario nao podera entrar no Portal, mas a conta e os historicos serao preservados.'}
            </p>
          </ConfirmationDialog>

          <ConfirmationDialog
            confirmLabel="Confirmar vinculo"
            error={dialogError}
            isOpen={dialogMode === 'link' && selectedPerson !== null}
            isPending={isMutating}
            onClose={closeDialog}
            onConfirm={() => void handleLink()}
            title={user.person ? 'Alterar vinculo?' : 'Vincular pessoa?'}
          >
            <p>
              {user.person ? `Vinculo atual: ${user.person.display_name}.` : 'Este usuario ainda nao possui pessoa vinculada.'}
            </p>
            <p>Novo vinculo: <strong>{selectedPerson?.display_name}</strong>.</p>
          </ConfirmationDialog>

          {dialogMode === 'link' && selectedPerson === null ? (
            <div className="dialog-backdrop" role="presentation">
              <div className="confirm-dialog" role="dialog" aria-labelledby="link-person-title" aria-modal="true">
                <h2 id="link-person-title">{user.person ? 'Alterar vinculo' : 'Vincular pessoa'}</h2>
                <PersonSearchPanel
                  currentPersonId={user.person?.id}
                  onConfirm={(person) => setSelectedPerson(person)}
                />
                {dialogError ? (
                  <div className="form-alert form-alert--error" role="alert">
                    {dialogError}
                  </div>
                ) : null}
                <div className="form-actions">
                  <button className="button button--secondary" type="button" onClick={closeDialog}>
                    Cancelar
                  </button>
                </div>
              </div>
            </div>
          ) : null}

          <ConfirmationDialog
            confirmLabel="Remover vinculo"
            error={dialogError}
            isOpen={dialogMode === 'unlink'}
            isPending={isMutating}
            onClose={closeDialog}
            onConfirm={() => void handleUnlink()}
            title="Remover vinculo?"
          >
            <p>
              Deseja remover o vinculo entre este usuario e esta pessoa? O acesso do usuario nao sera excluido.
            </p>
          </ConfirmationDialog>
        </>
      ) : null}
    </section>
  )
}

export default UserAccessPage
