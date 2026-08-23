import { useEffect } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, Save } from 'lucide-react'
import { useForm, type UseFormSetError } from 'react-hook-form'
import {
  departmentCreateDefaultValues,
  departmentCreateSchema,
  departmentUpdateSchema,
  type DepartmentCreateFormData,
  type DepartmentCreateFormValues,
  type DepartmentUpdateFormData,
  type DepartmentUpdateFormValues,
} from '../../schemas/department'

type DepartmentFormValues = DepartmentCreateFormValues | DepartmentUpdateFormValues
type DepartmentFormData = DepartmentCreateFormData | DepartmentUpdateFormData

type DepartmentFormProps = {
  codeReadOnlyValue?: string
  generalError: string | null
  initialValues?: DepartmentFormValues
  isSubmitting: boolean
  mode: 'create' | 'edit'
  onCancel: () => void
  onSubmit: (values: DepartmentFormData) => void
  setApiFieldError: (setError: UseFormSetError<DepartmentFormValues>) => void
  submitLabel: string
  submittingLabel: string
}

function DepartmentForm({
  codeReadOnlyValue,
  generalError,
  initialValues,
  isSubmitting,
  mode,
  onCancel,
  onSubmit,
  setApiFieldError,
  submitLabel,
  submittingLabel,
}: DepartmentFormProps) {
  const schema = mode === 'create' ? departmentCreateSchema : departmentUpdateSchema
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
    setError,
  } = useForm<DepartmentFormValues, unknown, DepartmentFormData>({
    defaultValues: initialValues ?? departmentCreateDefaultValues,
    resolver: zodResolver(schema),
  })

  useEffect(() => {
    setApiFieldError(setError)
  }, [setApiFieldError, setError])

  useEffect(() => {
    if (initialValues) {
      reset(initialValues)
    }
  }, [initialValues, reset])

  return (
    <form className="person-form" onSubmit={(event) => void handleSubmit(onSubmit)(event)}>
      {generalError ? (
        <div className="form-alert form-alert--error" role="alert">
          {generalError}
        </div>
      ) : null}

      <fieldset className="form-section" disabled={isSubmitting}>
        <legend>Departamento</legend>

        <div className="form-grid">
          <div className="field-group field-group--wide">
            <label htmlFor="nome">Nome *</label>
            <input
              id="nome"
              type="text"
              aria-invalid={Boolean(errors.nome)}
              aria-describedby={errors.nome ? 'nome-error' : undefined}
              {...register('nome')}
            />
            {errors.nome ? (
              <span className="field-error" id="nome-error">
                {errors.nome.message}
              </span>
            ) : null}
          </div>

          {mode === 'create' ? (
            <div className="field-group field-group--wide">
              <label htmlFor="codigo">Codigo *</label>
              <input
                id="codigo"
                type="text"
                aria-invalid={Boolean('codigo' in errors && errors.codigo)}
                aria-describedby={'codigo' in errors && errors.codigo ? 'codigo-error' : undefined}
                {...register('codigo')}
              />
              {'codigo' in errors && errors.codigo ? (
                <span className="field-error" id="codigo-error">
                  {errors.codigo.message}
                </span>
              ) : null}
            </div>
          ) : (
            <div className="field-group field-group--wide">
              <label htmlFor="codigo-readonly">Codigo</label>
              <input id="codigo-readonly" type="text" value={codeReadOnlyValue ?? ''} readOnly />
            </div>
          )}

          <div className="field-group field-group--wide">
            <label htmlFor="descricao">Descricao</label>
            <textarea
              id="descricao"
              rows={5}
              aria-invalid={Boolean(errors.descricao)}
              aria-describedby={errors.descricao ? 'descricao-error' : undefined}
              {...register('descricao')}
            />
            {errors.descricao ? (
              <span className="field-error" id="descricao-error">
                {errors.descricao.message}
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
        <button className="button button--primary" type="submit" disabled={isSubmitting}>
          <Save size={17} aria-hidden="true" />
          {isSubmitting ? submittingLabel : submitLabel}
        </button>
      </div>
    </form>
  )
}

export default DepartmentForm
