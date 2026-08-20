import { useEffect, useState } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, Ban, CalendarPlus, CheckCircle2, ClipboardCheck, Edit3, Play, Save, UserPlus } from 'lucide-react'
import { useForm, type UseFormSetError } from 'react-hook-form'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { DiscipleshipApiValidationError, DiscipleshipBusinessError, DiscipleshipHttpError } from '../api/discipleship'
import DiscipleshipStatusBadge from '../components/discipleship/DiscipleshipStatusBadge'
import { useCan } from '../hooks/useAuth'
import {
  useCancelDiscipleshipLesson,
  useCompleteDiscipleshipEnrollment,
  useCreateDiscipleshipLesson,
  useDiscipleshipClass,
  useDiscipleshipClassLifecycle,
  useDiscipleshipCompletion,
  useCreateDiscipleshipEnrollment,
  useDiscipleshipEnrollments,
  useDiscipleshipLessons,
  useUpdateDiscipleshipLesson,
  useWithdrawDiscipleshipEnrollment,
} from '../hooks/useDiscipleshipClasses'
import { usePeople } from '../hooks/usePeople'
import {
  discipleshipLessonDefaultValues,
  discipleshipLessonSchema,
  type DiscipleshipLessonFormData,
  type DiscipleshipLessonFormValues,
} from '../schemas/discipleshipLesson'
import type {
  DiscipleshipClass,
  DiscipleshipCompletionSummary,
  DiscipleshipEnrollment,
  DiscipleshipLesson,
} from '../types/discipleship'
import { discipleshipStatusLabel, enrollmentStatusLabel, formatDate, lessonStatusLabel } from '../utils/discipleship'

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
    if (error.code === 'DISCIPLESHIP_CLASS_NOT_OPEN_FOR_LESSONS') {
      return 'Esta turma nao esta aberta para gerenciamento de aulas.'
    }
    if (error.code === 'DISCIPLESHIP_LESSON_DATE_CONFLICT') {
      return 'Ja existe uma aula cadastrada para esta turma nesta data.'
    }
    if (error.code === 'INVALID_DISCIPLESHIP_LESSON_TRANSITION') {
      return 'Esta aula nao permite esta acao.'
    }
    if (error.code === 'DISCIPLESHIP_CLASS_NOT_COMPLETED') {
      return 'A turma ainda nao foi concluida.'
    }
    if (error.code === 'DISCIPLESHIP_ATTENDANCE_INCOMPLETE') {
      return 'Ainda existem chamadas pendentes para esta matricula.'
    }
    if (error.code === 'DISCIPLESHIP_MINIMUM_ATTENDANCE_NOT_REACHED') {
      return 'A frequencia minima nao foi atingida.'
    }
    if (error.code === 'DISCIPLESHIP_NO_VALID_ATTENDANCE_DENOMINATOR') {
      return 'Nao ha aulas validas suficientes para calcular a frequencia.'
    }
    if (error.code === 'DISCIPLESHIP_ENROLLMENT_WITHDRAWN') {
      return 'Matriculas desistentes nao podem ser concluidas.'
    }
    if (error.code === 'DISCIPLESHIP_ENROLLMENT_ALREADY_COMPLETED') {
      return 'Esta matricula ja foi concluida.'
    }
  }

  return 'Nao foi possivel executar esta acao.'
}

function formatPercentage(value: number | null) {
  return value === null ? 'Nao avaliavel' : `${value.toFixed(2).replace('.', ',')}%`
}

function completionResultLabel(completion?: DiscipleshipCompletionSummary) {
  if (!completion) return 'Carregando'
  if (completion.status === 'COMPLETED') return 'Concluido'
  if (completion.completion.can_complete) return 'Apta a conclusao'
  if (completion.completion.reason === 'CLASS_NOT_COMPLETED') return 'Em andamento'
  if (completion.completion.reason === 'ENROLLMENT_WITHDRAWN') return 'Desistente'
  if (completion.completion.reason === 'ATTENDANCE_INCOMPLETE') return 'Chamada pendente'
  if (completion.completion.reason === 'NO_FREQUENCY_DENOMINATOR') return 'Sem base avaliavel'
  if (completion.completion.reason === 'MINIMUM_ATTENDANCE_NOT_REACHED') return 'Frequencia insuficiente'
  if (completion.completion.reason === 'ALREADY_COMPLETED') return 'Concluido'
  return 'Nao apta'
}

