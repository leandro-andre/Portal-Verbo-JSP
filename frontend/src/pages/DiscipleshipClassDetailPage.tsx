import { useEffect, useState } from 'react'
import { ArrowLeft, Ban, CheckCircle2, Edit3, Play, UserPlus } from 'lucide-react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { DiscipleshipBusinessError, DiscipleshipHttpError } from '../api/discipleship'
import DiscipleshipStatusBadge from '../components/discipleship/DiscipleshipStatusBadge'
import { useCan } from '../hooks/useAuth'
import {
  useDiscipleshipClass,
  useDiscipleshipClassLifecycle,
  useCreateDiscipleshipEnrollment,
  useDiscipleshipEnrollments,
  useWithdrawDiscipleshipEnrollment,
} from '../hooks/useDiscipleshipClasses'
import { usePeople } from '../hooks/usePeople'
import type { DiscipleshipClass, DiscipleshipEnrollment } from '../types/discipleship'
import { discipleshipStatusLabel, enrollmentStatusLabel, formatDate } from '../utils/discipleship'

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
    if (error.code === 'PERSON_NOT_IN_CHURCH_JOURNEY') {
      return 'Esta pessoa ainda nao esta na jornada da igreja.'
    }
    if (error.code === 'DISCIPLESHIP_CLASS_NOT_OPEN_FOR_ENROLLMENT') {
      return 'Esta turma nao esta aberta para matriculas.'
    }
    if (error.code === 'DISCIPLESHIP_ENROLLMENT_ALREADY_EXISTS') {
      return 'Esta pessoa ja possui matricula nesta turma.'
    }
    if (error.code === 'INVALID_DISCIPLESHIP_ENROLLMENT_TRANSITION') {
      return 'Esta matricula nao permite esta acao.'
    }
  }

  return 'Nao foi possivel executar esta acao.'
}

