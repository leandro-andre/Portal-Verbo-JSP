import { useCallback, useEffect, useRef, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { Send } from 'lucide-react'
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

type SetError = UseFormSetError<AccessRequestFormValues>

function AccessRequestPage() {
  const createRequest = useCreateAccessRequest()
  const [isSuccess, setIsSuccess] = useState(false)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [pendingRequestError, setPendingRequestError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<AccessRequestValidationError | null>(null)
  const appliedApiErrorsRef = useRef<AccessRequestValidationError | null>(null)
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
    setError,
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
        setPendingRequestError('Ja existe uma solicitacao pendente para este e-mail ou telefone.')
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
                  {...register('phone')}
                />
                {errors.phone ? (
                  <span className="field-error" id="access_phone-error">
                    {errors.phone.message}
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
