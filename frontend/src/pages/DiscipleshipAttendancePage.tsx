import { useMemo, useState } from 'react'
import { ArrowLeft, Save } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { DiscipleshipBusinessError, DiscipleshipHttpError } from '../api/discipleship'
import {
  useDiscipleshipAttendance,
  useDiscipleshipClass,
  useSaveDiscipleshipAttendance,
} from '../hooks/useDiscipleshipClasses'
import type { DiscipleshipAttendanceStatus } from '../types/discipleship'
import { attendanceStatusLabel, formatDate } from '../utils/discipleship'

const ATTENDANCE_OPTIONS: DiscipleshipAttendanceStatus[] = ['PRESENT', 'ABSENT', 'JUSTIFIED']

function businessErrorMessage(error: unknown) {
  if (error instanceof DiscipleshipBusinessError) {
    if (error.code === 'DISCIPLESHIP_ATTENDANCE_CLASS_MISMATCH') {
      return 'Esta matricula nao pertence a turma da aula.'
    }
    if (error.code === 'DISCIPLESHIP_LESSON_NOT_YET_AVAILABLE_FOR_ATTENDANCE') {
      return 'A chamada ainda nao esta disponivel para esta aula.'
    }
    if (error.code === 'CANCELLED_DISCIPLESHIP_LESSON_DOES_NOT_ACCEPT_ATTENDANCE') {
      return 'Aulas canceladas nao aceitam chamada.'
    }
    if (error.code === 'DISCIPLESHIP_ENROLLMENT_NOT_ELIGIBLE_FOR_LESSON') {
      return 'Esta matricula nao e elegivel para esta aula.'
    }
    if (error.code === 'INVALID_DISCIPLESHIP_ATTENDANCE_STATUS') {
      return 'Informe um status de presenca valido.'
    }
  }

  return 'Nao foi possivel salvar a chamada.'
}

