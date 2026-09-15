import { useCallback, useRef, useState } from 'react'
import type { UseFormSetError } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { DiaconiaApiValidationError } from '../api/diaconia'
import InventoryItemForm from '../components/diaconia/InventoryItemForm'
import { deactivateInventoryItem } from '../api/diaconiaInventory'
import { useCreateInventoryItem, useInventoryCategories } from '../hooks/useDiaconiaInventory'
import type { InventoryItemFormData, InventoryItemFormValues } from '../schemas/diaconiaInventory'
import type { CreateInventoryItemInput } from '../types/diaconiaInventory'

type SetError = UseFormSetError<InventoryItemFormValues>

function DiaconiaInventoryItemCreatePage() {
  const navigate = useNavigate()
  const createItem = useCreateInventoryItem()
  const { data: categories = [], isLoading: categoriesLoading } = useInventoryCategories({ status: 'ACTIVE' })
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<DiaconiaApiValidationError | null>(null)
  const appliedApiErrorsRef = useRef<DiaconiaApiValidationError | null>(null)

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
    const payload: CreateInventoryItemInput = {
      name: values.name,
      category_id: values.category_id,
      description: values.description,
    }
    setGeneralError(null)
    setApiValidationErrors(null)
    appliedApiErrorsRef.current = null

    try {
      const item = await createItem.mutateAsync(payload)
      if (!values.is_active) {
        await deactivateInventoryItem(item.id)
      }
      navigate('/diaconia/inventario/itens')
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
        <Link to="/diaconia/inventario">Inventario</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario/itens">Itens</Link>
        <span aria-hidden="true">/</span>
        <strong>Novo item</strong>
      </nav>

      <div className="page-heading page-heading--compact">
        <div>
          <h1>Novo item</h1>
          <p className="page-heading__description">Cadastre um bem no catalogo operacional do inventario.</p>
        </div>
      </div>

      {categoriesLoading ? (
        <div className="state-panel"><h2>Carregando formulario...</h2></div>
      ) : categories.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhuma categoria ativa disponivel.</h2>
          <p>Cadastre ou reative uma categoria antes de criar itens de inventario.</p>
          <Link className="button button--primary" to="/diaconia/inventario/categorias">Gerenciar categorias</Link>
        </div>
      ) : (
        <InventoryItemForm
          categories={categories}
          generalError={generalError}
          isSubmitting={createItem.isPending}
          onCancel={() => navigate('/diaconia/inventario/itens')}
          onSubmit={(values) => void handleSubmit(values)}
          setApiFieldError={setApiFieldError}
          submitLabel="Criar item"
          submittingLabel="Criando..."
        />
      )}
    </section>
  )
}

export default DiaconiaInventoryItemCreatePage
