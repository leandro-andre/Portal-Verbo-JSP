import { useEffect } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { AlertTriangle, ArrowLeft, Save } from 'lucide-react'
import { useForm, type UseFormSetError } from 'react-hook-form'
import type { PossibleDuplicateResponse } from '../../types/person'
import {
  personCreateDefaultValues,
  personCreateSchema,
  type PersonCreateFormData,
  type PersonCreateFormValues,
} from '../../schemas/person'

type PersonFormProps = {
  duplicate: PossibleDuplicateResponse | null
  generalError: string | null
  isSubmitting: boolean
  onCancel: () => void
  onConfirmDuplicate: () => void
  onDuplicateBack: () => void
  onSubmit: (values: PersonCreateFormData) => void
  setApiFieldError: (setError: UseFormSetError<PersonCreateFormValues>) => void
}

function formatBirthDate(value: string) {
  if (!value) {
    return '-'
  }

  const [year, month, day] = value.split('-')
  return year && month && day ? `${day}/${month}/${year}` : value
}

function PersonForm({
  duplicate,
  generalError,
  isSubmitting,
  onCancel,
  onConfirmDuplicate,
  onDuplicateBack,
  onSubmit,
  setApiFieldError,
}: PersonFormProps) {
  const {
    formState: { errors },
    handleSubmit,
    register,
    setError,
  } = useForm<PersonCreateFormValues, unknown, PersonCreateFormData>({
    defaultValues: personCreateDefaultValues,
    resolver: zodResolver(personCreateSchema),
  })

  useEffect(() => {
    setApiFieldError(setError)
  }, [setApiFieldError, setError])

  return (
    <form className="person-form" onSubmit={(event) => void handleSubmit(onSubmit)(event)}>
      {generalError ? (
        <div className="form-alert form-alert--error" role="alert">
          {generalError}
        </div>
      ) : null}

      {duplicate ? (
        <div className="duplicate-panel" role="alert" aria-live="assertive">
          <div className="duplicate-panel__heading">
            <AlertTriangle size={20} aria-hidden="true" />
            <div>
              <h2>Possivel cadastro existente</h2>
              <p>{duplicate.message}</p>
            </div>
          </div>

          <div className="duplicate-panel__list" aria-label="Pessoas possivelmente duplicadas">
            {duplicate.candidates.map((candidate) => (
              <div className="duplicate-candidate" key={candidate.id}>
                <strong>{candidate.display_name}</strong>
                <span>{candidate.full_name}</span>
                <span>{formatBirthDate(candidate.birth_date)}</span>
              </div>
            ))}
          </div>

          <div className="form-actions">
            <button className="button button--secondary" type="button" onClick={onDuplicateBack}>
              Voltar ao formulario
            </button>
            <button
              className="button button--primary"
              type="button"
              disabled={isSubmitting}
              onClick={onConfirmDuplicate}
            >
              <Save size={17} aria-hidden="true" />
              {isSubmitting ? 'Cadastrando...' : 'Cadastrar mesmo assim'}
            </button>
          </div>
        </div>
      ) : null}

      <fieldset className="form-section" disabled={isSubmitting || Boolean(duplicate)}>
        <legend>Dados pessoais</legend>

        <div className="form-grid">
          <div className="field-group field-group--wide">
            <label htmlFor="full_name">Nome completo *</label>
            <input
              id="full_name"
              type="text"
              autoComplete="name"
              aria-invalid={Boolean(errors.full_name)}
              aria-describedby={errors.full_name ? 'full_name-error' : undefined}
              {...register('full_name')}
            />
            {errors.full_name ? (
              <span className="field-error" id="full_name-error">
                {errors.full_name.message}
              </span>
            ) : null}
          </div>

          <div className="field-group">
            <label htmlFor="preferred_name">Nome preferido</label>
            <input
              id="preferred_name"
              type="text"
              autoComplete="nickname"
              aria-invalid={Boolean(errors.preferred_name)}
              aria-describedby={errors.preferred_name ? 'preferred_name-error' : undefined}
              {...register('preferred_name')}
            />
            {errors.preferred_name ? (
              <span className="field-error" id="preferred_name-error">
                {errors.preferred_name.message}
              </span>
            ) : null}
          </div>

          <div className="field-group">
            <label htmlFor="birth_date">Data de nascimento *</label>
            <input
              id="birth_date"
              type="date"
              aria-invalid={Boolean(errors.birth_date)}
              aria-describedby={errors.birth_date ? 'birth_date-error' : undefined}
              {...register('birth_date')}
            />
            {errors.birth_date ? (
              <span className="field-error" id="birth_date-error">
                {errors.birth_date.message}
              </span>
            ) : null}
          </div>
        </div>
      </fieldset>

      <fieldset className="form-section" disabled={isSubmitting || Boolean(duplicate)}>
        <legend>Contato</legend>

        <div className="form-grid">
          <div className="field-group">
            <label htmlFor="email">E-mail</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              aria-invalid={Boolean(errors.email)}
              aria-describedby={errors.email ? 'email-error' : undefined}
              {...register('email')}
            />
            {errors.email ? (
              <span className="field-error" id="email-error">
                {errors.email.message}
              </span>
            ) : null}
          </div>

          <div className="field-group">
            <label htmlFor="phone">Telefone</label>
            <input
              id="phone"
              type="tel"
              autoComplete="tel"
              aria-invalid={Boolean(errors.phone)}
              aria-describedby={errors.phone ? 'phone-error' : undefined}
              {...register('phone')}
            />
            {errors.phone ? (
              <span className="field-error" id="phone-error">
                {errors.phone.message}
              </span>
            ) : null}
          </div>
        </div>
      </fieldset>

      <div className="form-actions">
        <button className="button button--secondary" type="button" onClick={onCancel}>
          <ArrowLeft size={17} aria-hidden="true" />
          Cancelar
        </button>
        <button className="button button--primary" type="submit" disabled={isSubmitting || Boolean(duplicate)}>
          <Save size={17} aria-hidden="true" />
          {isSubmitting ? 'Salvando...' : 'Salvar pessoa'}
        </button>
      </div>
    </form>
  )
}

export default PersonForm
