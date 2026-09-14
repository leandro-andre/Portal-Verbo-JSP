import { useEffect, useMemo } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, Save } from 'lucide-react'
import { useForm, useWatch, type UseFormSetError } from 'react-hook-form'
import {
  stockMovementDefaultValues,
  stockMovementSchema,
  type StockMovementFormData,
  type StockMovementFormValues,
} from '../../schemas/diaconiaStock'
import type { StockItem, StockMovementType } from '../../types/diaconia'

type StockMovementFormProps = {
  generalError: string | null
  isSubmitting: boolean
  items: StockItem[]
  movementType: StockMovementType
  onCancel: () => void
  onSubmit: (values: StockMovementFormData) => void
  setApiFieldError: (setError: UseFormSetError<StockMovementFormValues>) => void
  submitLabel: string
  submittingLabel: string
}

function StockMovementForm({
  generalError,
  isSubmitting,
  items,
  movementType,
  onCancel,
  onSubmit,
  setApiFieldError,
  submitLabel,
  submittingLabel,
}: StockMovementFormProps) {
  const {
    control,
    formState: { errors },
    handleSubmit,
    register,
    setError,
  } = useForm<StockMovementFormValues, unknown, StockMovementFormData>({
    defaultValues: stockMovementDefaultValues,
    resolver: zodResolver(stockMovementSchema),
  })
  const selectedItemId = useWatch({ control, name: 'item_id' })
  const selectedItem = useMemo(
    () => items.find((item) => item.id === Number(selectedItemId)) ?? null,
    [items, selectedItemId],
  )

  useEffect(() => {
    setApiFieldError(setError)
  }, [setApiFieldError, setError])

  return (
    <form className="person-form" onSubmit={(event) => void handleSubmit(onSubmit)(event)}>
      {generalError ? <div className="form-alert form-alert--error" role="alert">{generalError}</div> : null}

      <fieldset className="form-section" disabled={isSubmitting}>
        <legend>{movementType === 'ENTRADA' ? 'Entrada de estoque' : 'Saida de estoque'}</legend>

        <div className="form-grid">
          <div className="field-group field-group--wide">
            <label htmlFor="movement-item">Item *</label>
            <select id="movement-item" aria-invalid={Boolean(errors.item_id)} {...register('item_id')}>
              <option value={0}>Selecione</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} - {item.unit}
                </option>
              ))}
            </select>
            {errors.item_id ? <span className="field-error">{errors.item_id.message}</span> : null}
          </div>

          <div className="field-group">
            <label htmlFor="movement-quantity">Quantidade *</label>
            <input id="movement-quantity" type="number" min={1} step={1} aria-invalid={Boolean(errors.quantity)} {...register('quantity')} />
            {selectedItem ? (
              <span className="field-help">
                {movementType === 'SAIDA'
                  ? `Saldo disponivel: ${selectedItem.current_stock} ${selectedItem.unit}`
                  : `Unidade: ${selectedItem.unit}`}
              </span>
            ) : null}
            {errors.quantity ? <span className="field-error">{errors.quantity.message}</span> : null}
          </div>

          <div className="field-group field-group--wide">
            <label htmlFor="movement-notes">Observacao</label>
            <textarea id="movement-notes" rows={5} aria-invalid={Boolean(errors.notes)} {...register('notes')} />
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

export default StockMovementForm
