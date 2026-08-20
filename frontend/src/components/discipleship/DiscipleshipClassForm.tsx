import { useEffect } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, Save } from 'lucide-react'
import { useForm, type UseFormSetError } from 'react-hook-form'
import {
  discipleshipClassDefaultValues,
  discipleshipClassSchema,
  type DiscipleshipClassFormData,
  type DiscipleshipClassFormValues,
} from '../../schemas/discipleshipClass'
import type { Person } from '../../types/person'

type DiscipleshipClassFormProps = {
  generalError: string | null
  initialValues?: DiscipleshipClassFormValues
  isSubmitting: boolean
  onCancel: () => void
  onSubmit: (values: DiscipleshipClassFormData) => void
  setApiFieldError: (setError: UseFormSetError<DiscipleshipClassFormValues>) => void
  submitLabel: string
  submittingLabel: string
  teachers: Person[]
}

function DiscipleshipClassForm({
  generalError,
  initialValues,
  isSubmitting,
  onCancel,
  onSubmit,
  setApiFieldError,
  submitLabel,
  submittingLabel,
  teachers,
}: DiscipleshipClassFormProps) {
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
    setError,
  } = useForm<DiscipleshipClassFormValues, unknown, DiscipleshipClassFormData>({
    defaultValues: initialValues ?? discipleshipClassDefaultValues,
    resolver: zodResolver(discipleshipClassSchema),
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
        <legend>Turma</legend>

        <div className="form-grid">
          <div className="field-group field-group--wide">
            <label htmlFor="name">Nome *</label>
            <input
              id="name"
              type="text"
              aria-invalid={Boolean(errors.name)}
              aria-describedby={errors.name ? 'name-error' : undefined}
              {...register('name')}
            />
            {errors.name ? (
              <span className="field-error" id="name-error">
                {errors.name.message}
              </span>
            ) : null}
          </div>

          <div className="field-group field-group--wide">
            <label htmlFor="teacher_id">Professor *</label>
            <select
              id="teacher_id"
              aria-invalid={Boolean(errors.teacher_id)}
              aria-describedby={errors.teacher_id ? 'teacher_id-error' : undefined}
              {...register('teacher_id')}
            >
              <option value={0}>Selecione uma pessoa</option>
              {teachers.map((teacher) => (
                <option key={teacher.id} value={teacher.id}>
                  {teacher.display_name}
                </option>
              ))}
            </select>
            {errors.teacher_id ? (
              <span className="field-error" id="teacher_id-error">
                {errors.teacher_id.message}
              </span>
            ) : null}
          </div>

          <div className="field-group">
            <label htmlFor="start_date">Data de inicio *</label>
            <input
              id="start_date"
              type="date"
              aria-invalid={Boolean(errors.start_date)}
              aria-describedby={errors.start_date ? 'start_date-error' : undefined}
              {...register('start_date')}
            />
            {errors.start_date ? (
              <span className="field-error" id="start_date-error">
                {errors.start_date.message}
              </span>
            ) : null}
          </div>

          <div className="field-group">
            <label htmlFor="expected_end_date">Termino previsto *</label>
            <input
              id="expected_end_date"
              type="date"
              aria-invalid={Boolean(errors.expected_end_date)}
              aria-describedby={errors.expected_end_date ? 'expected_end_date-error' : undefined}
              {...register('expected_end_date')}
            />
            {errors.expected_end_date ? (
              <span className="field-error" id="expected_end_date-error">
                {errors.expected_end_date.message}
              </span>
            ) : null}
          </div>

          <div className="field-group">
            <label htmlFor="planned_sessions">Quantidade prevista de aulas *</label>
            <input
              id="planned_sessions"
              type="number"
              min={1}
              step={1}
              aria-invalid={Boolean(errors.planned_sessions)}
              aria-describedby={errors.planned_sessions ? 'planned_sessions-error' : undefined}
              {...register('planned_sessions')}
            />
            {errors.planned_sessions ? (
              <span className="field-error" id="planned_sessions-error">
                {errors.planned_sessions.message}
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

export default DiscipleshipClassForm
