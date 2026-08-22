import { useCallback, useEffect, useRef, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff, LogIn, Send } from 'lucide-react'
import { useForm, type UseFormSetError } from 'react-hook-form'
import {
  AccessRequestValidationError,
  PendingAccessRequestExistsError,
} from '../api/accessRequests'
import { useCreateAccessRequest } from '../hooks/useAccessRequests'
import {
  accessRequestDefaultValues,
  accessRequestSchema,
  type AccessRequestFormData,
  type AccessRequestFormValues,
} from '../schemas/accessRequest'
import { Link } from 'react-router-dom'

type SetError = UseFormSetError<AccessRequestFormValues>

function onlyDigits(value: string) {
  return value.replace(/\D/g, '')
}

function formatBrazilianPhone(value: string) {
  const digits = onlyDigits(value).slice(0, 11)
  if (digits.length <= 2) {
    return digits ? `(${digits}` : ''
  }
  if (digits.length <= 6) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2)}`
  }
  if (digits.length <= 10) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`
  }
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
}

function AccessRequestPage() {
  const createRequest = useCreateAccessRequest()
  const [isSuccess, setIsSuccess] = useState(false)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [pendingRequestError, setPendingRequestError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<AccessRequestValidationError | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false)
  const appliedApiErrorsRef = useRef<AccessRequestValidationError | null>(null)
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
    setError,
    setValue,
  } = useForm<AccessRequestFormValues, unknown, AccessRequestFormData>({
    defaultValues: accessRequestDefaultValues,
    resolver: zodResolver(accessRequestSchema),
  })

  const setApiFieldError = useCallback(
    (applyError: SetError) => {
      if (!apiValidationErrors || appliedApiErrorsRef.current === apiValidationErrors) {
        return
      }

      appliedApiErrorsRef.current = apiValidationErrors
      Object.entries(apiValidationErrors.fieldErrors).forEach(([field, messages]) => {
        const message = messages?.[0]

        if (message) {
          applyError(field as keyof AccessRequestFormValues, { message, type: 'server' })
        }
      })
    },
    [apiValidationErrors],
  )

  useEffect(() => {
    setApiFieldError(setError)
  }, [setApiFieldError, setError])

  const onSubmit = async (values: AccessRequestFormData) => {
    setGeneralError(null)
    setPendingRequestError(null)
    setApiValidationErrors(null)
    appliedApiErrorsRef.current = null

    try {
      await createRequest.mutateAsync(values)
      setIsSuccess(true)
      reset(accessRequestDefaultValues)
    } catch (error) {
      if (error instanceof PendingAccessRequestExistsError) {
        if (error.details.code === 'USERNAME_ALREADY_EXISTS') {
          setError('username', {
            message: 'Este nome de usuario ja esta sendo utilizado.',
            type: 'server',
          })
        } else {
          setPendingRequestError('Ja existe uma solicitacao pendente para este e-mail ou telefone.')
        }
        return
      }

      if (error instanceof AccessRequestValidationError) {
        setApiValidationErrors(error)
        return
      }

      setGeneralError('Nao foi possivel enviar sua solicitacao. Tente novamente.')
    }
  }

  return (
    <main className="public-access-page">
      <section className="access-request-shell" aria-labelledby="access-request-title">
        <div className="access-request-brand">
          <div className="access-request-brand__mark" aria-hidden="true">
            VV
          </div>
          <div>
            <strong>Verbo da Vida</strong>
            <span>Jardim Sao Paulo</span>
          </div>
        </div>

        {isSuccess ? (
          <div className="access-request-success" role="status">
            <h1>Solicitacao recebida</h1>
            <p>
              A Secretaria ira revisar seus dados. Voce recebera uma orientacao quando o acesso for aprovado.
            </p>
            <Link className="button button--secondary" to="/login">
              <LogIn size={17} aria-hidden="true" />
              Voltar para o login
            </Link>
          </div>
        ) : (
          <>
            <div className="access-request-heading">
              <h1 id="access-request-title">Quero me cadastrar</h1>
              <p>
                Informe seus dados para solicitar acesso ao Portal. A Secretaria ira revisar sua solicitacao antes da liberacao.
              </p>
            </div>

            <form className="access-request-form" onSubmit={(event) => void handleSubmit(onSubmit)(event)}>
              {pendingRequestError ? (
                <div className="form-alert form-alert--error" role="alert">
                  {pendingRequestError}
                </div>
              ) : null}

              {generalError ? (
                <div className="form-alert form-alert--error" role="alert">
                  {generalError}
                </div>
              ) : null}

              <div className="field-group">
                <label htmlFor="access_full_name">Nome completo *</label>
                <input
                  id="access_full_name"
                  type="text"
                  autoComplete="name"
                  aria-invalid={Boolean(errors.full_name)}
                  aria-describedby={errors.full_name ? 'access_full_name-error' : undefined}
                  {...register('full_name')}
                />
                {errors.full_name ? (
                  <span className="field-error" id="access_full_name-error">
                    {errors.full_name.message}
                  </span>
                ) : null}
              </div>

              <div className="field-group">
                <label htmlFor="access_birth_date">Data de nascimento *</label>
                <input
                  id="access_birth_date"
                  type="date"
                  aria-invalid={Boolean(errors.birth_date)}
                  aria-describedby={errors.birth_date ? 'access_birth_date-error' : undefined}
                  {...register('birth_date')}
                />
                {errors.birth_date ? (
                  <span className="field-error" id="access_birth_date-error">
                    {errors.birth_date.message}
                  </span>
                ) : null}
              </div>

              <div className="field-group">
                <label htmlFor="access_email">E-mail *</label>
                <input
                  id="access_email"
                  type="email"
                  autoComplete="email"
                  aria-invalid={Boolean(errors.email)}
                  aria-describedby={errors.email ? 'access_email-error' : undefined}
                  {...register('email')}
                />
                {errors.email ? (
                  <span className="field-error" id="access_email-error">
                    {errors.email.message}
                  </span>
                ) : null}
              </div>

              <div className="field-group">
                <label htmlFor="access_phone">Telefone *</label>
                <input
                  id="access_phone"
                  type="tel"
                  autoComplete="tel"
                  aria-invalid={Boolean(errors.phone)}
                  aria-describedby={errors.phone ? 'access_phone-error' : undefined}
                  {...register('phone', {
                    onChange: (event) => {
                      setValue('phone', formatBrazilianPhone(event.target.value), {
                        shouldDirty: true,
                        shouldValidate: true,
                      })
                    },
                  })}
                />
                {errors.phone ? (
                  <span className="field-error" id="access_phone-error">
                    {errors.phone.message}
                  </span>
                ) : null}
              </div>

              <div className="field-group">
                <label htmlFor="access_username">Usuario *</label>
                <input
                  id="access_username"
                  type="text"
                  autoComplete="username"
                  aria-invalid={Boolean(errors.username)}
                  aria-describedby={errors.username ? 'access_username-error' : undefined}
                  {...register('username')}
                />
                {errors.username ? (
                  <span className="field-error" id="access_username-error">
                    {errors.username.message}
                  </span>
                ) : null}
              </div>

              <div className="field-group">
                <label htmlFor="access_password">Senha *</label>
                <div className="password-field">
                  <input
                    id="access_password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    aria-invalid={Boolean(errors.password)}
                    aria-describedby={errors.password ? 'access_password-error' : undefined}
                    {...register('password')}
                  />
                  <button
                    aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                    className="icon-button"
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                  >
                    {showPassword ? <EyeOff size={17} aria-hidden="true" /> : <Eye size={17} aria-hidden="true" />}
                  </button>
                </div>
                {errors.password ? (
                  <span className="field-error" id="access_password-error">
                    {errors.password.message}
                  </span>
                ) : null}
              </div>

              <div className="field-group">
                <label htmlFor="access_password_confirm">Confirmar senha *</label>
                <div className="password-field">
                  <input
                    id="access_password_confirm"
                    type={showPasswordConfirm ? 'text' : 'password'}
                    autoComplete="new-password"
                    aria-invalid={Boolean(errors.password_confirm)}
                    aria-describedby={errors.password_confirm ? 'access_password_confirm-error' : undefined}
                    {...register('password_confirm')}
                  />
                  <button
                    aria-label={showPasswordConfirm ? 'Ocultar confirmacao de senha' : 'Mostrar confirmacao de senha'}
                    className="icon-button"
                    type="button"
                    onClick={() => setShowPasswordConfirm((current) => !current)}
                  >
                    {showPasswordConfirm ? <EyeOff size={17} aria-hidden="true" /> : <Eye size={17} aria-hidden="true" />}
                  </button>
                </div>
                {errors.password_confirm ? (
                  <span className="field-error" id="access_password_confirm-error">
                    {errors.password_confirm.message}
                  </span>
                ) : null}
              </div>

              <button className="button button--primary" type="submit" disabled={createRequest.isPending}>
                <Send size={17} aria-hidden="true" />
                {createRequest.isPending ? 'Enviando...' : 'Enviar solicitacao'}
              </button>
            </form>
          </>
        )}
      </section>
    </main>
  )
}

export default AccessRequestPage
