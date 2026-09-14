import { useCallback, useRef, useState } from 'react'
import type { UseFormSetError } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { DiaconiaApiValidationError, DiaconiaHttpError } from '../api/diaconia'
import StockItemForm from '../components/diaconia/StockItemForm'
import {
  useStockCategories,
  useStockItem,
  useStockItemLifecycle,
  useStockUnits,
  useUpdateStockItem,
} from '../hooks/useDiaconiaStock'
import type { StockItemFormData, StockItemFormValues } from '../schemas/diaconiaStock'
import type { UpdateStockItemInput } from '../types/diaconia'

type SetError = UseFormSetError<StockItemFormValues>

function DiaconiaStockItemEditPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const itemId = Number(id)
  const isValidId = Number.isInteger(itemId) && itemId > 0
  const { data: item, error, isError, isLoading, refetch } = useStockItem(itemId)
  const { data: categories = [], isLoading: categoriesLoading } = useStockCategories()
  const { data: units = [], isLoading: unitsLoading } = useStockUnits()
  const updateItem = useUpdateStockItem(itemId)
  const lifecycle = useStockItemLifecycle(itemId)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<DiaconiaApiValidationError | null>(null)
  const appliedApiErrorsRef = useRef<DiaconiaApiValidationError | null>(null)
  const isNotFound = !isValidId || (error instanceof DiaconiaHttpError && error.status === 404)

  const availableCategories = categories.filter((category) => category.is_active || category.id === item?.category.id)

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
    const payload: UpdateStockItemInput = {
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
      await updateItem.mutateAsync(payload)
      if (item && values.is_active !== item.is_active) {
        if (values.is_active) {
          await lifecycle.reactivate.mutateAsync()
        } else {
          await lifecycle.deactivate.mutateAsync()
        }
      }
      navigate('/diaconia/estoque', { state: { successMessage: 'Item atualizado com sucesso.' } })
    } catch (error) {
      if (error instanceof DiaconiaApiValidationError) {
        setApiValidationErrors(error)
        return
      }
      setGeneralError('Nao foi possivel salvar as alteracoes.')
    }
  }

  return (
    <section className="person-create-page">
      {isLoading && isValidId ? (
        <div className="state-panel"><h1>Carregando item...</h1><p>Aguarde enquanto os dados sao carregados.</p></div>
      ) : isNotFound ? (
        <div className="state-panel">
          <h1>Item nao encontrado</h1>
          <p>Nao encontramos o item solicitado.</p>
          <Link className="button button--secondary" to="/diaconia/estoque">
            <ArrowLeft size={17} aria-hidden="true" />
            Voltar para Estoque
          </Link>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h1>Nao foi possivel carregar o item.</h1>
          <p>Verifique a conexao com o backend e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : item && !categoriesLoading && !unitsLoading ? (
        <>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link to="/diaconia">Diaconia</Link>
            <span aria-hidden="true">/</span>
            <Link to="/diaconia/estoque">Estoque</Link>
            <span aria-hidden="true">/</span>
            <strong>Editar</strong>
          </nav>

          <div className="page-heading page-heading--compact">
            <div>
              <h1>Editar item</h1>
              <p className="page-heading__description">Atualize o cadastro do material.</p>
            </div>
          </div>

          <StockItemForm
            categories={availableCategories}
            generalError={generalError}
            initialValues={{
              name: item.name,
              category_id: item.category.id,
              unit: item.unit,
              minimum_stock: item.minimum_stock,
              notes: item.notes,
              is_active: item.is_active,
            }}
            isSubmitting={updateItem.isPending || lifecycle.deactivate.isPending || lifecycle.reactivate.isPending}
            onCancel={() => navigate('/diaconia/estoque')}
            onSubmit={(values) => void handleSubmit(values)}
            setApiFieldError={setApiFieldError}
            submitLabel="Salvar item"
            submittingLabel="Salvando..."
            units={units}
          />
        </>
      ) : (
        <div className="state-panel"><h1>Carregando formulario...</h1></div>
      )}
    </section>
  )
}

export default DiaconiaStockItemEditPage
