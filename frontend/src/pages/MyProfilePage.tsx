import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Camera, RefreshCcw, Save, Trash2, UserRound } from 'lucide-react'
import { MyProfileError } from '../api/profile'
import { useMyProfile, useMyProfileMutations } from '../hooks/useMyProfile'
import { formatBrazilianMobile } from '../utils/phone'

function initials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'UP'
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  const [year, month, day] = value.split('-')
  return year && month && day ? `${day}/${month}/${year}` : value
}

function statusLabel(value?: string | null) {
  if (!value) return '-'
  return value === 'ACTIVE' ? 'Ativo' : 'Inativo'
}

function MyProfilePage() {
  const { data, isError, isLoading, refetch } = useMyProfile()
  const mutations = useMyProfileMutations()
  const [phoneDraft, setPhoneDraft] = useState<{ personId: number; value: string } | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [phoneError, setPhoneError] = useState<string | null>(null)
  const [photoError, setPhotoError] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const person = data?.person
  const photoUrl = preview || person?.photo_url || null
  const displayName = person?.display_name || data?.account.display_name || 'Usuario'
  const isSaving = mutations.update.isPending || mutations.uploadPhoto.isPending || mutations.deletePhoto.isPending
  const phone = person && phoneDraft?.personId === person.id
    ? phoneDraft.value
    : formatBrazilianMobile(person?.phone ?? '')

  useEffect(() => () => {
    if (preview) URL.revokeObjectURL(preview)
  }, [preview])

  const departments = useMemo(() => data?.departments ?? [], [data?.departments])

  const runAction = async (action: () => Promise<unknown>, success: string) => {
    setError(null)
    setPhoneError(null)
    setPhotoError(null)
    try {
      await action()
      setMessage(success)
    } catch (actionError) {
      if (actionError instanceof MyProfileError) {
        setPhoneError(actionError.fieldErrors.phone?.[0] ?? null)
        setPhotoError(actionError.fieldErrors.photo?.[0] ?? null)
        setError(actionError.message)
      } else {
        setError('Nao foi possivel concluir a acao.')
      }
    }
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    void runAction(() => mutations.update.mutateAsync({ phone }), 'Perfil atualizado.')
  }

  const handlePhotoChange = (file: File | undefined) => {
    if (!file) return
    if (preview) URL.revokeObjectURL(preview)
    setPreview(URL.createObjectURL(file))
    void runAction(
      () => mutations.uploadPhoto.mutateAsync(file),
      'Foto atualizada.',
    ).finally(() => {
      setPreview(null)
    })
  }

  if (isLoading) {
    return <section className="person-profile-page"><div className="state-panel"><h1>Carregando perfil...</h1></div></section>
  }

  if (isError || !data) {
    return (
      <section className="person-profile-page">
        <div className="state-panel state-panel--error">
          <h1>Nao foi possivel carregar seu perfil.</h1>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            <RefreshCcw size={17} aria-hidden="true" />
            Tentar novamente
          </button>
        </div>
      </section>
    )
  }

  if (!data.person_linked || !person) {
    return (
      <section className="person-profile-page">
        <div className="page-heading">
          <div>
            <h1>Meu Perfil</h1>
            <p className="page-heading__description">Dados pessoais vinculados ao seu acesso.</p>
          </div>
        </div>
        <div className="state-panel">
          <h2>Seu acesso ainda nao esta vinculado a uma pessoa.</h2>
          <p>Procure a Secretaria para revisar seu cadastro.</p>
        </div>
      </section>
    )
  }

  return (
    <section className="person-profile-page">
      <div className="page-heading">
        <div>
          <h1>Meu Perfil</h1>
          <p className="page-heading__description">Atualize seu celular/WhatsApp e mantenha sua foto visivel para a equipe.</p>
        </div>
      </div>

      {message ? <div className="form-alert form-alert--success" role="status">{message}</div> : null}
      {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

      <section className="profile-header">
        <div className="my-profile-photo" aria-hidden="true">
          {photoUrl ? <img src={photoUrl} alt="" /> : <span>{initials(displayName)}</span>}
        </div>
        <div className="profile-header__identity">
          <h1>{displayName}</h1>
          <p>{person.email || data.account.email || data.account.username}</p>
        </div>
        <div className="profile-actions">
          <label className="button button--secondary my-profile-upload">
            <Camera size={17} aria-hidden="true" />
            Trocar foto
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              disabled={isSaving}
              onChange={(event) => handlePhotoChange(event.target.files?.[0])}
            />
          </label>
          {person.photo_url ? (
            <button
              className="button button--secondary"
              type="button"
              disabled={isSaving}
              onClick={() => void runAction(() => mutations.deletePhoto.mutateAsync(), 'Foto removida.')}
            >
              <Trash2 size={17} aria-hidden="true" />
              Remover foto
            </button>
          ) : null}
        </div>
      </section>
      {photoError ? <div className="form-alert form-alert--error" role="alert">{photoError}</div> : null}

      <div className="profile-content">
        <section className="profile-section">
          <h2>Dados pessoais</h2>
          <dl className="profile-details">
            <div className="profile-detail"><dt>Nome completo</dt><dd>{person.full_name}</dd></div>
            <div className="profile-detail"><dt>Nome preferido</dt><dd>{person.preferred_name || '-'}</dd></div>
            <div className="profile-detail"><dt>Nascimento</dt><dd>{formatDate(person.birth_date)}</dd></div>
            <div className="profile-detail"><dt>Status cadastral</dt><dd>{statusLabel(person.status)}</dd></div>
          </dl>
        </section>

        <section className="profile-section">
          <h2>Contato</h2>
          <form className="department-inline-form my-profile-form" onSubmit={handleSubmit}>
            <label className="form-field">
              <span>Celular / WhatsApp</span>
              <input
                value={phone}
                onChange={(event) => setPhoneDraft({ personId: person.id, value: formatBrazilianMobile(event.target.value) })}
                aria-invalid={Boolean(phoneError)}
                placeholder="(81) 99999-9999"
              />
              {phoneError ? <span className="field-error">{phoneError}</span> : null}
            </label>
            <button className="button button--primary" type="submit" disabled={isSaving}>
              <Save size={17} aria-hidden="true" />
              {mutations.update.isPending ? 'Salvando...' : 'Salvar WhatsApp'}
            </button>
          </form>
        </section>

        <section className="profile-section">
          <h2>Igreja</h2>
          <dl className="profile-details">
            <div className="profile-detail"><dt>Jornada</dt><dd>{data.church?.has_church_journey ? 'Iniciada' : 'Nao iniciada'}</dd></div>
            <div className="profile-detail"><dt>Membresia</dt><dd>{statusLabel(data.church?.membership_status)}</dd></div>
            <div className="profile-detail"><dt>Membro desde</dt><dd>{formatDate(data.church?.member_since)}</dd></div>
            <div className="profile-detail"><dt>Discipulado</dt><dd>{data.church?.discipleship_completed ? 'Concluido' : 'Nao concluido'}</dd></div>
          </dl>
        </section>

        <section className="profile-section">
          <div className="section-heading-row">
            <h2>Departamentos</h2>
          </div>
          {departments.length > 0 ? (
            <div className="my-profile-departments">
              {departments.map((membership) => (
                <article className="identity-option" key={membership.id}>
                  <UserRound size={18} aria-hidden="true" />
                  <span>
                    <strong>{membership.department.name}</strong>
                    <span>{membership.role.name} desde {formatDate(membership.joined_at)}</span>
                  </span>
                </article>
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

export default MyProfilePage
