import { useState } from 'react'
import { ArrowLeft, Plus, RefreshCcw, Trash2 } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { useSchedule, useScheduleCandidates, useScheduleMutations } from '../hooks/useScheduling'

function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  return `${day}/${month}/${year}`
}

function formatTime(value: string) {
  return value.slice(0, 5)
}

function statusLabel(status: string) {
  return status === 'DRAFT' ? 'Rascunho' : status === 'PUBLISHED' ? 'Publicada' : 'Cancelada'
}

function ScheduleDetailPage() {
  const scheduleId = Number(useParams().id)
  const { data: schedule, isError, isLoading, refetch } = useSchedule(scheduleId)
  const { data: candidates = [] } = useScheduleCandidates(scheduleId, Boolean(schedule?.permissions.can_manage))
  const mutations = useScheduleMutations(scheduleId)
  const [error, setError] = useState<string | null>(null)

  const run = async (action: () => Promise<unknown>) => {
    setError(null)
    try {
      await action()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Nao foi possivel concluir a acao.')
    }
  }

  if (isLoading) {
    return <section className="people-page"><div className="state-panel"><h2>Carregando escala...</h2></div></section>
  }
  if (isError || !schedule) {
    return (
      <section className="people-page">
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar a escala.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      </section>
    )
  }

  const canManage = schedule.permissions.can_manage
  const canEditAssignments = schedule.permissions.can_edit_assignments

  return (
    <section className="person-profile-page">
      <Link className="back-link" to="/escalas"><ArrowLeft size={17} aria-hidden="true" />Voltar para escalas</Link>
      <div className="profile-header">
        <div className="profile-header__identity">
          <h1>{schedule.department.nome}</h1>
          <p>{formatDate(schedule.worship_service.date)} - {formatTime(schedule.worship_service.time)} - {schedule.worship_service.name}</p>
        </div>
        <div className="profile-actions">
          {canManage && schedule.status === 'DRAFT' ? (
            <>
              <button className="button button--primary" type="button" onClick={() => void run(() => mutations.publish.mutateAsync())}>Publicar</button>
              <button className="button button--secondary" type="button" onClick={() => void run(() => mutations.cancel.mutateAsync())}>Cancelar</button>
            </>
          ) : null}
          {canManage && schedule.status === 'PUBLISHED' ? (
            <>
              <button className="button button--secondary" type="button" onClick={() => void run(() => mutations.reopen.mutateAsync())}>Reabrir</button>
              <button className="button button--secondary" type="button" onClick={() => void run(() => mutations.cancel.mutateAsync())}>Cancelar</button>
            </>
          ) : null}
          {canManage && schedule.status === 'CANCELLED' ? (
            <button className="button button--secondary" type="button" onClick={() => void run(() => mutations.reactivate.mutateAsync())}>
              <RefreshCcw size={17} aria-hidden="true" />
              Reativar para rascunho
            </button>
          ) : null}
        </div>
      </div>

      {error ? <div className="form-alert form-alert--error">{error}</div> : null}

      <div className="profile-content">
        <section className="profile-section">
          <h2>Dados da escala</h2>
          <dl className="profile-details">
            <div className="profile-detail"><dt>Status</dt><dd>{statusLabel(schedule.status)}</dd></div>
            <div className="profile-detail"><dt>Culto</dt><dd>{schedule.worship_service.name}</dd></div>
            <div className="profile-detail"><dt>Departamento</dt><dd>{schedule.department.nome}</dd></div>
            <div className="profile-detail"><dt>Criada por</dt><dd>{schedule.created_by?.display_name ?? '-'}</dd></div>
            {schedule.worship_service.status === 'CANCELLED' ? <div className="form-alert form-alert--error">Culto cancelado</div> : null}
          </dl>
        </section>

        <section className="profile-section">
          <h2>Pessoas escaladas</h2>
          {schedule.assignments.length === 0 ? (
            <p className="page-heading__description">Nenhuma pessoa escalada.</p>
          ) : (
            <div className="table-shell table-shell--section">
              <table className="people-table">
                <thead><tr><th>Pessoa</th><th>Cargo</th><th aria-label="Acao" /></tr></thead>
                <tbody>
                  {schedule.assignments.map((assignment) => (
                    <tr key={assignment.id}>
                      <td>{assignment.department_membership.person.display_name}</td>
                      <td>{assignment.department_membership.role.name}</td>
                      <td>
                        {canEditAssignments ? (
                          <button className="button button--secondary" type="button" onClick={() => void run(() => mutations.deleteAssignment.mutateAsync(assignment.id))}>
                            <Trash2 size={16} aria-hidden="true" />
                            Remover
                          </button>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {canManage ? (
          <section className="profile-section">
            <h2>Candidatos</h2>
            <div className="table-shell table-shell--section">
              <table className="people-table">
                <thead><tr><th>Pessoa</th><th>Cargo</th><th>Elegibilidade</th><th aria-label="Acao" /></tr></thead>
                <tbody>
                  {candidates.map((candidate) => (
                    <tr key={candidate.department_membership.id}>
                      <td>{candidate.department_membership.person.display_name}</td>
                      <td>{candidate.department_membership.role.name}</td>
                      <td>{candidate.eligible ? 'Apta' : candidate.reasons.map((reason) => reason.message).join(', ')}</td>
                      <td>
                        {canEditAssignments && candidate.eligible ? (
                          <button className="button button--primary" type="button" onClick={() => void run(() => mutations.addAssignment.mutateAsync(candidate.department_membership.id))}>
                            <Plus size={16} aria-hidden="true" />
                            Adicionar
                          </button>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
      </div>
    </section>
  )
}

export default ScheduleDetailPage
