import { useEffect } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, Save } from 'lucide-react'
import { useForm, type UseFormSetError } from 'react-hook-form'
import {
  stockItemDefaultValues,
  stockItemSchema,
  type StockItemFormData,
  type StockItemFormValues,
} from '../../schemas/diaconiaStock'
import type { StockCategory, StockUnit } from '../../types/diaconia'

type StockItemFormProps = {
  categories: StockCategory[]
  generalError: string | null
  initialValues?: StockItemFormValues
  isSubmitting: boolean
  onCancel: () => void
  onSubmit: (values: StockItemFormData) => void
  setApiFieldError: (setError: UseFormSetError<StockItemFormValues>) => void
  submitLabel: string
  submittingLabel: string
  units: StockUnit[]
}

function StockItemForm({
  categories,
  generalError,
  initialValues,
  isSubmitting,
  onCancel,
  onSubmit,
  setApiFieldError,
  submitLabel,
  submittingLabel,
  units,
}: StockItemFormProps) {
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
    setError,
  } = useForm<StockItemFormValues, unknown, StockItemFormData>({
    defaultValues: initialValues ?? stockItemDefaultValues,
    resolver: zodResolver(stockItemSchema),
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
      {generalError ? <div className="form-alert form-alert--error" role="alert">{generalError}</div> : null}

      <fieldset className="form-section" disabled={isSubmitting}>
        <legend>Item de estoque</legend>

        <div className="form-grid">
          <div className="field-group field-group--wide">
            <label htmlFor="stock-name">Nome *</label>
            <input id="stock-name" type="text" aria-invalid={Boolean(errors.name)} {...register('name')} />
            {errors.name ? <span className="field-error">{errors.name.message}</span> : null}
          </div>

          <div className="field-group">
            <label htmlFor="stock-category">Categoria *</label>
            <select id="stock-category" aria-invalid={Boolean(errors.category_id)} {...register('category_id')}>
              <option value={0}>Selecione</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id} disabled={!category.is_active}>
                  {category.name}{category.is_active ? '' : ' (inativa)'}
                </option>
              ))}
            </select>
            {errors.category_id ? <span className="field-error">{errors.category_id.message}</span> : null}
          </div>

          <div className="field-group">
            <label htmlFor="stock-unit">Unidade *</label>
            <select id="stock-unit" aria-invalid={Boolean(errors.unit)} {...register('unit')}>
              <option value="">Selecione</option>
              {units.map((unit) => <option key={unit.value} value={unit.value}>{unit.label}</option>)}
            </select>
            {errors.unit ? <span className="field-error">{errors.unit.message}</span> : null}
          </div>

          <div className="field-group">
            <label htmlFor="minimum-stock">Estoque minimo *</label>
            <input id="minimum-stock" type="number" min={0} step={1} aria-invalid={Boolean(errors.minimum_stock)} {...register('minimum_stock')} />
            <span className="field-help">Informe 0 caso este item nao precise de controle de estoque minimo.</span>
            {errors.minimum_stock ? <span className="field-error">{errors.minimum_stock.message}</span> : null}
          </div>

          <div className="field-group">
            <label htmlFor="stock-status">Status</label>
            <select id="stock-status" {...register('is_active', { setValueAs: (value) => value === 'true' })}>
              <option value="true">Ativo</option>
              <option value="false">Inativo</option>
            </select>
          </div>

          <div className="field-group field-group--wide">
            <label htmlFor="stock-notes">Observacao</label>
            <textarea id="stock-notes" rows={5} aria-invalid={Boolean(errors.notes)} {...register('notes')} />
            {errors.notes ? <span className="field-error">{errors.notes.message}</span> : null}
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

export default StockItemForm
