import { useState } from 'react'
import type { FormEvent } from 'react'
import { CalendarDays, Plus } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useDepartments } from '../hooks/useDepartments'
import { useCreateSchedule, useSchedules } from '../hooks/useScheduling'
import { useWorshipServices } from '../hooks/useWorship'

const months = ['Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

function initialMonth() {
  const today = new Date()
  return { year: today.getFullYear(), month: today.getMonth() + 1 }
}

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

function SchedulesPage() {
  const initial = initialMonth()
  const [year, setYear] = useState(initial.year)
  const [month, setMonth] = useState(initial.month)
  const [departmentId, setDepartmentId] = useState('')
  const [status, setStatus] = useState('')
  const [newDepartmentId, setNewDepartmentId] = useState('')
  const [newWorshipServiceId, setNewWorshipServiceId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { data: schedules = [], isError, isLoading, refetch } = useSchedules(year, month, departmentId, status)
  const { data: departments = [] } = useDepartments()
  const { data: worshipServices = [] } = useWorshipServices(year, month)
  const createMutation = useCreateSchedule(year, month, departmentId, status)
  const activeDepartments = departments.filter((department) => department.ativo)
  const scheduledServices = worshipServices.filter((service) => service.status === 'SCHEDULED')

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    try {
      const schedule = await createMutation.mutateAsync({
        department_id: Number(newDepartmentId),
        worship_service_id: Number(newWorshipServiceId),
      })
      navigate(`/escalas/${schedule.id}`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Nao foi possivel criar a escala.')
    }
  }

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Escalas</h1>
          <p className="page-heading__description">Fundacao operacional de escalas por culto e departamento.</p>
        </div>
      </div>

      {error ? <div className="form-alert form-alert--error">{error}</div> : null}

      <div className="people-toolbar">
        <label className="status-filter">
          Mes
          <select value={month} onChange={(event) => setMonth(Number(event.target.value))}>
            {months.map((label, index) => <option key={label} value={index + 1}>{label}</option>)}
          </select>
        </label>
        <label className="status-filter">
          Ano
          <select value={year} onChange={(event) => setYear(Number(event.target.value))}>
            {[2026, 2027, 2028].map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <label className="status-filter">
          Departamento
          <select value={departmentId} onChange={(event) => setDepartmentId(event.target.value)}>
            <option value="">Todos</option>
            {departments.map((department) => <option key={department.id} value={department.id}>{department.nome}</option>)}
          </select>
        </label>
        <label className="status-filter">
          Status
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">Todos</option>
            <option value="DRAFT">Rascunho</option>
            <option value="PUBLISHED">Publicada</option>
            <option value="CANCELLED">Cancelada</option>
          </select>
        </label>
      </div>

      <div className="profile-content">
        <section className="profile-section">
          <h2>Nova escala</h2>
          <form className="department-inline-form" onSubmit={handleCreate}>
            <label className="field-group">
              <span>Culto</span>
              <select required value={newWorshipServiceId} onChange={(event) => setNewWorshipServiceId(event.target.value)}>
                <option value="">Selecione</option>
                {scheduledServices.map((service) => (
                  <option key={service.id} value={service.id}>
                    {formatDate(service.date)} - {formatTime(service.time)} - {service.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field-group">
              <span>Departamento</span>
              <select required value={newDepartmentId} onChange={(event) => setNewDepartmentId(event.target.value)}>
                <option value="">Selecione</option>
                {activeDepartments.map((department) => <option key={department.id} value={department.id}>{department.nome}</option>)}
              </select>
            </label>
            <button className="button button--primary" disabled={createMutation.isPending} type="submit">
              <Plus size={17} aria-hidden="true" />
              Nova escala
            </button>
          </form>
        </section>
      </div>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando escalas...</h2><p>Aguarde enquanto buscamos os dados.</p></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <CalendarDays size={26} aria-hidden="true" />
          <h2>Nao foi possivel carregar as escalas.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : schedules.length === 0 ? (
        <div className="state-panel"><h2>Nenhuma escala encontrada</h2><p>Crie uma escala para um culto futuro e departamento ativo.</p></div>
      ) : (
        <div className="table-shell">
          <table className="people-table">
            <thead>
              <tr>
                <th>Culto</th>
                <th>Departamento</th>
                <th>Status</th>
                <th>Pessoas</th>
                <th aria-label="Acao" />
              </tr>
            </thead>
            <tbody>
              {schedules.map((schedule) => (
                <tr key={schedule.id}>
                  <td>
                    <strong>{formatDate(schedule.worship_service.date)} - {formatTime(schedule.worship_service.time)}</strong>
                    <span className="table-muted">{schedule.worship_service.name}</span>
                  </td>
                  <td>{schedule.department.nome}</td>
                  <td>{statusLabel(schedule.status)}</td>
                  <td>{schedule.assignments_count} pessoas</td>
                  <td><Link className="button button--secondary" to={`/escalas/${schedule.id}`}>Ver</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default SchedulesPage
