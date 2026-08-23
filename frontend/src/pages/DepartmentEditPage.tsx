import { useCallback, useRef, useState } from 'react'
import type { UseFormSetError } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { DepartmentApiValidationError, DepartmentHttpError } from '../api/departments'
import DepartmentForm from '../components/departments/DepartmentForm'
import { useDepartment, useUpdateDepartment } from '../hooks/useDepartments'
import type {
  DepartmentUpdateFormData,
  DepartmentUpdateFormValues,
} from '../schemas/department'
import type { UpdateDepartmentInput } from '../types/department'

type SetError = UseFormSetError<DepartmentUpdateFormValues>

function DepartmentEditPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const departmentId = Number(id)
  const isValidId = Number.isInteger(departmentId) && departmentId > 0
  const { data: department, error, isError, isLoading, refetch } = useDepartment(departmentId)
  const updateDepartment = useUpdateDepartment(departmentId)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<DepartmentApiValidationError | null>(null)
  const appliedApiErrorsRef = useRef<DepartmentApiValidationError | null>(null)
  const isNotFound = !isValidId || (error instanceof DepartmentHttpError && error.status === 404)

  const setApiFieldError = useCallback(
    (setError: SetError) => {
      if (!apiValidationErrors || appliedApiErrorsRef.current === apiValidationErrors) {
        return
      }

      appliedApiErrorsRef.current = apiValidationErrors
      Object.entries(apiValidationErrors.fieldErrors).forEach(([field, messages]) => {
        const message = messages?.[0]

        if (message && field !== 'codigo') {
          setError(field as keyof DepartmentUpdateFormValues, { message, type: 'server' })
        }
      })
    },
    [apiValidationErrors],
  )

  const handleSubmit = async (values: DepartmentUpdateFormData) => {
    const payload: UpdateDepartmentInput = values
    setGeneralError(null)
    setApiValidationErrors(null)
    appliedApiErrorsRef.current = null

    try {
      await updateDepartment.mutateAsync(payload)
      navigate(`/departamentos/${departmentId}`, {
        state: { successMessage: 'Departamento atualizado com sucesso.' },
      })
    } catch (submitError) {
      if (submitError instanceof DepartmentApiValidationError) {
        setApiValidationErrors(submitError)
        return
      }
      setGeneralError('Nao foi possivel salvar as alteracoes.')
    }
  }

  return (
    <section className="person-create-page">
      {isLoading && isValidId ? (
        <div className="state-panel"><h1>Carregando departamento...</h1><p>Aguarde enquanto os dados sao carregados.</p></div>
      ) : isNotFound ? (
        <div className="state-panel">
          <h1>Departamento nao encontrado</h1>
          <p>Nao encontramos o departamento solicitado.</p>
          <Link className="button button--secondary" to="/departamentos">
            <ArrowLeft size={17} aria-hidden="true" />
            Voltar para Departamentos
          </Link>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h1>Nao foi possivel carregar o departamento.</h1>
          <p>Verifique a conexao com o backend e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            Tentar novamente
          </button>
        </div>
      ) : department ? (
        <>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link to="/departamentos">Departamentos</Link>
            <span aria-hidden="true">/</span>
            <Link to={`/departamentos/${department.id}`}>{department.nome}</Link>
            <span aria-hidden="true">/</span>
            <strong>Editar</strong>
          </nav>

          <div className="page-heading page-heading--compact">
            <div>
              <h1>Editar departamento</h1>
              <p className="page-heading__description">Atualize nome e descricao.</p>
            </div>
          </div>

          <DepartmentForm
            codeReadOnlyValue={department.codigo}
            generalError={generalError}
            initialValues={{
              nome: department.nome,
              descricao: department.descricao,
            }}
            isSubmitting={updateDepartment.isPending}
            mode="edit"
            onCancel={() => navigate(`/departamentos/${department.id}`)}
            onSubmit={(values) => void handleSubmit(values as DepartmentUpdateFormData)}
            setApiFieldError={setApiFieldError}
            submitLabel="Salvar departamento"
            submittingLabel="Salvando..."
          />
        </>
      ) : null}
    </section>
  )
}

export default DepartmentEditPage