function DiscipleshipAttendancePage() {
  const { classId: classIdParam, lessonId: lessonIdParam } = useParams()
  const classId = Number(classIdParam)
  const lessonId = Number(lessonIdParam)
  const isValidId = Number.isInteger(classId) && classId > 0 && Number.isInteger(lessonId) && lessonId > 0
  const { data: discipleshipClass } = useDiscipleshipClass(classId)
  const { data, error, isError, isLoading, refetch } = useDiscipleshipAttendance(classId, lessonId)
  const saveAttendance = useSaveDiscipleshipAttendance(classId, lessonId)
  const [statusOverrides, setStatusOverrides] = useState<Record<number, DiscipleshipAttendanceStatus | undefined>>({})
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const isNotFound = !isValidId || (error instanceof DiscipleshipHttpError && error.status === 404)

  const selectedRecords = useMemo(
    () => {
      if (!data) {
        return []
      }

      return data.students
        .map((student) => ({
          enrollment_id: student.enrollment_id,
          status: statusOverrides[student.enrollment_id] ?? student.attendance?.status,
        }))
        .filter(
          (record): record is { enrollment_id: number; status: DiscipleshipAttendanceStatus } =>
            Boolean(record.status),
        )
    },
    [data, statusOverrides],
  )

  const handleSave = async () => {
    setGeneralError(null)
    setSuccessMessage(null)

    try {
      await saveAttendance.mutateAsync({ records: selectedRecords })
      setSuccessMessage('Chamada salva com sucesso.')
    } catch (saveError) {
      setGeneralError(businessErrorMessage(saveError))
    }
  }

  return (
    <section className="person-profile-page">
      {isLoading && isValidId ? (
        <div className="state-panel"><h1>Carregando chamada...</h1><p>Aguarde enquanto os dados sao carregados.</p></div>
      ) : isNotFound ? (
        <div className="state-panel">
          <h1>Chamada nao encontrada</h1>
          <p>Nao encontramos a aula solicitada.</p>
          <Link className="button button--secondary" to="/discipulado"><ArrowLeft size={17} aria-hidden="true" />Voltar</Link>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h1>Nao foi possivel carregar a chamada.</h1>
          <p>Verifique seu acesso e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : data ? (
        <>
          <nav className="breadcrumbs" aria-label="Breadcrumb">
            <Link to="/discipulado">Discipulado</Link>
            {discipleshipClass ? (
              <>
                <span aria-hidden="true">/</span>
                <Link to={`/discipulado/${classId}`}>{discipleshipClass.name}</Link>
              </>
            ) : null}
            <span aria-hidden="true">/</span>
            <strong>Chamada</strong>
          </nav>

          <header className="profile-header">
            <div className="profile-header__identity">
              <h1>{data.lesson.title}</h1>
              <p className="page-heading__description">
                {formatDate(data.lesson.lesson_date)} | {data.summary.recorded} de {data.summary.eligible} lancados
              </p>
            </div>
            <div className="profile-actions">
              <Link className="button button--secondary" to={`/discipulado/${classId}`}>
                <ArrowLeft size={17} aria-hidden="true" />
                Voltar
              </Link>
              {data.permissions.can_manage_attendance ? (
                <button
                  className="button button--primary"
                  type="button"
                  disabled={saveAttendance.isPending}
                  onClick={() => void handleSave()}
                >
                  <Save size={17} aria-hidden="true" />
                  {saveAttendance.isPending ? 'Salvando...' : 'Salvar chamada'}
                </button>
              ) : null}
            </div>
          </header>

          {successMessage ? <div className="form-alert form-alert--success" role="status">{successMessage}</div> : null}
          {generalError ? <div className="form-alert form-alert--error" role="alert">{generalError}</div> : null}

          <div className="attendance-summary-grid">
            <div><strong>{data.summary.eligible}</strong><span>Alunos</span></div>
            <div><strong>{data.summary.present}</strong><span>Presentes</span></div>
            <div><strong>{data.summary.absent}</strong><span>Ausentes</span></div>
            <div><strong>{data.summary.justified}</strong><span>Justificadas</span></div>
            <div><strong>{data.summary.not_recorded}</strong><span>Nao lancados</span></div>
          </div>

          {data.lesson.status === 'CANCELLED' ? (
            <div className="state-panel state-panel--compact">
              <h2>Aula cancelada</h2>
              <p>Esta aula nao aceita chamada.</p>
            </div>
          ) : null}

          <div className="attendance-list">
            {data.students.length > 0 ? (
              data.students.map((student) => {
                const selectedStatus = statusOverrides[student.enrollment_id] ?? student.attendance?.status

                return (
                  <article className="attendance-row" key={student.enrollment_id}>
                    <div>
                      <strong>{student.person.display_name}</strong>
                      <span>{selectedStatus ? attendanceStatusLabel(selectedStatus) : 'Nao lancado'}</span>
                    </div>
                    <div className="attendance-options" role="group" aria-label={`Chamada de ${student.person.display_name}`}>
                      {ATTENDANCE_OPTIONS.map((option) => (
                        <button
                          key={option}
                          className={`attendance-option${selectedStatus === option ? ' attendance-option--selected' : ''}`}
                          type="button"
                          aria-pressed={selectedStatus === option}
                          disabled={!data.permissions.can_manage_attendance}
                          onClick={() =>
                            setStatusOverrides((current) => ({
                              ...current,
                              [student.enrollment_id]: option,
                            }))
                          }
                        >
                          {attendanceStatusLabel(option)}
                        </button>
                      ))}
                    </div>
                  </article>
                )
              })
            ) : (
              <div className="state-panel state-panel--compact">
                <h2>Nenhum aluno elegivel</h2>
                <p>Esta aula nao possui matriculas elegiveis para chamada.</p>
              </div>
            )}
          </div>
        </>
      ) : null}
    </section>
  )
}

export default DiscipleshipAttendancePage
