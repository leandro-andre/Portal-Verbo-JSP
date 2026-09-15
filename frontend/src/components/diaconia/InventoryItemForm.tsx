import { useEffect } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, Save } from 'lucide-react'
import { useForm, type UseFormSetError } from 'react-hook-form'
import {
  inventoryItemDefaultValues,
  inventoryItemSchema,
  type InventoryItemFormData,
  type InventoryItemFormValues,
} from '../../schemas/diaconiaInventory'
import type { InventoryCategory } from '../../types/diaconiaInventory'

type InventoryItemFormProps = {
  categories: InventoryCategory[]
  generalError: string | null
  initialValues?: InventoryItemFormValues
  isSubmitting: boolean
  onCancel: () => void
  onSubmit: (values: InventoryItemFormData) => void
  setApiFieldError: (setError: UseFormSetError<InventoryItemFormValues>) => void
  submitLabel: string
  submittingLabel: string
}

function InventoryItemForm({
  categories,
  generalError,
  initialValues,
  isSubmitting,
  onCancel,
  onSubmit,
  setApiFieldError,
  submitLabel,
  submittingLabel,
}: InventoryItemFormProps) {
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
    setError,
  } = useForm<InventoryItemFormValues, unknown, InventoryItemFormData>({
    defaultValues: initialValues ?? inventoryItemDefaultValues,
    resolver: zodResolver(inventoryItemSchema),
  })

  useEffect(() => {
    setApiFieldError(setError)
  }, [setApiFieldError, setError])

  useEffect(() => {
    if (initialValues) reset(initialValues)
  }, [initialValues, reset])

  return (
    <form className="person-form" onSubmit={(event) => void handleSubmit(onSubmit)(event)}>
      {generalError ? <div className="form-alert form-alert--error" role="alert">{generalError}</div> : null}

      <fieldset className="form-section" disabled={isSubmitting}>
        <legend>Item de inventario</legend>

        <div className="form-grid">
          <div className="field-group field-group--wide">
            <label htmlFor="inventory-item-name">Nome *</label>
            <input id="inventory-item-name" type="text" aria-invalid={Boolean(errors.name)} {...register('name')} />
            {errors.name ? <span className="field-error">{errors.name.message}</span> : null}
          </div>

          <div className="field-group">
            <label htmlFor="inventory-item-category">Categoria *</label>
            <select id="inventory-item-category" aria-invalid={Boolean(errors.category_id)} {...register('category_id')}>
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
            <label htmlFor="inventory-item-status">Status</label>
            <select id="inventory-item-status" {...register('is_active', { setValueAs: (value) => value === 'true' })}>
              <option value="true">Ativo</option>
              <option value="false">Inativo</option>
            </select>
          </div>

          <div className="field-group field-group--wide">
            <label htmlFor="inventory-item-description">Descricao</label>
            <textarea id="inventory-item-description" rows={5} aria-invalid={Boolean(errors.description)} {...register('description')} />
            {errors.description ? <span className="field-error">{errors.description.message}</span> : null}
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

export default InventoryItemForm
