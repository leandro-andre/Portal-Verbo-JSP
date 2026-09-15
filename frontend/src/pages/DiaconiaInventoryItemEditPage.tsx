import { useCallback, useRef, useState } from 'react'
import type { UseFormSetError } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { DiaconiaApiValidationError, DiaconiaHttpError } from '../api/diaconia'
import InventoryItemForm from '../components/diaconia/InventoryItemForm'
import {
  useInventoryCategories,
  useInventoryItem,
  useInventoryItemLifecycle,
  useUpdateInventoryItem,
} from '../hooks/useDiaconiaInventory'
import type { InventoryItemFormData, InventoryItemFormValues } from '../schemas/diaconiaInventory'
import type { UpdateInventoryItemInput } from '../types/diaconiaInventory'

type SetError = UseFormSetError<InventoryItemFormValues>

function DiaconiaInventoryItemEditPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const itemId = Number(id)
  const isValidId = Number.isInteger(itemId) && itemId > 0
  const { data: item, error, isError, isLoading, refetch } = useInventoryItem(itemId)
  const { data: categories = [], isLoading: categoriesLoading } = useInventoryCategories({ status: 'ALL' })
  const updateItem = useUpdateInventoryItem(itemId)
  const lifecycle = useInventoryItemLifecycle(itemId)
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
        if (message) setError(field as keyof InventoryItemFormValues, { message, type: 'server' })
      })
    },
    [apiValidationErrors],
  )

  const handleSubmit = async (values: InventoryItemFormData) => {
    const payload: UpdateInventoryItemInput = {
      name: values.name,
      category_id: values.category_id,
      description: values.description,
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
      navigate('/diaconia/inventario/itens')
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
          <Link className="button button--secondary" to="/diaconia/inventario/itens">
            <ArrowLeft size={17} aria-hidden="true" />
            Voltar para Itens
          </Link>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h1>Nao foi possivel carregar o item.</h1>
          <p>Verifique a conexao com o backend e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : item && !categoriesLoading ? (
        <>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link to="/diaconia">Diaconia</Link>
            <span aria-hidden="true">/</span>
            <Link to="/diaconia/inventario">Inventario</Link>
            <span aria-hidden="true">/</span>
            <Link to="/diaconia/inventario/itens">Itens</Link>
            <span aria-hidden="true">/</span>
            <strong>Editar</strong>
          </nav>

          <div className="page-heading page-heading--compact">
            <div>
              <h1>Editar item</h1>
              <p className="page-heading__description">Atualize o cadastro do bem no inventario.</p>
            </div>
          </div>

          <InventoryItemForm
            categories={availableCategories}
            generalError={generalError}
            initialValues={{
              name: item.name,
              category_id: item.category.id,
              description: item.description,
              is_active: item.is_active,
            }}
            isSubmitting={updateItem.isPending || lifecycle.deactivate.isPending || lifecycle.reactivate.isPending}
            onCancel={() => navigate('/diaconia/inventario/itens')}
            onSubmit={(values) => void handleSubmit(values)}
            setApiFieldError={setApiFieldError}
            submitLabel="Salvar item"
            submittingLabel="Salvando..."
          />
        </>
      ) : (
        <div className="state-panel"><h1>Carregando formulario...</h1></div>
      )}
    </section>
  )
}

export default DiaconiaInventoryItemEditPage
