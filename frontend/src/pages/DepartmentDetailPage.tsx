import { useEffect, useState } from 'react'
import { ArrowLeft, Edit3, RefreshCcw } from 'lucide-react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { DepartmentBusinessError, DepartmentHttpError } from '../api/departments'
import { useCan } from '../hooks/useAuth'
import { useDepartment, useDepartmentLifecycle } from '../hooks/useDepartments'
import type { Department } from '../types/department'

function formatDate(value: string) {
  if (!value) {
    return '-'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat('pt-BR').format(date)
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="profile-detail">
      <dt>{label}</dt>
      <dd>{value || '-'}</dd>
    </div>
  )
}

function DepartmentStatusBadge({ ativo }: { ativo: boolean }) {
  return (
    <span className={`status-badge ${ativo ? 'person-status-badge--active' : 'person-status-badge--inactive'}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {ativo ? 'Ativo' : 'Inativo'}
    </span>
  )
}

function LifecycleDialog({
  department,
  error,
  isPending,
  mode,
  onClose,
  onConfirm,
}: {
  department: Department
  error: string | null
  isPending: boolean
  mode: 'deactivate' | 'reactivate'
  onClose: () => void
  onConfirm: () => void
}) {
  const isDeactivate = mode === 'deactivate'

  return (
    <div className="dialog-backdrop" role="presentation">
      <div className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="department-lifecycle-title">
        <h2 id="department-lifecycle-title">
          {isDeactivate ? `Inativar o departamento ${department.nome}?` : `Reativar o departamento ${department.nome}?`}
        </h2>
        <div className="dialog-copy">
          {isDeactivate ? (
            <>
              <p>O departamento permanecera no historico.</p>
              <p>Esta acao nao excluira membros nem escalas existentes.</p>
            </>
          ) : (
            <p>O departamento voltara a aparecer como ativo.</p>
          )}
        </div>

        {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

        <div className="form-actions">
          <button className="button button--secondary" type="button" disabled={isPending} onClick={onClose}>
            Cancelar
          </button>
          <button className="button button--primary" type="button" disabled={isPending} onClick={onConfirm}>
            <RefreshCcw size={17} aria-hidden="true" />
            {isPending
              ? isDeactivate ? 'Inativando...' : 'Reativando...'
              : isDeactivate ? 'Inativar departamento' : 'Reativar departamento'}
          </button>
        </div>
      </div>
    </div>
  )
}

function businessErrorMessage(error: unknown) {
  if (error instanceof DepartmentBusinessError && error.code === 'INVALID_DEPARTMENT_TRANSITION') {
    return 'Esta acao nao esta disponivel para o status atual do departamento.'
  }
  return 'Nao foi possivel alterar o departamento.'
}

function DepartmentDetailPage() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const departmentId = Number(id)
  const isValidId = Number.isInteger(departmentId) && departmentId > 0
  const { data: department, error, isError, isLoading, refetch } = useDepartment(departmentId)
  const lifecycle = useDepartmentLifecycle(departmentId)
  const canChange = useCan('DEPARTMENT_CHANGE')
  const canDeactivate = useCan('DEPARTMENT_DEACTIVATE')
  const canReactivate = useCan('DEPARTMENT_REACTIVATE')
  const [dialogMode, setDialogMode] = useState<'deactivate' | 'reactivate' | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState(() => {
    const state = location.state as { successMessage?: string } | null
    return state?.successMessage ?? null
  })
  const isNotFound = !isValidId || (error instanceof DepartmentHttpError && error.status === 404)
  const isActionPending = lifecycle.deactivate.isPending || lifecycle.reactivate.isPending

  useEffect(() => {
    if (location.state) {
      navigate(location.pathname, { replace: true, state: null })
    }
  }, [location.pathname, location.state, navigate])

  const handleConfirmLifecycle = async () => {
    if (!dialogMode) {
      return
    }

    setActionError(null)

    try {
      if (dialogMode === 'deactivate') {
        await lifecycle.deactivate.mutateAsync()
        setSuccessMessage('Departamento inativado com sucesso.')
      } else {
        await lifecycle.reactivate.mutateAsync()
        setSuccessMessage('Departamento reativado com sucesso.')
      }
      setDialogMode(null)
    } catch (lifecycleError) {
      setActionError(businessErrorMessage(lifecycleError))
    }
  }

  return (
    <section className="person-profile-page">
      {isLoading && isValidId ? (
        <div className="state-panel"><h1>Carregando departamento...</h1><p>Aguarde enquanto os dados sao carregados.</p></div>
      ) : isNotFound ? (
        <div className="state-panel">
          <h1>Departamento nao encontrado</h1>
          <p>Nao encontramos o departamento solicitado.</p>
          <Link className="button button--secondary" to="/departamentos">
            <ArrowLeft size={17} aria-hidden="true" />
            Voltar para Departamentos
          </Link>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h1>Nao foi possivel carregar o departamento.</h1>
          <p>Verifique a conexao com o backend e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            Tentar novamente
          </button>
        </div>
      ) : department ? (
        <>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link to="/departamentos">Departamentos</Link>
            <span aria-hidden="true">/</span>
            <strong>{department.nome}</strong>
          </nav>

          <header className="profile-header">
            <div className="profile-header__identity">
              <h1>{department.nome}</h1>
              <DepartmentStatusBadge ativo={department.ativo} />
            </div>
            <div className="profile-actions">
              {canChange && department.ativo ? (
                <Link className="button button--secondary" to={`/departamentos/${department.id}/editar`}>
                  <Edit3 size={17} aria-hidden="true" />
                  Editar
                </Link>
              ) : null}
              {department.ativo && canDeactivate ? (
                <button className="button button--secondary" type="button" onClick={() => setDialogMode('deactivate')}>
                  <RefreshCcw size={17} aria-hidden="true" />
                  Inativar departamento
                </button>
              ) : null}
              {!department.ativo && canReactivate ? (
                <button className="button button--primary" type="button" onClick={() => setDialogMode('reactivate')}>
                  <RefreshCcw size={17} aria-hidden="true" />
                  Reativar departamento
                </button>
              ) : null}
            </div>
          </header>

          {successMessage ? <div className="form-alert form-alert--success" role="status">{successMessage}</div> : null}

          <div className="profile-content">
            <section className="profile-section">
              <h2>Dados do departamento</h2>
              <dl className="profile-details">
                <DetailItem label="Nome" value={department.nome} />
                <DetailItem label="Codigo" value={department.codigo} />
                <DetailItem label="Status" value={department.ativo ? 'Ativo' : 'Inativo'} />
                <DetailItem label="Criado em" value={formatDate(department.criado_em)} />
              </dl>
            </section>

            <section className="profile-section">
              <h2>Descricao</h2>
              <p className="page-heading__description">{department.descricao || 'Sem descricao cadastrada.'}</p>
            </section>
          </div>

          {dialogMode ? (
            <LifecycleDialog
              department={department}
              error={actionError}
              isPending={isActionPending}
              mode={dialogMode}
              onClose={() => {
                setActionError(null)
                setDialogMode(null)
              }}
              onConfirm={() => void handleConfirmLifecycle()}
            />
          ) : null}
        </>
      ) : null}
    </section>
  )
}

export default DepartmentDetailPage
