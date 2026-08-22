import { useCallback, useMemo, useRef, useState } from 'react'
import type { UseFormSetError } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiHttpError, ApiValidationError, PossibleDuplicateError } from '../api/people'
import PersonForm from '../components/people/PersonForm'
import { usePerson, useUpdatePerson } from '../hooks/usePeople'
import type { PersonCreateFormData, PersonCreateFormValues } from '../schemas/person'
import type { PossibleDuplicateResponse, UpdatePersonInput } from '../types/person'
import { formatBrazilianMobile } from '../utils/phone'

type SetError = UseFormSetError<PersonCreateFormValues>

function toPayload(values: PersonCreateFormData): UpdatePersonInput {
  return {
    full_name: values.full_name,
    preferred_name: values.preferred_name,
    birth_date: values.birth_date,
    email: values.email,
    phone: values.phone,
  }
}

function PersonEditPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const personId = Number(id)
  const isValidId = Number.isInteger(personId) && personId > 0
  const { data: person, error, isError, isLoading, refetch } = usePerson(personId)
  const updatePerson = useUpdatePerson(personId)
  const [duplicate, setDuplicate] = useState<PossibleDuplicateResponse | null>(null)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<ApiValidationError | null>(null)
  const lastPayloadRef = useRef<UpdatePersonInput | null>(null)
  const appliedApiErrorsRef = useRef<ApiValidationError | null>(null)
  const isNotFound = !isValidId || (error instanceof ApiHttpError && error.status === 404)

  const initialValues = useMemo<PersonCreateFormValues | undefined>(() => {
    if (!person) {
      return undefined
    }

    return {
      full_name: person.full_name,
      preferred_name: person.preferred_name,
      birth_date: person.birth_date,
      email: person.email,
      phone: formatBrazilianMobile(person.phone),
    }
  }, [person])

  const handleSuccess = () => {
    navigate(`/pessoas/${personId}`, {
      state: { successMessage: 'Dados atualizados com sucesso.' },
    })
  }

  const handleError = (mutationError: unknown) => {
    if (mutationError instanceof PossibleDuplicateError) {
      setDuplicate(mutationError.details)
      setGeneralError(null)
      return
    }

    if (mutationError instanceof ApiValidationError) {
      setApiValidationErrors(mutationError)
      setGeneralError(null)
      return
    }

    setGeneralError('Nao foi possivel salvar as alteracoes. Tente novamente.')
  }

  const handleSubmit = async (values: PersonCreateFormData) => {
    const payload = toPayload(values)
    lastPayloadRef.current = payload
    setDuplicate(null)
    setGeneralError(null)
    setApiValidationErrors(null)
    appliedApiErrorsRef.current = null

    try {
      await updatePerson.mutateAsync(payload)
      handleSuccess()
    } catch (mutationError) {
      handleError(mutationError)
    }
  }

  const handleConfirmDuplicate = async () => {
    if (!lastPayloadRef.current) {
      return
    }

    setGeneralError(null)

    try {
      await updatePerson.mutateAsync({
        ...lastPayloadRef.current,
        allow_possible_duplicate: true,
      })
      handleSuccess()
    } catch (mutationError) {
      handleError(mutationError)
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
      ) : person && initialValues ? (
        <>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link to="/pessoas">Pessoas</Link>
            <span aria-hidden="true">/</span>
            <Link to={`/pessoas/${person.id}`}>{person.display_name}</Link>
            <span aria-hidden="true">/</span>
            <strong>Editar</strong>
          </nav>

          <div className="page-heading page-heading--compact">
            <div>
              <h1>Editar pessoa</h1>
              <p className="page-heading__description">
                Atualize os dados cadastrais da pessoa.
              </p>
            </div>
          </div>

          <PersonForm
            duplicate={duplicate}
            duplicateConfirmLabel="Salvar mesmo assim"
            generalError={generalError}
            initialValues={initialValues}
            isSubmitting={updatePerson.isPending}
            onCancel={() => navigate(`/pessoas/${person.id}`)}
            onConfirmDuplicate={() => void handleConfirmDuplicate()}
            onDuplicateBack={() => setDuplicate(null)}
            onSubmit={(values) => void handleSubmit(values)}
            setApiFieldError={setApiFieldError}
            submitLabel="Salvar alteracoes"
            submittingLabel="Salvando..."
          />
        </>
      ) : null}
    </section>
  )
}

export default PersonEditPage
