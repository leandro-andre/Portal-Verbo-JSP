import { useCallback, useRef, useState } from 'react'
import type { UseFormSetError } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { DepartmentApiValidationError } from '../api/departments'
import DepartmentForm from '../components/departments/DepartmentForm'
import { useCreateDepartment } from '../hooks/useDepartments'
import type {
  DepartmentCreateFormData,
  DepartmentCreateFormValues,
} from '../schemas/department'
import type { CreateDepartmentInput } from '../types/department'

type SetError = UseFormSetError<DepartmentCreateFormValues>

function DepartmentCreatePage() {
  const navigate = useNavigate()
  const createDepartment = useCreateDepartment()
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<DepartmentApiValidationError | null>(null)
  const appliedApiErrorsRef = useRef<DepartmentApiValidationError | null>(null)

  const setApiFieldError = useCallback(
    (setError: SetError) => {
      if (!apiValidationErrors || appliedApiErrorsRef.current === apiValidationErrors) {
        return
      }

      appliedApiErrorsRef.current = apiValidationErrors
      Object.entries(apiValidationErrors.fieldErrors).forEach(([field, messages]) => {
        const message = messages?.[0]

        if (message) {
          setError(field as keyof DepartmentCreateFormValues, { message, type: 'server' })
        }
      })
    },
    [apiValidationErrors],
  )

  const handleSubmit = async (values: DepartmentCreateFormData) => {
    const payload: CreateDepartmentInput = values
    setGeneralError(null)
    setApiValidationErrors(null)
    appliedApiErrorsRef.current = null

    try {
      const department = await createDepartment.mutateAsync(payload)
      navigate(`/departamentos/${department.id}`, {
        state: { successMessage: 'Departamento criado com sucesso.' },
      })
    } catch (error) {
      if (error instanceof DepartmentApiValidationError) {
        setApiValidationErrors(error)
        return
      }
      setGeneralError('Nao foi possivel criar o departamento.')
    }
  }

  return (
    <section className="person-create-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <span>Departamentos</span>
        <span aria-hidden="true">/</span>
        <strong>Novo departamento</strong>
      </nav>

      <div className="page-heading page-heading--compact">
        <div>
          <h1>Novo departamento</h1>
          <p className="page-heading__description">Cadastre um departamento da igreja.</p>
        </div>
      </div>

      <DepartmentForm
        generalError={generalError}
        isSubmitting={createDepartment.isPending}
        mode="create"
        onCancel={() => navigate('/departamentos')}
        onSubmit={(values) => void handleSubmit(values as DepartmentCreateFormData)}
        setApiFieldError={setApiFieldError}
        submitLabel="Criar departamento"
        submittingLabel="Criando..."
      />
    </section>
  )
}

export default DepartmentCreatePage
