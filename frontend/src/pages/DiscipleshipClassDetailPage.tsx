import { useEffect, useState } from 'react'
import { ArrowLeft, Ban, CheckCircle2, Edit3, Play } from 'lucide-react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { DiscipleshipBusinessError, DiscipleshipHttpError } from '../api/discipleship'
import DiscipleshipStatusBadge from '../components/discipleship/DiscipleshipStatusBadge'
import { useCan } from '../hooks/useAuth'
import {
  useDiscipleshipClass,
  useDiscipleshipClassLifecycle,
} from '../hooks/useDiscipleshipClasses'
import type { DiscipleshipClass } from '../types/discipleship'
import { discipleshipStatusLabel, formatDate } from '../utils/discipleship'

type LifecycleAction = 'start' | 'complete' | 'cancel'

function DetailItem({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="profile-detail">
      <dt>{label}</dt>
      <dd>{value || '-'}</dd>
    </div>
  )
}

function actionCopy(action: LifecycleAction, discipleshipClass: DiscipleshipClass) {
  if (action === 'start') {
    return {
      title: `Iniciar turma ${discipleshipClass.name}?`,
      description: 'Ao confirmar, ela passara para Em andamento.',
      label: 'Iniciar turma',
      pending: 'Iniciando...',
    }
  }
  if (action === 'complete') {
    return {
      title: 'Concluir esta turma?',
      description: 'Esta acao encerra a turma, mas ainda nao conclui automaticamente o discipulado dos alunos.',
      label: 'Concluir turma',
      pending: 'Concluindo...',
    }
  }
  return {
    title: 'Cancelar esta turma?',
    description: 'Os dados permanecerao preservados.',
    label: 'Cancelar turma',
    pending: 'Cancelando...',
  }
}

