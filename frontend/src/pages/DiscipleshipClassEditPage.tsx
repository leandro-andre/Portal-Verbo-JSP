import { useCallback, useMemo, useRef, useState } from 'react'
import type { UseFormSetError } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { DiscipleshipApiValidationError, DiscipleshipHttpError } from '../api/discipleship'
import DiscipleshipClassForm from '../components/discipleship/DiscipleshipClassForm'
import { useDiscipleshipClass, useUpdateDiscipleshipClass } from '../hooks/useDiscipleshipClasses'
import { usePeople } from '../hooks/usePeople'
import type {
  DiscipleshipClassFormData,
  DiscipleshipClassFormValues,
} from '../schemas/discipleshipClass'
import type { UpdateDiscipleshipClassInput } from '../types/discipleship'

type SetError = UseFormSetError<DiscipleshipClassFormValues>

function toPayload(values: DiscipleshipClassFormData): UpdateDiscipleshipClassInput {
  return {
    name: values.name,
    teacher_id: values.teacher_id,
    start_date: values.start_date,
    expected_end_date: values.expected_end_date,
    planned_sessions: values.planned_sessions,
  }
}

function DiscipleshipClassEditPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const classId = Number(id)
  const isValidId = Number.isInteger(classId) && classId > 0
  const { data: discipleshipClass, error, isError, isLoading, refetch } = useDiscipleshipClass(classId)
  const { data: people = [] } = usePeople()
  const updateClass = useUpdateDiscipleshipClass(classId)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<DiscipleshipApiValidationError | null>(null)
  const appliedApiErrorsRef = useRef<DiscipleshipApiValidationError | null>(null)
  const isNotFound = !isValidId || (error instanceof DiscipleshipHttpError && error.status === 404)
  const isClosed = discipleshipClass?.status === 'COMPLETED' || discipleshipClass?.status === 'CANCELLED'

  const initialValues = useMemo<DiscipleshipClassFormValues | undefined>(() => {
    if (!discipleshipClass) {
      return undefined
    }

    return {
      name: discipleshipClass.name,
      teacher_id: discipleshipClass.teacher.id,
      start_date: discipleshipClass.start_date,
      expected_end_date: discipleshipClass.expected_end_date,
      planned_sessions: discipleshipClass.planned_sessions,
    }
  }, [discipleshipClass])

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
      await updateClass.mutateAsync(toPayload(values))
      navigate(`/discipulado/${classId}`, {
        state: { successMessage: 'Turma atualizada com sucesso.' },
      })
    } catch (error) {
      if (error instanceof DiscipleshipApiValidationError) {
        setApiValidationErrors(error)
        return
      }
      setGeneralError('Nao foi possivel atualizar a turma.')
    }
  }

  return (
    <section className="person-create-page">
      {isLoading && isValidId ? (
        <div className="state-panel"><h1>Carregando turma...</h1><p>Aguarde enquanto os dados sao carregados.</p></div>
      ) : isNotFound ? (
        <div className="state-panel">
          <h1>Turma nao encontrada</h1>
          <p>Nao encontramos a turma solicitada.</p>
          <Link className="button button--secondary" to="/discipulado"><ArrowLeft size={17} aria-hidden="true" />Voltar</Link>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h1>Nao foi possivel carregar a turma.</h1>
          <p>Verifique a conexao com o backend e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : discipleshipClass && initialValues ? (
        <>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link to="/discipulado">Discipulado</Link>
            <span aria-hidden="true">/</span>
            <Link to={`/discipulado/${discipleshipClass.id}`}>{discipleshipClass.name}</Link>
            <span aria-hidden="true">/</span>
            <strong>Editar</strong>
          </nav>

          <div className="page-heading page-heading--compact">
            <div>
              <h1>Editar turma</h1>
              <p className="page-heading__description">Atualize os dados basicos da turma.</p>
            </div>
          </div>

          {isClosed ? (
            <div className="state-panel state-panel--error">
              <h2>Esta turma nao pode ser editada.</h2>
              <p>Turmas concluidas ou canceladas permanecem somente para consulta.</p>
            </div>
          ) : (
            <DiscipleshipClassForm
              generalError={generalError}
              initialValues={initialValues}
              isSubmitting={updateClass.isPending}
              onCancel={() => navigate(`/discipulado/${classId}`)}
              onSubmit={(values) => void handleSubmit(values)}
              setApiFieldError={setApiFieldError}
              submitLabel="Salvar turma"
              submittingLabel="Salvando..."
              teachers={people}
            />
          )}
        </>
      ) : null}
    </section>
  )
}

export default DiscipleshipClassEditPage
