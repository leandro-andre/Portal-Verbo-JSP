import { useCallback, useRef, useState } from 'react'
import type { UseFormSetError } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { deactivateStockItem, DiaconiaApiValidationError } from '../api/diaconia'
import StockItemForm from '../components/diaconia/StockItemForm'
import { useCreateStockItem, useStockCategories, useStockUnits } from '../hooks/useDiaconiaStock'
import type { StockItemFormData, StockItemFormValues } from '../schemas/diaconiaStock'
import type { CreateStockItemInput } from '../types/diaconia'

type SetError = UseFormSetError<StockItemFormValues>

function DiaconiaStockItemCreatePage() {
  const navigate = useNavigate()
  const createItem = useCreateStockItem()
  const { data: categories = [], isLoading: categoriesLoading } = useStockCategories()
  const { data: units = [], isLoading: unitsLoading } = useStockUnits()
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<DiaconiaApiValidationError | null>(null)
  const appliedApiErrorsRef = useRef<DiaconiaApiValidationError | null>(null)
  const activeCategories = categories.filter((category) => category.is_active)

  const setApiFieldError = useCallback(
    (setError: SetError) => {
      if (!apiValidationErrors || appliedApiErrorsRef.current === apiValidationErrors) return
      appliedApiErrorsRef.current = apiValidationErrors
      Object.entries(apiValidationErrors.fieldErrors).forEach(([field, messages]) => {
        const message = messages?.[0]
        if (message) setError(field as keyof StockItemFormValues, { message, type: 'server' })
      })
    },
    [apiValidationErrors],
  )

  const handleSubmit = async (values: StockItemFormData) => {
    const payload: CreateStockItemInput = {
      name: values.name,
      category_id: values.category_id,
      unit: values.unit,
      minimum_stock: values.minimum_stock,
      notes: values.notes,
    }
    setGeneralError(null)
    setApiValidationErrors(null)
    appliedApiErrorsRef.current = null

    try {
      const item = await createItem.mutateAsync(payload)
      if (!values.is_active) {
        await deactivateStockItem(item.id)
      }
      navigate('/diaconia/estoque', { state: { successMessage: 'Item criado com sucesso.' } })
    } catch (error) {
      if (error instanceof DiaconiaApiValidationError) {
        setApiValidationErrors(error)
        return
      }
      setGeneralError('Nao foi possivel criar o item.')
    }
  }

  return (
    <section className="person-create-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/estoque">Estoque</Link>
        <span aria-hidden="true">/</span>
        <strong>Novo item</strong>
      </nav>

      <div className="page-heading page-heading--compact">
        <div>
          <h1>Novo item</h1>
          <p className="page-heading__description">Cadastre um material controlado pela Diaconia.</p>
        </div>
      </div>

      {categoriesLoading || unitsLoading ? (
        <div className="state-panel"><h2>Carregando formulario...</h2></div>
      ) : (
        <StockItemForm
          categories={activeCategories}
          generalError={generalError}
          isSubmitting={createItem.isPending}
          onCancel={() => navigate('/diaconia/estoque')}
          onSubmit={(values) => void handleSubmit(values)}
          setApiFieldError={setApiFieldError}
          submitLabel="Criar item"
          submittingLabel="Criando..."
          units={units}
        />
      )}
    </section>
  )
}

export default DiaconiaStockItemCreatePage