function LifecycleDialog({
  action,
  discipleshipClass,
  error,
  isPending,
  onClose,
  onConfirm,
}: {
  action: LifecycleAction
  discipleshipClass: DiscipleshipClass
  error: string | null
  isPending: boolean
  onClose: () => void
  onConfirm: () => void
}) {
  const copy = actionCopy(action, discipleshipClass)

  return (
    <div className="dialog-backdrop" role="presentation">
      <div className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="discipleship-action-title">
        <h2 id="discipleship-action-title">{copy.title}</h2>
        <p>{copy.description}</p>

        {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

        <div className="form-actions">
          <button className="button button--secondary" type="button" disabled={isPending} onClick={onClose}>
            Cancelar
          </button>
          <button className="button button--primary" type="button" disabled={isPending} onClick={onConfirm}>
            {action === 'start' ? <Play size={17} aria-hidden="true" /> : null}
            {action === 'complete' ? <CheckCircle2 size={17} aria-hidden="true" /> : null}
            {action === 'cancel' ? <Ban size={17} aria-hidden="true" /> : null}
            {isPending ? copy.pending : copy.label}
          </button>
        </div>
      </div>
    </div>
  )
}

function businessErrorMessage(error: unknown) {
  if (error instanceof DiscipleshipBusinessError) {
    if (error.code === 'DISCIPLESHIP_CLASS_ALREADY_IN_PROGRESS') {
      return 'Ja existe uma turma de discipulado em andamento.'
    }
    if (error.code === 'INVALID_DISCIPLESHIP_CLASS_TRANSITION') {
      return 'Esta acao nao esta disponivel para o status atual da turma.'
    }
  }

  return 'Nao foi possivel executar esta acao.'
}

function DiscipleshipClassDetailPage() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const classId = Number(id)
  const isValidId = Number.isInteger(classId) && classId > 0
  const { data: discipleshipClass, error, isError, isLoading, refetch } = useDiscipleshipClass(classId)
  const lifecycle = useDiscipleshipClassLifecycle(classId)
  const canChange = useCan('DISCIPLESHIP_CLASS_CHANGE')
  const canStart = useCan('DISCIPLESHIP_CLASS_START')
  const canComplete = useCan('DISCIPLESHIP_CLASS_COMPLETE')
  const canCancel = useCan('DISCIPLESHIP_CLASS_CANCEL')
  const [dialogAction, setDialogAction] = useState<LifecycleAction | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState(() => {
    const state = location.state as { successMessage?: string } | null
    return state?.successMessage ?? null
  })
  const isNotFound = !isValidId || (error instanceof DiscipleshipHttpError && error.status === 404)

  useEffect(() => {
    if (location.state) {
      navigate(location.pathname, { replace: true, state: null })
    }
  }, [location.pathname, location.state, navigate])

  const isActionPending =
    lifecycle.start.isPending ||
    lifecycle.complete.isPending ||
    lifecycle.cancel.isPending

  const handleConfirmAction = async () => {
    if (!dialogAction) {
      return
    }

    setActionError(null)

    try {
      if (dialogAction === 'start') {
        await lifecycle.start.mutateAsync()
        setSuccessMessage('Turma iniciada com sucesso.')
      } else if (dialogAction === 'complete') {
        await lifecycle.complete.mutateAsync()
        setSuccessMessage('Turma concluida com sucesso.')
      } else {
        await lifecycle.cancel.mutateAsync()
        setSuccessMessage('Turma cancelada com sucesso.')
      }
      setDialogAction(null)
    } catch (actionFailure) {
      setActionError(businessErrorMessage(actionFailure))
    }
  }

  return (
    <section className="person-profile-page">
      {isLoading && isValidId ? (
        <div className="state-panel"><h1>Carregando turma...</h1><p>Aguarde enquanto os dados sao carregados.</p></div>
      ) : isNotFound ? (
        <div className="state-panel">
          <h1>Turma nao encontrada</h1>
          <p>Nao encontramos a turma solicitada.</p>
          <Link className="button button--secondary" to="/discipulado"><ArrowLeft size={17} aria-hidden="true" />Voltar para Discipulado</Link>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h1>Nao foi possivel carregar a turma.</h1>
          <p>Verifique a conexao com o backend e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : discipleshipClass ? (
        <>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link to="/discipulado">Discipulado</Link>
            <span aria-hidden="true">/</span>
            <strong>{discipleshipClass.name}</strong>
          </nav>

          <header className="profile-header">
            <div className="profile-header__identity">
              <h1>{discipleshipClass.name}</h1>
              <DiscipleshipStatusBadge status={discipleshipClass.status} />
            </div>
            <div className="profile-actions">
              {canChange && !['COMPLETED', 'CANCELLED'].includes(discipleshipClass.status) ? (
                <Link className="button button--secondary" to={`/discipulado/${discipleshipClass.id}/editar`}>
                  <Edit3 size={17} aria-hidden="true" />
                  Editar
                </Link>
              ) : null}
              {discipleshipClass.status === 'PLANNED' && canStart ? (
                <button className="button button--primary" type="button" onClick={() => setDialogAction('start')}>
                  <Play size={17} aria-hidden="true" />
                  Iniciar turma
                </button>
              ) : null}
              {discipleshipClass.status === 'IN_PROGRESS' && canComplete ? (
                <button className="button button--primary" type="button" onClick={() => setDialogAction('complete')}>
                  <CheckCircle2 size={17} aria-hidden="true" />
                  Concluir turma
                </button>
              ) : null}
              {['PLANNED', 'IN_PROGRESS'].includes(discipleshipClass.status) && canCancel ? (
                <button className="button button--secondary" type="button" onClick={() => setDialogAction('cancel')}>
                  <Ban size={17} aria-hidden="true" />
                  Cancelar turma
                </button>
              ) : null}
            </div>
          </header>

          {successMessage ? <div className="form-alert form-alert--success" role="status">{successMessage}</div> : null}

          <div className="profile-content">
            <section className="profile-section">
              <h2>Dados da turma</h2>
              <dl className="profile-details">
                <DetailItem label="Nome" value={discipleshipClass.name} />
                <DetailItem label="Status" value={discipleshipStatusLabel(discipleshipClass.status)} />
                <DetailItem label="Professor" value={discipleshipClass.teacher.display_name} />
                <DetailItem label="Periodo" value={`${formatDate(discipleshipClass.start_date)} - ${formatDate(discipleshipClass.expected_end_date)}`} />
                <DetailItem label="Aulas previstas" value={discipleshipClass.planned_sessions} />
              </dl>
            </section>
          </div>

          {dialogAction ? (
            <LifecycleDialog
              action={dialogAction}
              discipleshipClass={discipleshipClass}
              error={actionError}
              isPending={isActionPending}
              onClose={() => {
                setActionError(null)
                setDialogAction(null)
              }}
              onConfirm={() => void handleConfirmAction()}
            />
          ) : null}
        </>
      ) : null}
    </section>
  )
}

export default DiscipleshipClassDetailPage