function applyLessonApiErrors(
  error: DiscipleshipApiValidationError,
  setError: UseFormSetError<DiscipleshipLessonFormValues>,
) {
  const fieldErrors = error.fieldErrors

  if ('title' in fieldErrors && fieldErrors.title?.[0]) {
    setError('title', { message: fieldErrors.title[0] })
  }
  if ('lesson_date' in fieldErrors && fieldErrors.lesson_date?.[0]) {
    setError('lesson_date', { message: fieldErrors.lesson_date[0] })
  }
}

function EnrollmentStatusBadge({ status }: { status: DiscipleshipEnrollment['status'] }) {
  return (
    <span className={`status-badge enrollment-status-badge--${status.toLowerCase()}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {enrollmentStatusLabel(status)}
    </span>
  )
}

function LessonStatusBadge({ status }: { status: DiscipleshipLesson['status'] }) {
  return (
    <span className={`status-badge lesson-status-badge--${status.toLowerCase()}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {lessonStatusLabel(status)}
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

function LessonFormDialog({
  error,
  initialLesson,
  isPending,
  onClose,
  onSubmit,
}: {
  error: string | null
  initialLesson: DiscipleshipLesson | null
  isPending: boolean
  onClose: () => void
  onSubmit: (values: DiscipleshipLessonFormData, setError: UseFormSetError<DiscipleshipLessonFormValues>) => void
}) {
  const {
    formState: { errors },
    handleSubmit,
    register,
    setError,
  } = useForm<DiscipleshipLessonFormValues, unknown, DiscipleshipLessonFormData>({
    defaultValues: initialLesson
      ? {
          title: initialLesson.title,
          lesson_date: initialLesson.lesson_date,
        }
      : discipleshipLessonDefaultValues,
    resolver: zodResolver(discipleshipLessonSchema),
  })

  return (
    <div className="dialog-backdrop" role="presentation">
      <div className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="lesson-dialog-title">
        <h2 id="lesson-dialog-title">{initialLesson ? 'Editar aula' : 'Nova aula'}</h2>

        <form className="lesson-form" onSubmit={(event) => void handleSubmit((values) => onSubmit(values, setError))(event)}>
          <fieldset className="form-section" disabled={isPending}>
            <div className="form-grid">
              <div className="field-group field-group--wide">
                <label htmlFor="lesson-title">Titulo *</label>
                <input
                  id="lesson-title"
                  type="text"
                  aria-invalid={Boolean(errors.title)}
                  aria-describedby={errors.title ? 'lesson-title-error' : undefined}
                  {...register('title')}
                />
                {errors.title ? (
                  <span className="field-error" id="lesson-title-error">
                    {errors.title.message}
                  </span>
                ) : null}
              </div>

              <div className="field-group field-group--wide">
                <label htmlFor="lesson-date">Data *</label>
                <input
                  id="lesson-date"
                  type="date"
                  aria-invalid={Boolean(errors.lesson_date)}
                  aria-describedby={errors.lesson_date ? 'lesson-date-error' : undefined}
                  {...register('lesson_date')}
                />
                {errors.lesson_date ? (
                  <span className="field-error" id="lesson-date-error">
                    {errors.lesson_date.message}
                  </span>
                ) : null}
              </div>
            </div>
          </fieldset>

          {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

          <div className="form-actions">
            <button className="button button--secondary" type="button" disabled={isPending} onClick={onClose}>
              Cancelar
            </button>
            <button className="button button--primary" type="submit" disabled={isPending}>
              <Save size={17} aria-hidden="true" />
              {isPending ? 'Salvando...' : initialLesson ? 'Salvar aula' : 'Criar aula'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function CancelLessonDialog({
  error,
  isPending,
  lesson,
  onClose,
  onConfirm,
}: {
  error: string | null
  isPending: boolean
  lesson: DiscipleshipLesson
  onClose: () => void
  onConfirm: () => void
}) {
  return (
    <div className="dialog-backdrop" role="presentation">
      <div className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="cancel-lesson-dialog-title">
        <h2 id="cancel-lesson-dialog-title">Cancelar a aula "{lesson.title}"?</h2>
        <p>A aula sera preservada no historico e nao sera considerada no calculo futuro de frequencia.</p>

        {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

        <div className="form-actions">
          <button className="button button--secondary" type="button" disabled={isPending} onClick={onClose}>
            Voltar
          </button>
          <button className="button button--primary" type="button" disabled={isPending} onClick={onConfirm}>
            <Ban size={17} aria-hidden="true" />
            {isPending ? 'Cancelando...' : 'Cancelar aula'}
          </button>
        </div>
      </div>
    </div>
  )
}

function CompleteEnrollmentDialog({
  completion,
  enrollment,
  error,
  isPending,
  onClose,
  onConfirm,
}: {
  completion: DiscipleshipCompletionSummary
  enrollment: DiscipleshipEnrollment
  error: string | null
  isPending: boolean
  onClose: () => void
  onConfirm: () => void
}) {
  return (
    <div className="dialog-backdrop" role="presentation">
      <div className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="complete-enrollment-title">
        <h2 id="complete-enrollment-title">Concluir o discipulado de {enrollment.person.display_name}?</h2>
        <p>
          Frequencia final: {formatPercentage(completion.frequency.percentage)}. O minimo exigido e{' '}
          {completion.completion.minimum_percentage}%.
        </p>
        <p>Esta acao registrara a conclusao do discipulado, mas nao tornara a pessoa membro automaticamente.</p>

        {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

        <div className="form-actions">
          <button className="button button--secondary" type="button" disabled={isPending} onClick={onClose}>
            Cancelar
          </button>
          <button className="button button--primary" type="button" disabled={isPending} onClick={onConfirm}>
            <CheckCircle2 size={17} aria-hidden="true" />
            {isPending ? 'Concluindo...' : 'Concluir discipulado'}
          </button>
        </div>
      </div>
    </div>
  )
}

function EnrollmentCompletionCells({
  canCompleteEnrollment,
  canWithdrawEnrollment,
  classId,
  enrollment,
  onCompleteClick,
  onWithdrawClick,
}: {
  canCompleteEnrollment: boolean
  canWithdrawEnrollment: boolean
  classId: number
  enrollment: DiscipleshipEnrollment
  onCompleteClick: (enrollment: DiscipleshipEnrollment, completion: DiscipleshipCompletionSummary) => void
  onWithdrawClick: (enrollment: DiscipleshipEnrollment) => void
}) {
  const { data: completion, isError, isLoading } = useDiscipleshipCompletion(classId, enrollment.id)

  if (isLoading) {
    return (
      <>
        <td>Carregando...</td>
        <td>Carregando...</td>
        <td />
      </>
    )
  }

  if (isError || !completion) {
    return (
      <>
        <td>Nao disponivel</td>
        <td>Nao disponivel</td>
        <td />
      </>
    )
  }

  return (
    <>
      <td>
        <strong>{formatPercentage(completion.frequency.percentage)}</strong>
        <span className="table-muted">
          {completion.frequency.present} presentes | {completion.frequency.absent} ausentes |{' '}
          {completion.frequency.justified} justificadas
        </span>
      </td>
      <td>
        <strong>{completionResultLabel(completion)}</strong>
        <span className="table-muted">
          {completion.frequency.attendance_complete
            ? 'Chamada completa'
            : `${completion.frequency.not_recorded} nao lancadas`}
        </span>
      </td>
      <td>
        <div className="table-actions">
          <span className="table-muted">
            Matricula: {formatDate(enrollment.enrolled_at)}
            {enrollment.withdrawn_at ? ` | Desistencia: ${formatDate(enrollment.withdrawn_at)}` : ''}
            {enrollment.completed_at ? ` | Conclusao: ${formatDate(enrollment.completed_at)}` : ''}
          </span>
          {canCompleteEnrollment && completion.completion.can_complete ? (
            <button
              className="button button--secondary"
              type="button"
              onClick={() => onCompleteClick(enrollment, completion)}
            >
              <CheckCircle2 size={17} aria-hidden="true" />
              Concluir discipulado
            </button>
          ) : null}
          {canWithdrawEnrollment && enrollment.status === 'ENROLLED' ? (
            <button
              className="button button--secondary"
              type="button"
              onClick={() => onWithdrawClick(enrollment)}
            >
              <Ban size={17} aria-hidden="true" />
              Marcar desistencia
            </button>
          ) : null}
        </div>
      </td>
    </>
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
  const { data: lessons = [], isError: isLessonsError, isLoading: isLessonsLoading } = useDiscipleshipLessons(classId)
  const lifecycle = useDiscipleshipClassLifecycle(classId)
  const createEnrollment = useCreateDiscipleshipEnrollment(classId)
  const withdrawEnrollment = useWithdrawDiscipleshipEnrollment(classId)
  const completeEnrollment = useCompleteDiscipleshipEnrollment(classId)
  const createLesson = useCreateDiscipleshipLesson(classId)
  const updateLesson = useUpdateDiscipleshipLesson(classId)
  const cancelLesson = useCancelDiscipleshipLesson(classId)
  const canChange = useCan('DISCIPLESHIP_CLASS_CHANGE')
  const canStart = useCan('DISCIPLESHIP_CLASS_START')
  const canComplete = useCan('DISCIPLESHIP_CLASS_COMPLETE')
  const canCancel = useCan('DISCIPLESHIP_CLASS_CANCEL')
  const canCreateEnrollment = useCan('DISCIPLESHIP_ENROLLMENT_CREATE')
  const canWithdrawEnrollment = useCan('DISCIPLESHIP_ENROLLMENT_WITHDRAW')
  const canCompleteEnrollment = useCan('DISCIPLESHIP_COMPLETION_MANAGE')
  const canCreateLesson = useCan('DISCIPLESHIP_LESSON_CREATE')
  const canChangeLesson = useCan('DISCIPLESHIP_LESSON_CHANGE')
  const canCancelLesson = useCan('DISCIPLESHIP_LESSON_CANCEL')
  const [dialogAction, setDialogAction] = useState<LifecycleAction | null>(null)
  const [isEnrollDialogOpen, setIsEnrollDialogOpen] = useState(false)
  const [withdrawTarget, setWithdrawTarget] = useState<DiscipleshipEnrollment | null>(null)
  const [completeTarget, setCompleteTarget] = useState<{
    enrollment: DiscipleshipEnrollment
    completion: DiscipleshipCompletionSummary
  } | null>(null)
  const [isLessonDialogOpen, setIsLessonDialogOpen] = useState(false)
  const [lessonEditTarget, setLessonEditTarget] = useState<DiscipleshipLesson | null>(null)
  const [lessonCancelTarget, setLessonCancelTarget] = useState<DiscipleshipLesson | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [enrollmentError, setEnrollmentError] = useState<string | null>(null)
  const [completionError, setCompletionError] = useState<string | null>(null)
  const [lessonError, setLessonError] = useState<string | null>(null)
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
  const cancelledLessonsCount = lessons.filter((lesson) => lesson.status === 'CANCELLED').length
  const canManageLessonsInClass = discipleshipClass ? ['PLANNED', 'IN_PROGRESS'].includes(discipleshipClass.status) : false
  const today = new Date().toISOString().slice(0, 10)

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

  const handleCompleteEnrollment = async () => {
    if (!completeTarget) {
      return
    }

    setCompletionError(null)

    try {
      await completeEnrollment.mutateAsync(completeTarget.enrollment.id)
      setCompleteTarget(null)
      setSuccessMessage('Discipulado concluido para esta matricula.')
    } catch (error) {
      setCompletionError(businessErrorMessage(error))
    }
  }

  const handleSubmitLesson = async (
    values: DiscipleshipLessonFormData,
    setError: UseFormSetError<DiscipleshipLessonFormValues>,
  ) => {
    setLessonError(null)

    try {
      if (lessonEditTarget) {
        await updateLesson.mutateAsync({ id: lessonEditTarget.id, payload: values })
        setSuccessMessage('Aula atualizada com sucesso.')
      } else {
        await createLesson.mutateAsync(values)
        setSuccessMessage('Aula criada com sucesso.')
      }
      setLessonEditTarget(null)
      setIsLessonDialogOpen(false)
    } catch (error) {
      if (error instanceof DiscipleshipApiValidationError) {
        applyLessonApiErrors(error, setError)
        return
      }

      setLessonError(businessErrorMessage(error))
    }
  }

  const handleCancelLesson = async () => {
    if (!lessonCancelTarget) {
      return
    }

    setLessonError(null)

    try {
      await cancelLesson.mutateAsync(lessonCancelTarget.id)
      setLessonCancelTarget(null)
      setSuccessMessage('Aula cancelada com sucesso.')
    } catch (error) {
      setLessonError(businessErrorMessage(error))
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
                  <h2>Aulas</h2>
                  <p className="page-heading__description">
                    {discipleshipClass.planned_sessions} previstas | {lessons.length} cadastradas
                    {cancelledLessonsCount > 0 ? ` | ${cancelledLessonsCount} canceladas` : ''}
                  </p>
                </div>
                {canCreateLesson && canManageLessonsInClass ? (
                  <button
                    className="button button--primary"
                    type="button"
                    onClick={() => {
                      setLessonError(null)
                      setLessonEditTarget(null)
                      setIsLessonDialogOpen(true)
                    }}
                  >
                    <CalendarPlus size={17} aria-hidden="true" />
                    Nova aula
                  </button>
                ) : null}
              </div>

              {isLessonsLoading ? (
                <p className="page-heading__description">Carregando aulas...</p>
              ) : isLessonsError ? (
                <p className="page-heading__description">Nao foi possivel carregar as aulas.</p>
              ) : lessons.length > 0 ? (
                <div className="table-shell table-shell--section">
                  <table className="people-table">
                    <thead>
                      <tr>
                        <th scope="col">Aula</th>
                        <th scope="col">Titulo</th>
                        <th scope="col">Data</th>
                        <th scope="col">Status</th>
                        <th scope="col" className="people-table__actions-header">Acao</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lessons.map((lesson, index) => {
                        const canActOnLesson = canManageLessonsInClass && lesson.status === 'SCHEDULED'
                        const isFutureLesson = lesson.lesson_date > today

                        return (
                          <tr key={lesson.id}>
                            <td>Aula {index + 1}</td>
                            <td><strong>{lesson.title}</strong></td>
                            <td>{formatDate(lesson.lesson_date)}</td>
                            <td><LessonStatusBadge status={lesson.status} /></td>
                            <td>
                              <div className="table-actions">
                                {canChangeLesson && canActOnLesson ? (
                                  <button
                                    className="button button--secondary"
                                    type="button"
                                    onClick={() => {
                                      setLessonError(null)
                                      setLessonEditTarget(lesson)
                                      setIsLessonDialogOpen(true)
                                    }}
                                  >
                                    <Edit3 size={17} aria-hidden="true" />
                                    Editar
                                  </button>
                                ) : null}
                                {canCancelLesson && canActOnLesson ? (
                                  <button
                                    className="button button--secondary"
                                    type="button"
                                    onClick={() => {
                                      setLessonError(null)
                                      setLessonCancelTarget(lesson)
                                    }}
                                  >
                                    <Ban size={17} aria-hidden="true" />
                                    Cancelar aula
                                  </button>
                                ) : null}
                                {lesson.status === 'CANCELLED' ? (
                                  <span className="table-muted">Sem chamada - aula cancelada</span>
                                ) : isFutureLesson ? (
                                  <span className="table-muted">Chamada disponivel em {formatDate(lesson.lesson_date)}</span>
                                ) : (
                                  <Link
                                    className="button button--secondary"
                                    to={`/discipulado/${discipleshipClass.id}/aulas/${lesson.id}/chamada`}
                                  >
                                    <ClipboardCheck size={17} aria-hidden="true" />
                                    Fazer chamada
                                  </Link>
                                )}
                              </div>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="page-heading__description">Nenhuma aula cadastrada nesta turma.</p>
              )}
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
                        <th scope="col">Frequencia</th>
                        <th scope="col">Resultado</th>
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
                          <EnrollmentCompletionCells
                            canCompleteEnrollment={canCompleteEnrollment}
                            canWithdrawEnrollment={canWithdrawEnrollment}
                            classId={classId}
                            enrollment={enrollment}
                            onCompleteClick={(targetEnrollment, completion) => {
                              setCompletionError(null)
                              setCompleteTarget({ enrollment: targetEnrollment, completion })
                            }}
                            onWithdrawClick={(targetEnrollment) => {
                              setEnrollmentError(null)
                              setWithdrawTarget(targetEnrollment)
                            }}
                          />
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
          {completeTarget ? (
            <CompleteEnrollmentDialog
              completion={completeTarget.completion}
              enrollment={completeTarget.enrollment}
              error={completionError}
              isPending={completeEnrollment.isPending}
              onClose={() => setCompleteTarget(null)}
              onConfirm={() => void handleCompleteEnrollment()}
            />
          ) : null}
          {isLessonDialogOpen ? (
            <LessonFormDialog
              error={lessonError}
              initialLesson={lessonEditTarget}
              isPending={createLesson.isPending || updateLesson.isPending}
              onClose={() => {
                setLessonError(null)
                setLessonEditTarget(null)
                setIsLessonDialogOpen(false)
              }}
              onSubmit={(values, setError) => void handleSubmitLesson(values, setError)}
            />
          ) : null}
          {lessonCancelTarget ? (
            <CancelLessonDialog
              error={lessonError}
              isPending={cancelLesson.isPending}
              lesson={lessonCancelTarget}
              onClose={() => setLessonCancelTarget(null)}
              onConfirm={() => void handleCancelLesson()}
            />
          ) : null}
        </>
      ) : null}
    </section>
  )
}

export default DiscipleshipClassDetailPage
