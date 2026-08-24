import { useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowLeft, CalendarClock } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useCan } from '../hooks/useAuth'
import { useWorshipTemplateMutations, useWorshipTemplates } from '../hooks/useWorship'
import type { WorshipServiceTemplate, WorshipTemplateInput, WorshipWeekday } from '../types/worship'

const weekdays: Array<{ label: string; value: WorshipWeekday }> = [
  { label: 'Segunda-feira', value: 0 },
  { label: 'Terca-feira', value: 1 },
  { label: 'Quarta-feira', value: 2 },
  { label: 'Quinta-feira', value: 3 },
  { label: 'Sexta-feira', value: 4 },
  { label: 'Sabado', value: 5 },
  { label: 'Domingo', value: 6 },
]

const emptyTemplate: WorshipTemplateInput = {
  name: '',
  weekday: 6,
  time: '10:00',
}

function formatTime(value: string) {
  return value.slice(0, 5)
}

function TemplateStatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`status-badge ${active ? 'status-badge--active' : 'status-badge--inactive'}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {active ? 'Ativo' : 'Inativo'}
    </span>
  )
}

function TemplateForm({
  initial,
  isPending,
  onCancel,
  onSubmit,
  submitLabel,
}: {
  initial: WorshipTemplateInput
  isPending: boolean
  onCancel?: () => void
  onSubmit: (payload: WorshipTemplateInput) => void
  submitLabel: string
}) {
  const [form, setForm] = useState<WorshipTemplateInput>(initial)

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit(form)
  }

  return (
    <form className="department-inline-form" onSubmit={handleSubmit}>
      <label className="field-group">
        <span>Nome *</span>
        <input
          required
          value={form.name}
          onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
        />
      </label>
      <label className="field-group">
        <span>Dia da semana *</span>
        <select
          required
          value={form.weekday}
          onChange={(event) => setForm((current) => ({ ...current, weekday: Number(event.target.value) as WorshipWeekday }))}
        >
          {weekdays.map((weekday) => (
            <option key={weekday.value} value={weekday.value}>
              {weekday.label}
            </option>
          ))}
        </select>
      </label>
      <label className="field-group">
        <span>Horario *</span>
        <input
          required
          type="time"
          value={form.time}
          onChange={(event) => setForm((current) => ({ ...current, time: event.target.value }))}
        />
      </label>
      <div className="form-actions">
        {onCancel ? (
          <button className="button button--secondary" type="button" onClick={onCancel}>
            Cancelar
          </button>
        ) : null}
        <button className="button button--primary" disabled={isPending} type="submit">
          {submitLabel}
        </button>
      </div>
    </form>
  )
}

function WorshipTemplatesPage() {
  const canManage = useCan('WORSHIP_SCHEDULE_MANAGE')
  const { data: templates = [], isError, isLoading, refetch } = useWorshipTemplates()
  const mutations = useWorshipTemplateMutations()
  const [editing, setEditing] = useState<WorshipServiceTemplate | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const pending = mutations.create.isPending
    || mutations.update.isPending
    || mutations.deactivate.isPending
    || mutations.reactivate.isPending

  const handleCreate = async (payload: WorshipTemplateInput) => {
    setError(null)
    setMessage(null)
    try {
      await mutations.create.mutateAsync(payload)
      setMessage('Culto padrao criado.')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Nao foi possivel criar o culto padrao.')
    }
  }

  const handleUpdate = async (payload: WorshipTemplateInput) => {
    if (!editing) {
      return
    }
    setError(null)
    setMessage(null)
    try {
      await mutations.update.mutateAsync({ id: editing.id, payload })
      setEditing(null)
      setMessage('Culto padrao atualizado.')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Nao foi possivel atualizar o culto padrao.')
    }
  }

  const handleLifecycle = async (template: WorshipServiceTemplate) => {
    setError(null)
    setMessage(null)
    try {
      if (template.active) {
        await mutations.deactivate.mutateAsync(template.id)
        setMessage('Culto padrao inativado.')
      } else {
        await mutations.reactivate.mutateAsync(template.id)
        setMessage('Culto padrao reativado.')
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Nao foi possivel alterar o culto padrao.')
    }
  }

  return (
    <section className="people-page">
      <div className="breadcrumbs">
        <Link to="/agenda-cultos">Agenda de cultos</Link>
        <span>/</span>
        <strong>Cultos padrao</strong>
      </div>

      <div className="page-heading">
        <div>
          <h1>Cultos padrao</h1>
          <p className="page-heading__description">Regras semanais usadas para gerar novas ocorrencias mensais.</p>
        </div>
        <Link className="button button--secondary" to="/agenda-cultos">
          <ArrowLeft size={17} aria-hidden="true" />
          Voltar para Agenda de Cultos
        </Link>
      </div>

      {message ? <div className="form-alert form-alert--success">{message}</div> : null}
      {error ? <div className="form-alert form-alert--error">{error}</div> : null}

      {canManage ? (
        <div className="profile-content">
          <section className="profile-section">
            <h2>{editing ? 'Editar culto padrao' : 'Novo culto padrao'}</h2>
            {editing ? (
              <p className="page-heading__description">
                Alteracoes afetam apenas novas ocorrencias. Cultos ja gerados nao serao modificados.
              </p>
            ) : null}
            <TemplateForm
              key={editing?.id ?? 'new'}
              initial={editing ? { name: editing.name, weekday: editing.weekday, time: formatTime(editing.time) } : emptyTemplate}
              isPending={pending}
              submitLabel={editing ? 'Salvar culto padrao' : 'Criar culto padrao'}
              onCancel={editing ? () => setEditing(null) : undefined}
              onSubmit={(payload) => void (editing ? handleUpdate(payload) : handleCreate(payload))}
            />
          </section>
        </div>
      ) : null}

      {isLoading ? (
        <div className="state-panel">
          <h2>Carregando cultos padrao...</h2>
          <p>Aguarde enquanto buscamos os dados.</p>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <CalendarClock size={26} aria-hidden="true" />
          <h2>Nao foi possivel carregar os cultos padrao.</h2>
          <p>Verifique sua permissao e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            Tentar novamente
          </button>
        </div>
      ) : templates.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhum culto padrao cadastrado</h2>
          <p>Cadastre os horarios fixos para gerar a agenda mensal.</p>
        </div>
      ) : (
        <div className="table-shell">
          <table className="people-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Dia</th>
                <th>Horario</th>
                <th>Status</th>
                <th className="people-table__actions-header">Acoes</th>
              </tr>
            </thead>
            <tbody>
              {templates.map((template) => (
                <tr key={template.id}>
                  <td><strong>{template.name}</strong></td>
                  <td>{template.weekday_label}</td>
                  <td>{formatTime(template.time)}</td>
                  <td><TemplateStatusBadge active={template.active} /></td>
                  <td>
                    {canManage ? (
                      <div className="table-actions">
                        <button className="button button--secondary" type="button" onClick={() => setEditing(template)}>
                          Editar
                        </button>
                        <button className="button button--secondary" disabled={pending} type="button" onClick={() => void handleLifecycle(template)}>
                          {template.active ? 'Inativar' : 'Reativar'}
                        </button>
                      </div>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default WorshipTemplatesPage
