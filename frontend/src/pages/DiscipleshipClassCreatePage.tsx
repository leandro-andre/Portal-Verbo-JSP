import { useCallback, useRef, useState } from 'react'
import type { UseFormSetError } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { DiscipleshipApiValidationError } from '../api/discipleship'
import DiscipleshipClassForm from '../components/discipleship/DiscipleshipClassForm'
import { useCreateDiscipleshipClass } from '../hooks/useDiscipleshipClasses'
import { usePeople } from '../hooks/usePeople'
import type {
  DiscipleshipClassFormData,
  DiscipleshipClassFormValues,
} from '../schemas/discipleshipClass'
import type { CreateDiscipleshipClassInput } from '../types/discipleship'

type SetError = UseFormSetError<DiscipleshipClassFormValues>

function toPayload(values: DiscipleshipClassFormData): CreateDiscipleshipClassInput {
  return {
    name: values.name,
    teacher_id: values.teacher_id,
    start_date: values.start_date,
    expected_end_date: values.expected_end_date,
    planned_sessions: values.planned_sessions,
  }
}

function DiscipleshipClassCreatePage() {
  const navigate = useNavigate()
  const createClass = useCreateDiscipleshipClass()
  const { data: people = [] } = usePeople()
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<DiscipleshipApiValidationError | null>(null)
  const appliedApiErrorsRef = useRef<DiscipleshipApiValidationError | null>(null)

  const setApiFieldError = useCallback(
    (setError: SetError) => {
      if (!apiValidationErrors || appliedApiErrorsRef.current === apiValidationErrors) {
        return
      }

      appliedApiErrorsRef.current = apiValidationErrors
      Object.entries(apiValidationErrors.fieldErrors).forEach(([field, messages]) => {
        const message = messages?.[0]

        if (message) {
          setError(field as keyof DiscipleshipClassFormValues, { message, type: 'server' })
        }
      })
    },
    [apiValidationErrors],
  )

  const handleSubmit = async (values: DiscipleshipClassFormData) => {
    setGeneralError(null)
    setApiValidationErrors(null)
    appliedApiErrorsRef.current = null

    try {
      const discipleshipClass = await createClass.mutateAsync(toPayload(values))
      navigate(`/discipulado/${discipleshipClass.id}`, {
        state: { successMessage: 'Turma criada com sucesso.' },
      })
    } catch (error) {
      if (error instanceof DiscipleshipApiValidationError) {
        setApiValidationErrors(error)
        return
      }
      setGeneralError('Nao foi possivel criar a turma. Tente novamente.')
    }
  }

  return (
    <section className="person-create-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <span>Discipulado</span>
        <span aria-hidden="true">/</span>
        <strong>Nova turma</strong>
      </nav>

      <div className="page-heading page-heading--compact">
        <div>
          <h1>Nova turma</h1>
          <p className="page-heading__description">Cadastre uma turma de discipulado.</p>
        </div>
      </div>

      <DiscipleshipClassForm
        generalError={generalError}
        isSubmitting={createClass.isPending}
        onCancel={() => navigate('/discipulado')}
        onSubmit={(values) => void handleSubmit(values)}
        setApiFieldError={setApiFieldError}
        submitLabel="Criar turma"
        submittingLabel="Criando..."
        teachers={people}
      />
    </section>
  )
}

export default DiscipleshipClassCreatePage