function EnrollmentStatusBadge({ status }: { status: DiscipleshipEnrollment['status'] }) {
  return (
    <span className={`status-badge enrollment-status-badge--${status.toLowerCase()}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {enrollmentStatusLabel(status)}
    </span>
  )
}

function EnrollPersonDialog({
  enrolledPersonIds,
  error,
  isPending,
  onClose,
  onConfirm,
}: {
  enrolledPersonIds: Set<number>
  error: string | null
  isPending: boolean
  onClose: () => void
  onConfirm: (personId: number) => void
}) {
  const { data: people = [], isLoading } = usePeople()
  const [search, setSearch] = useState('')
  const [selectedPersonId, setSelectedPersonId] = useState<number | null>(null)
  const normalizedSearch = search.trim().toLowerCase()
  const candidates = people.filter((person) => {
    if (!person.has_church_journey || enrolledPersonIds.has(person.id)) {
      return false
    }

    return (
      !normalizedSearch ||
      person.display_name.toLowerCase().includes(normalizedSearch) ||
      person.full_name.toLowerCase().includes(normalizedSearch)
    )
  })

  return (
    <div className="dialog-backdrop" role="presentation">
      <div className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="enroll-dialog-title">
        <h2 id="enroll-dialog-title">Matricular pessoa</h2>

        <label className="field-group">
          <span>Buscar pessoa</span>
          <input
            type="search"
            placeholder="Buscar por nome..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <div className="selection-list" aria-label="Pessoas elegiveis">
          {isLoading ? (
            <p className="page-heading__description">Carregando pessoas...</p>
          ) : candidates.length > 0 ? (
            candidates.map((person) => (
              <button
                key={person.id}
                className={`selection-option${selectedPersonId === person.id ? ' selection-option--selected' : ''}`}
                type="button"
                onClick={() => setSelectedPersonId(person.id)}
              >
                <strong>{person.display_name}</strong>
                <span>{person.full_name}</span>
              </button>
            ))
          ) : (
            <p className="page-heading__description">Nenhuma pessoa elegivel encontrada.</p>
          )}
        </div>

        {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

        <div className="form-actions">
          <button className="button button--secondary" type="button" disabled={isPending} onClick={onClose}>
            Cancelar
          </button>
          <button
            className="button button--primary"
            type="button"
            disabled={isPending || selectedPersonId === null}
            onClick={() => selectedPersonId !== null && onConfirm(selectedPersonId)}
          >
            <UserPlus size={17} aria-hidden="true" />
            {isPending ? 'Matriculando...' : 'Matricular'}
          </button>
        </div>
      </div>
    </div>
  )
}

function WithdrawEnrollmentDialog({
  enrollment,
  error,
  isPending,
  onClose,
  onConfirm,
}: {
  enrollment: DiscipleshipEnrollment
  error: string | null
  isPending: boolean
  onClose: () => void
  onConfirm: () => void
}) {
  return (
    <div className="dialog-backdrop" role="presentation">
      <div className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="withdraw-dialog-title">
        <h2 id="withdraw-dialog-title">Marcar {enrollment.person.display_name} como desistente desta turma?</h2>
        <p>Os dados da matricula serao preservados.</p>

        {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

        <div className="form-actions">
          <button className="button button--secondary" type="button" disabled={isPending} onClick={onClose}>
            Cancelar
          </button>
          <button className="button button--primary" type="button" disabled={isPending} onClick={onConfirm}>
            <Ban size={17} aria-hidden="true" />
            {isPending ? 'Confirmando...' : 'Confirmar desistencia'}
          </button>
        </div>
      </div>
    </div>
  )
}

function DiscipleshipClassDetailPage() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const classId = Number(id)
  const isValidId = Number.isInteger(classId) && classId > 0
  const { data: discipleshipClass, error, isError, isLoading, refetch } = useDiscipleshipClass(classId)
  const { data: enrollments = [], isError: isEnrollmentsError, isLoading: isEnrollmentsLoading } = useDiscipleshipEnrollments(classId)
  const lifecycle = useDiscipleshipClassLifecycle(classId)
  const createEnrollment = useCreateDiscipleshipEnrollment(classId)
  const withdrawEnrollment = useWithdrawDiscipleshipEnrollment(classId)
  const canChange = useCan('DISCIPLESHIP_CLASS_CHANGE')
  const canStart = useCan('DISCIPLESHIP_CLASS_START')
  const canComplete = useCan('DISCIPLESHIP_CLASS_COMPLETE')
  const canCancel = useCan('DISCIPLESHIP_CLASS_CANCEL')
  const canCreateEnrollment = useCan('DISCIPLESHIP_ENROLLMENT_CREATE')
  const canWithdrawEnrollment = useCan('DISCIPLESHIP_ENROLLMENT_WITHDRAW')
  const [dialogAction, setDialogAction] = useState<LifecycleAction | null>(null)
  const [isEnrollDialogOpen, setIsEnrollDialogOpen] = useState(false)
  const [withdrawTarget, setWithdrawTarget] = useState<DiscipleshipEnrollment | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [enrollmentError, setEnrollmentError] = useState<string | null>(null)
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

  const enrolledPersonIds = new Set(enrollments.map((enrollment) => enrollment.person.id))
  const enrolledCount = enrollments.filter((enrollment) => enrollment.status === 'ENROLLED').length
  const withdrawnCount = enrollments.filter((enrollment) => enrollment.status === 'WITHDRAWN').length
  const canEnrollInClass = discipleshipClass ? ['PLANNED', 'IN_PROGRESS'].includes(discipleshipClass.status) : false

  const handleEnroll = async (personId: number) => {
    setEnrollmentError(null)

    try {
      await createEnrollment.mutateAsync({ person_id: personId })
      setIsEnrollDialogOpen(false)
      setSuccessMessage('Pessoa matriculada com sucesso.')
    } catch (error) {
      setEnrollmentError(businessErrorMessage(error))
    }
  }

  const handleWithdraw = async () => {
    if (!withdrawTarget) {
      return
    }

    setEnrollmentError(null)

    try {
      await withdrawEnrollment.mutateAsync(withdrawTarget.id)
      setWithdrawTarget(null)
      setSuccessMessage('Matricula marcada como desistente.')
    } catch (error) {
      setEnrollmentError(businessErrorMessage(error))
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
            <section className="profile-section">
              <div className="section-heading-row">
                <div>
                  <h2>Alunos</h2>
                  <p className="page-heading__description">
                    {enrolledCount} matriculados | {withdrawnCount} desistentes
                  </p>
                </div>
                {canCreateEnrollment && canEnrollInClass ? (
                  <button
                    className="button button--primary"
                    type="button"
                    onClick={() => {
                      setEnrollmentError(null)
                      setIsEnrollDialogOpen(true)
                    }}
                  >
                    <UserPlus size={17} aria-hidden="true" />
                    Matricular pessoa
                  </button>
                ) : null}
              </div>

              {discipleshipClass.status === 'IN_PROGRESS' && canCreateEnrollment ? (
                <p className="page-heading__description">Esta turma ja esta em andamento.</p>
              ) : null}

              {isEnrollmentsLoading ? (
                <p className="page-heading__description">Carregando matriculas...</p>
              ) : isEnrollmentsError ? (
                <p className="page-heading__description">Nao foi possivel carregar as matriculas.</p>
              ) : enrollments.length > 0 ? (
                <div className="table-shell table-shell--section">
                  <table className="people-table">
                    <thead>
                      <tr>
                        <th scope="col">Pessoa</th>
                        <th scope="col">Status</th>
                        <th scope="col">Matricula</th>
                        <th scope="col">Desistencia</th>
                        <th scope="col" className="people-table__actions-header">Acao</th>
                      </tr>
                    </thead>
                    <tbody>
                      {enrollments.map((enrollment) => (
                        <tr key={enrollment.id}>
                          <td>
                            <strong>{enrollment.person.display_name}</strong>
                            {enrollment.person.full_name !== enrollment.person.display_name ? (
                              <span className="table-muted">{enrollment.person.full_name}</span>
                            ) : null}
                          </td>
                          <td><EnrollmentStatusBadge status={enrollment.status} /></td>
                          <td>{formatDate(enrollment.enrolled_at)}</td>
                          <td>{enrollment.withdrawn_at ? formatDate(enrollment.withdrawn_at) : '-'}</td>
                          <td>
                            {canWithdrawEnrollment && enrollment.status === 'ENROLLED' ? (
                              <button
                                className="button button--secondary"
                                type="button"
                                onClick={() => {
                                  setEnrollmentError(null)
                                  setWithdrawTarget(enrollment)
                                }}
                              >
                                <Ban size={17} aria-hidden="true" />
                                Marcar desistencia
                              </button>
                            ) : null}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="page-heading__description">Nenhuma pessoa matriculada nesta turma.</p>
              )}
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
          {isEnrollDialogOpen ? (
            <EnrollPersonDialog
              enrolledPersonIds={enrolledPersonIds}
              error={enrollmentError}
              isPending={createEnrollment.isPending}
              onClose={() => setIsEnrollDialogOpen(false)}
              onConfirm={(personId) => void handleEnroll(personId)}
            />
          ) : null}
          {withdrawTarget ? (
            <WithdrawEnrollmentDialog
              enrollment={withdrawTarget}
              error={enrollmentError}
              isPending={withdrawEnrollment.isPending}
              onClose={() => setWithdrawTarget(null)}
              onConfirm={() => void handleWithdraw()}
            />
          ) : null}
        </>
      ) : null}
    </section>
  )
}

export default DiscipleshipClassDetailPage
