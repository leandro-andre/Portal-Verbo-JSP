import { useMemo, useState } from 'react'
import { ArrowLeft, Plus, RefreshCcw, Trash2 } from 'lucide-react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useSchedule, useScheduleCandidates, useScheduleMutations } from '../hooks/useScheduling'
import type { DepartmentRole } from '../types/department'
import type { ScheduleDetail } from '../types/scheduling'

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

function roleAssignments(schedule: ScheduleDetail, role: DepartmentRole) {
  return schedule.assignments.filter((assignment) => assignment.department_membership.role.id === role.id)
}

function ScheduleDetailPage() {
  const scheduleId = Number(useParams().id)
  const [searchParams] = useSearchParams()
  const backQuery = new URLSearchParams()
  const backYear = searchParams.get('year')
  const backMonth = searchParams.get('month')
  const backDepartment = searchParams.get('department')
  if (backYear) backQuery.set('year', backYear)
  if (backMonth) backQuery.set('month', backMonth)
  if (backDepartment) backQuery.set('department', backDepartment)
  const backUrl = `/escalas${backQuery.toString() ? `?${backQuery.toString()}` : ''}`
  const { data: schedule, isError, isLoading, refetch } = useSchedule(scheduleId)
  const [selectedRole, setSelectedRole] = useState<DepartmentRole | null>(null)
  const [candidateSearch, setCandidateSearch] = useState('')
  const { data: candidates = [] } = useScheduleCandidates(
    scheduleId,
    selectedRole?.id,
    Boolean(schedule?.permissions.can_manage && selectedRole),
  )
  const mutations = useScheduleMutations(scheduleId)
  const [error, setError] = useState<string | null>(null)

  const filteredCandidates = useMemo(() => {
    const query = candidateSearch.trim().toLowerCase()
    if (!query) return candidates
    return candidates.filter((candidate) =>
      candidate.department_membership.person.display_name.toLowerCase().includes(query),
    )
  }, [candidateSearch, candidates])

  const run = async (action: () => Promise<unknown>) => {
    setError(null)
    try {
      await action()
      setCandidateSearch('')
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
      <Link className="back-link" to={backUrl}><ArrowLeft size={17} aria-hidden="true" />Voltar para escalas de {backMonth && backYear ? `${backMonth}/${backYear}` : 'mes'}</Link>
      <div className="profile-header">
        <div className="profile-header__identity">
          <h1>{schedule.worship_service.name}</h1>
          <p>{formatDate(schedule.worship_service.date)} - {formatTime(schedule.worship_service.time)} - {schedule.department.nome}</p>
        </div>
        <div className="profile-actions">
          <span className="status-badge lesson-status-badge--scheduled">
            <span className="status-badge__dot" aria-hidden="true" />
            {statusLabel(schedule.status)}
          </span>
          {canManage && schedule.status === 'DRAFT' ? (
            <>
              <button className="button button--primary" type="button" onClick={() => void run(() => mutations.publish.mutateAsync())}>Publicar escala</button>
              <button
                className="button button--secondary"
                type="button"
                onClick={() => {
                  if (window.confirm('Esta acao cancela apenas a escala deste Departamento. O culto continuara na Agenda de Cultos.')) {
                    void run(() => mutations.cancel.mutateAsync())
                  }
                }}
              >
                Cancelar escala
              </button>
            </>
          ) : null}
          {canManage && schedule.status === 'PUBLISHED' ? (
            <>
              <button className="button button--secondary" type="button" onClick={() => void run(() => mutations.reopen.mutateAsync())}>Reabrir para edicao</button>
              <button
                className="button button--secondary"
                type="button"
                onClick={() => {
                  if (window.confirm('Esta acao cancela apenas a escala deste Departamento. O culto continuara na Agenda de Cultos.')) {
                    void run(() => mutations.cancel.mutateAsync())
                  }
                }}
              >
                Cancelar escala
              </button>
            </>
          ) : null}
          {canManage && schedule.status === 'CANCELLED' ? (
            <button className="button button--secondary" type="button" onClick={() => void run(() => mutations.reactivate.mutateAsync())}>
              <RefreshCcw size={17} aria-hidden="true" />
              Reativar como rascunho
            </button>
          ) : null}
        </div>
      </div>

      {error ? <div className="form-alert form-alert--error">{error}</div> : null}
      {schedule.worship_service.status === 'CANCELLED' ? <div className="form-alert form-alert--error">Culto cancelado na Agenda de Cultos.</div> : null}

      <div className="profile-content">
        <section className="profile-section">
          <h2>Montagem por cargo</h2>
          {schedule.active_roles.length === 0 ? (
            <div className="state-panel state-panel--compact">
              <h2>Este departamento ainda nao possui cargos ativos.</h2>
              <p>Cadastre cargos no Departamento antes de montar a escala por funcao.</p>
            </div>
          ) : null}
          {schedule.active_roles.map((role) => {
            const assignments = roleAssignments(schedule, role)
            return (
              <section className="profile-section" key={role.id}>
                <div className="section-heading-row">
                  <div>
                    <h2>{role.name}</h2>
                    <p className="page-heading__description">
                      {assignments.length > 0 ? `${assignments.length} pessoa(s)` : 'Nenhuma pessoa escalada'}
                    </p>
                  </div>
                  {canEditAssignments ? (
                    <button className="button button--primary" type="button" onClick={() => setSelectedRole(role)}>
                      <Plus size={17} aria-hidden="true" />
                      Adicionar {role.name.toLowerCase()}
                    </button>
                  ) : null}
                </div>
                {assignments.length > 0 ? (
                  <div className="table-shell table-shell--section">
                    <table className="people-table">
                      <thead><tr><th>Pessoa</th><th>Cargo</th><th aria-label="Acao" /></tr></thead>
                      <tbody>
                        {assignments.map((assignment) => (
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
                ) : null}
              </section>
            )
          })}
        </section>

        {selectedRole ? (
          <section className="profile-section">
            <div className="section-heading-row">
              <div>
                <h2>Adicionar {selectedRole.name.toLowerCase()}</h2>
                <p className="page-heading__description">Candidatos deste cargo, com elegibilidade calculada pelo backend.</p>
              </div>
              <button className="button button--secondary" type="button" onClick={() => setSelectedRole(null)}>Fechar</button>
            </div>
            <label className="search-field" htmlFor="candidate-search">
              <input
                id="candidate-search"
                placeholder="Buscar pessoa"
                type="search"
                value={candidateSearch}
                onChange={(event) => setCandidateSearch(event.target.value)}
              />
            </label>
            <div className="table-shell table-shell--section">
              <table className="people-table">
                <thead><tr><th>Pessoa</th><th>Elegibilidade</th><th aria-label="Acao" /></tr></thead>
                <tbody>
                  {filteredCandidates.map((candidate) => (
                    <tr key={candidate.department_membership.id}>
                      <td>{candidate.department_membership.person.display_name}</td>
                      <td>{candidate.eligible ? 'Disponivel' : candidate.reasons.map((reason) => reason.message).join(', ')}</td>
                      <td>
                        {candidate.eligible ? (
                          <button className="button button--primary" type="button" onClick={() => void run(() => mutations.addAssignment.mutateAsync(candidate.department_membership.id))}>
                            Adicionar
                          </button>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                  {filteredCandidates.length === 0 ? (
                    <tr><td colSpan={3}>Nenhum candidato encontrado para este cargo.</td></tr>
                  ) : null}
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
