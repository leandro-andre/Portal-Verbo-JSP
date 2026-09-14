import { useCallback, useRef, useState } from 'react'
import type { UseFormSetError } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { DiaconiaApiValidationError, DiaconiaBusinessError } from '../api/diaconia'
import StockMovementForm from '../components/diaconia/StockMovementForm'
import { useCreateStockMovement, useStockItems } from '../hooks/useDiaconiaStock'
import type { StockMovementFormData, StockMovementFormValues } from '../schemas/diaconiaStock'
import type { CreateStockMovementInput, StockMovementType } from '../types/diaconia'

type SetError = UseFormSetError<StockMovementFormValues>

type DiaconiaStockMovementCreatePageProps = {
  movementType: StockMovementType
}

function DiaconiaStockMovementCreatePage({ movementType }: DiaconiaStockMovementCreatePageProps) {
  const navigate = useNavigate()
  const { data: items = [], isLoading } = useStockItems()
  const createMovement = useCreateStockMovement()
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [apiValidationErrors, setApiValidationErrors] = useState<DiaconiaApiValidationError | null>(null)
  const appliedApiErrorsRef = useRef<DiaconiaApiValidationError | null>(null)
  const activeItems = items.filter((item) => item.is_active)
  const isEntry = movementType === 'ENTRADA'

  const setApiFieldError = useCallback(
    (setError: SetError) => {
      if (!apiValidationErrors || appliedApiErrorsRef.current === apiValidationErrors) return
      appliedApiErrorsRef.current = apiValidationErrors
      Object.entries(apiValidationErrors.fieldErrors).forEach(([field, messages]) => {
        const message = messages?.[0]
        if (message) setError(field as keyof StockMovementFormValues, { message, type: 'server' })
      })
    },
    [apiValidationErrors],
  )

  const handleSubmit = async (values: StockMovementFormData) => {
    const payload: CreateStockMovementInput = {
      item_id: values.item_id,
      movement_type: movementType,
      quantity: values.quantity,
      notes: values.notes,
    }
    setGeneralError(null)
    setApiValidationErrors(null)
    appliedApiErrorsRef.current = null

    try {
      await createMovement.mutateAsync(payload)
      navigate('/diaconia/estoque', {
        state: { successMessage: isEntry ? 'Entrada registrada com sucesso.' : 'Saida registrada com sucesso.' },
      })
    } catch (error) {
      if (error instanceof DiaconiaApiValidationError) {
        setApiValidationErrors(error)
        return
      }
      if (error instanceof DiaconiaBusinessError) {
        setGeneralError(error.message)
        return
      }
      setGeneralError(isEntry ? 'Nao foi possivel registrar a entrada.' : 'Nao foi possivel registrar a saida.')
    }
  }

  return (
    <section className="person-create-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/estoque">Estoque</Link>
        <span aria-hidden="true">/</span>
        <strong>{isEntry ? 'Nova entrada' : 'Nova saida'}</strong>
      </nav>

      <div className="page-heading page-heading--compact">
        <div>
          <h1>{isEntry ? 'Nova entrada' : 'Nova saida'}</h1>
          <p className="page-heading__description">
            {isEntry ? 'Registre a chegada de materiais ao estoque.' : 'Registre a retirada de materiais do estoque.'}
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando itens...</h2></div>
      ) : (
        <StockMovementForm
          generalError={generalError}
          isSubmitting={createMovement.isPending}
          items={activeItems}
          movementType={movementType}
          onCancel={() => navigate('/diaconia/estoque')}
          onSubmit={(values) => void handleSubmit(values)}
          setApiFieldError={setApiFieldError}
          submitLabel={isEntry ? 'Registrar entrada' : 'Registrar saida'}
          submittingLabel="Registrando..."
        />
      )}
    </section>
  )
}

export default DiaconiaStockMovementCreatePage
