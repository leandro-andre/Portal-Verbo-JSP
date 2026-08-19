import { useCallback, useRef, useState } from 'react'
import type { UseFormSetError } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { ApiValidationError, PossibleDuplicateError } from '../api/people'
import PersonForm from '../components/people/PersonForm'
import { useCreatePerson } from '../hooks/usePeople'
import type { PersonCreateFormData, PersonCreateFormValues } from '../schemas/person'
import type { CreatePersonInput, PossibleDuplicateResponse } from '../types/person'

type SetError = UseFormSetError<PersonCreateFormValues>

function toPayload(values: PersonCreateFormData): CreatePersonInput {
  return {
    full_name: values.full_name,
    preferred_name: values.preferred_name,
    birth_date: values.birth_date,
    email: values.email,
    phone: values.phone,
  }
}

function PersonCreatePage() {
  const navigate = useNavigate()
  const createPerson = useCreatePerson()
  const [duplicate, setDuplicate] = useState<PossibleDuplicateResponse | null>(null)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<ApiValidationError | null>(null)
  const lastPayloadRef = useRef<CreatePersonInput | null>(null)
  const appliedApiErrorsRef = useRef<ApiValidationError | null>(null)

  const handleSuccess = () => {
    navigate('/pessoas', {
      state: { successMessage: 'Pessoa cadastrada com sucesso.' },
    })
  }

  const handleError = (error: unknown) => {
    if (error instanceof PossibleDuplicateError) {
      setDuplicate(error.details)
      setGeneralError(null)
      return
    }

    if (error instanceof ApiValidationError) {
      setApiValidationErrors(error)
      setGeneralError(null)
      return
    }

    setGeneralError('Nao foi possivel cadastrar a pessoa. Tente novamente.')
  }

  const handleSubmit = async (values: PersonCreateFormData) => {
    const payload = toPayload(values)
    lastPayloadRef.current = payload
    setDuplicate(null)
    setGeneralError(null)
    setApiValidationErrors(null)
    appliedApiErrorsRef.current = null

    try {
      await createPerson.mutateAsync(payload)
      handleSuccess()
    } catch (error) {
      handleError(error)
    }
  }

  const handleConfirmDuplicate = async () => {
    if (!lastPayloadRef.current) {
      return
    }

    setGeneralError(null)

    try {
      await createPerson.mutateAsync({
        ...lastPayloadRef.current,
        allow_possible_duplicate: true,
      })
      handleSuccess()
    } catch (error) {
      handleError(error)
    }
  }

  const setApiFieldError = useCallback(
    (setError: SetError) => {
      if (!apiValidationErrors || appliedApiErrorsRef.current === apiValidationErrors) {
        return
      }

      appliedApiErrorsRef.current = apiValidationErrors
      Object.entries(apiValidationErrors.fieldErrors).forEach(([field, messages]) => {
        const message = messages?.[0]

        if (message) {
          setError(field as keyof PersonCreateFormValues, { message, type: 'server' })
        }
      })
    },
    [apiValidationErrors],
  )

  return (
    <section className="person-create-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <span>Pessoas</span>
        <span aria-hidden="true">/</span>
        <strong>Nova pessoa</strong>
      </nav>

      <div className="page-heading page-heading--compact">
        <div>
          <h1>Nova pessoa</h1>
          <p className="page-heading__description">
            Cadastre uma nova pessoa no Portal.
          </p>
        </div>
      </div>

      <PersonForm
        duplicate={duplicate}
        generalError={generalError}
        isSubmitting={createPerson.isPending}
        onCancel={() => navigate('/pessoas')}
        onConfirmDuplicate={() => void handleConfirmDuplicate()}
        onDuplicateBack={() => setDuplicate(null)}
        onSubmit={(values) => void handleSubmit(values)}
        setApiFieldError={setApiFieldError}
      />
    </section>
  )
}

export default PersonCreatePage
