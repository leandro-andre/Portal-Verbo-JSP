import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowLeft, Edit3, Plus, RefreshCcw, Save } from 'lucide-react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { DepartmentBusinessError, DepartmentHttpError } from '../api/departments'
import { useCan } from '../hooks/useAuth'
import {
  useDepartment,
  useDepartmentEligiblePeople,
  useDepartmentLifecycle,
  useDepartmentMembershipMutations,
  useDepartmentMemberships,
  useDepartmentRoleMutations,
  useDepartmentRoles,
  useDepartmentScheduleRequirementMutations,
  useDepartmentScheduleRequirements,
} from '../hooks/useDepartments'
import type { Department, DepartmentRole } from '../types/department'
import type { DepartmentScheduleRequirement } from '../types/scheduling'

function formatDate(value: string | null) {
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

function RoleStatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`status-badge ${active ? 'person-status-badge--active' : 'person-status-badge--inactive'}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {active ? 'Ativo' : 'Inativo'}
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
  if (error instanceof DepartmentBusinessError) {
    const messages: Record<string, string> = {
      INVALID_DEPARTMENT_TRANSITION: 'Esta acao nao esta disponivel para o status atual do departamento.',
      PERSON_IS_NOT_ACTIVE_MEMBER: 'A pessoa selecionada precisa ter membresia ativa.',
      DEPARTMENT_ROLE_MISMATCH: 'O cargo selecionado nao pertence a este departamento.',
      DEPARTMENT_NOT_ACTIVE: 'O departamento precisa estar ativo para esta acao.',
      DEPARTMENT_ROLE_NOT_ACTIVE: 'O cargo selecionado precisa estar ativo.',
      DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS: 'Esta pessoa ja esta vinculada a este departamento.',
      INVALID_DEPARTMENT_ROLE_TRANSITION: 'Esta transicao de cargo nao esta disponivel.',
      INVALID_DEPARTMENT_MEMBERSHIP_TRANSITION: 'Esta transicao de pessoa no departamento nao esta disponivel.',
      SCHEDULE_REQUIREMENT_ALREADY_EXISTS: 'Este cargo ja possui configuracao de escala.',
      SCHEDULE_REQUIREMENT_ROLE_MISMATCH: 'O cargo informado nao pertence a este departamento.',
      SCHEDULE_REQUIREMENT_ROLE_INACTIVE: 'Cargo inativo nao pode receber configuracao ativa.',
      INVALID_SCHEDULE_REQUIREMENT_QUANTITIES: 'O recomendado deve ser maior ou igual ao minimo.',
      INVALID_SCHEDULE_REQUIREMENT_TRANSITION: 'Esta transicao de configuracao nao esta disponivel.',
    }
    return messages[error.code] ?? error.message
  }
  return 'Nao foi possivel concluir a acao.'
}

function RoleForm({
  isPending,
  onSubmit,
}: {
  isPending: boolean
  onSubmit: (payload: { name: string; can_manage_department: boolean; can_manage_members: boolean; can_manage_schedules: boolean }) => void
}) {
  const [name, setName] = useState('')
  const [canManageDepartment, setCanManageDepartment] = useState(false)
  const [canManageMembers, setCanManageMembers] = useState(false)
  const [canManageSchedules, setCanManageSchedules] = useState(false)

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit({
      name,
      can_manage_department: canManageDepartment,
      can_manage_members: canManageMembers,
      can_manage_schedules: canManageSchedules,
    })
    setName('')
    setCanManageDepartment(false)
    setCanManageMembers(false)
    setCanManageSchedules(false)
  }

  return (
    <form className="department-inline-form" onSubmit={handleSubmit}>
      <label className="form-field">
        <span>Nome do cargo</span>
        <input value={name} onChange={(event) => setName(event.target.value)} required />
      </label>
      <label className="checkbox-field">
        <input
          type="checkbox"
          checked={canManageDepartment}
          onChange={(event) => setCanManageDepartment(event.target.checked)}
        />
        <span>Gerencia dados do departamento</span>
      </label>
      <label className="checkbox-field">
        <input
          type="checkbox"
          checked={canManageMembers}
          onChange={(event) => setCanManageMembers(event.target.checked)}
        />
        <span>Gerencia cargos e pessoas</span>
      </label>
      <label className="checkbox-field">
        <input
          type="checkbox"
          checked={canManageSchedules}
          onChange={(event) => setCanManageSchedules(event.target.checked)}
        />
        <span>Gerencia escalas</span>
      </label>
      <button className="button button--primary" type="submit" disabled={isPending}>
        <Plus size={17} aria-hidden="true" />
        {isPending ? 'Criando...' : 'Criar cargo'}
      </button>
    </form>
  )
}

function RequirementDialog({
  isPending,
  mode,
  onClose,
  onSubmit,
  role,
  requirement,
}: {
  isPending: boolean
  mode: 'create' | 'edit'
  onClose: () => void
  onSubmit: (payload: { minimum_quantity: number; recommended_quantity: number }) => void
  role: DepartmentRole
  requirement: DepartmentScheduleRequirement | null
}) {
  const [minimumQuantity, setMinimumQuantity] = useState(String(requirement?.minimum_quantity ?? 1))
  const [recommendedQuantity, setRecommendedQuantity] = useState(String(requirement?.recommended_quantity ?? requirement?.minimum_quantity ?? 1))

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit({
      minimum_quantity: Number(minimumQuantity),
      recommended_quantity: Number(recommendedQuantity),
    })
  }

  return (
    <div className="dialog-backdrop" role="presentation">
      <form className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="schedule-requirement-title" onSubmit={handleSubmit}>
        <h2 id="schedule-requirement-title">{mode === 'create' ? 'Configurar' : 'Editar'} {role.name}</h2>
        <label className="form-field">
          <span>Quantidade minima</span>
          <input min="0" type="number" value={minimumQuantity} onChange={(event) => setMinimumQuantity(event.target.value)} required />
        </label>
        <label className="form-field">
          <span>Quantidade recomendada</span>
          <input min="0" type="number" value={recommendedQuantity} onChange={(event) => setRecommendedQuantity(event.target.value)} required />
        </label>
        <div className="dialog-copy">
          <p>Minimo bloqueia publicacao quando nao atendido.</p>
          <p>Recomendado gera aviso, mas nao bloqueia.</p>
        </div>
        <div className="form-actions">
          <button className="button button--secondary" type="button" disabled={isPending} onClick={onClose}>Cancelar</button>
          <button className="button button--primary" type="submit" disabled={isPending}>
            <Save size={17} aria-hidden="true" />
            {isPending ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </form>
    </div>
  )
}

function MembershipForm({
  activeRoles,
  candidates,
  isPending,
  onSubmit,
}: {
  activeRoles: DepartmentRole[]
  candidates: Array<{ id: number; display_name: string }>
  isPending: boolean
  onSubmit: (payload: { person_id: number; role_id: number }) => void
}) {
  const [personId, setPersonId] = useState('')
  const [roleId, setRoleId] = useState('')

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit({
      person_id: Number(personId),
      role_id: Number(roleId),
    })
    setPersonId('')
    setRoleId('')
  }

  return (
    <form className="department-inline-form" onSubmit={handleSubmit}>
      <label className="form-field">
        <span>Pessoa</span>
        <select value={personId} onChange={(event) => setPersonId(event.target.value)} required>
          <option value="">Selecione</option>
          {candidates.map((person) => (
            <option key={person.id} value={person.id}>{person.display_name}</option>
          ))}
        </select>
      </label>
      <label className="form-field">
        <span>Cargo</span>
        <select value={roleId} onChange={(event) => setRoleId(event.target.value)} required>
          <option value="">Selecione</option>
          {activeRoles.map((role) => (
            <option key={role.id} value={role.id}>{role.name}</option>
          ))}
        </select>
      </label>
      <button className="button button--primary" type="submit" disabled={isPending || activeRoles.length === 0}>
        <Plus size={17} aria-hidden="true" />
        {isPending ? 'Adicionando...' : 'Adicionar pessoa'}
      </button>
    </form>
  )
}

function DepartmentDetailPage() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const departmentId = Number(id)
  const isValidId = Number.isInteger(departmentId) && departmentId > 0
  const { data: department, error, isError, isLoading, refetch } = useDepartment(departmentId)
  const rolesQuery = useDepartmentRoles(departmentId, Boolean(department))
  const membershipsQuery = useDepartmentMemberships(departmentId, Boolean(department))
  const eligiblePeopleQuery = useDepartmentEligiblePeople(departmentId, Boolean(department?.permissions?.can_manage_members))
  const requirementsQuery = useDepartmentScheduleRequirements(departmentId, Boolean(department))
  const roleMutations = useDepartmentRoleMutations(departmentId)
  const requirementMutations = useDepartmentScheduleRequirementMutations(departmentId)
  const membershipMutations = useDepartmentMembershipMutations(departmentId)
  const lifecycle = useDepartmentLifecycle(departmentId)
  const canChangeGlobally = useCan('DEPARTMENT_CHANGE')
  const canDeactivate = useCan('DEPARTMENT_DEACTIVATE')
  const canReactivate = useCan('DEPARTMENT_REACTIVATE')
  const canManageSchedulesGlobally = useCan('SCHEDULE_MANAGE')
  const canChange = Boolean(department?.permissions?.can_manage_department || canChangeGlobally)
  const canManageRoles = Boolean(department?.permissions?.can_manage_roles)
  const canManageMembers = Boolean(department?.permissions?.can_manage_members)
  const canManageSchedules = Boolean(department?.permissions?.can_manage_schedules || canManageSchedulesGlobally)
  const [dialogMode, setDialogMode] = useState<'deactivate' | 'reactivate' | null>(null)
  const [requirementDialog, setRequirementDialog] = useState<{
    mode: 'create' | 'edit'
    role: DepartmentRole
    requirement: DepartmentScheduleRequirement | null
  } | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState(() => {
    const state = location.state as { successMessage?: string } | null
    return state?.successMessage ?? null
  })
  const isNotFound = !isValidId || (error instanceof DepartmentHttpError && error.status === 404)
  const isActionPending = lifecycle.deactivate.isPending || lifecycle.reactivate.isPending
  const roles = rolesQuery.data ?? []
  const memberships = membershipsQuery.data ?? []
  const activeRoles = roles.filter((role) => role.active)
  const requirements = requirementsQuery.data ?? []
  const requirementsByRole = new Map(requirements.map((requirement) => [requirement.role.id, requirement]))

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

  const runAction = async (action: () => Promise<unknown>, message: string) => {
    setActionError(null)
    try {
      await action()
      setSuccessMessage(message)
    } catch (mutationError) {
      setActionError(businessErrorMessage(mutationError))
    }
  }

  const handleRequirementSubmit = async (payload: { minimum_quantity: number; recommended_quantity: number }) => {
    if (!requirementDialog) {
      return
    }
    await runAction(
      () => requirementDialog.requirement
        ? requirementMutations.update.mutateAsync({ requirementId: requirementDialog.requirement.id, payload })
        : requirementMutations.create.mutateAsync({ role_id: requirementDialog.role.id, ...payload }),
      'Configuracao de escala salva.',
    )
    setRequirementDialog(null)
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
          {actionError ? <div className="form-alert form-alert--error" role="alert">{actionError}</div> : null}

          <div className="profile-content">
            <section className="profile-section">
              <h2>Visao geral</h2>
              <dl className="profile-details">
                <DetailItem label="Nome" value={department.nome} />
                <DetailItem label="Codigo" value={department.codigo} />
                <DetailItem label="Status" value={department.ativo ? 'Ativo' : 'Inativo'} />
                <DetailItem label="Criado em" value={formatDate(department.criado_em)} />
              </dl>
              <p className="page-heading__description">{department.descricao || 'Sem descricao cadastrada.'}</p>
            </section>

            <section className="profile-section">
              <div className="section-heading-row">
                <h2>Cargos</h2>
                {rolesQuery.isFetching ? <span className="table-muted">Atualizando...</span> : null}
              </div>
              {canManageRoles ? (
                <RoleForm
                  isPending={roleMutations.create.isPending}
                  onSubmit={(payload) =>
                    void runAction(
                      () => roleMutations.create.mutateAsync(payload),
                      'Cargo criado com sucesso.',
                    )
                  }
                />
              ) : null}
              <div className="table-shell table-shell--section">
                <table className="people-table">
                  <thead>
                    <tr>
                      <th>Nome</th>
                      <th>Codigo</th>
                      <th>Status</th>
                      <th>Permissoes</th>
                      {canManageRoles ? <th className="people-table__actions-header">Acoes</th> : null}
                    </tr>
                  </thead>
                  <tbody>
                    {roles.map((role) => (
                      <tr key={role.id}>
                        <td>{role.name}</td>
                        <td>{role.code}</td>
                        <td><RoleStatusBadge active={role.active} /></td>
                        <td>
                          {[
                            role.can_manage_department ? 'Departamento' : null,
                            role.can_manage_members ? 'Cargos e pessoas' : null,
                            role.can_manage_schedules ? 'Escalas' : null,
                          ].filter(Boolean).join(', ') || '-'}
                        </td>
                        {canManageRoles ? (
                          <td>
                            <div className="table-actions">
                              <button
                                className="button button--secondary"
                                type="button"
                                onClick={() =>
                                  void runAction(
                                    () => roleMutations.update.mutateAsync({
                                      roleId: role.id,
                                      payload: {
                                        name: role.name,
                                        can_manage_department: !role.can_manage_department,
                                        can_manage_members: role.can_manage_members,
                                        can_manage_schedules: role.can_manage_schedules,
                                      },
                                    }),
                                    'Cargo atualizado com sucesso.',
                                  )
                                }
                              >
                                <Save size={16} aria-hidden="true" />
                                Departamento
                              </button>
                              <button
                                className="button button--secondary"
                                type="button"
                                onClick={() =>
                                  void runAction(
                                    () => roleMutations.update.mutateAsync({
                                      roleId: role.id,
                                      payload: {
                                        name: role.name,
                                        can_manage_department: role.can_manage_department,
                                        can_manage_members: !role.can_manage_members,
                                        can_manage_schedules: role.can_manage_schedules,
                                      },
                                    }),
                                    'Cargo atualizado com sucesso.',
                                  )
                                }
                              >
                                <Save size={16} aria-hidden="true" />
                                Pessoas
                              </button>
                              <button
                                className="button button--secondary"
                                type="button"
                                onClick={() =>
                                  void runAction(
                                    () => roleMutations.update.mutateAsync({
                                      roleId: role.id,
                                      payload: {
                                        name: role.name,
                                        can_manage_department: role.can_manage_department,
                                        can_manage_members: role.can_manage_members,
                                        can_manage_schedules: !role.can_manage_schedules,
                                      },
                                    }),
                                    'Cargo atualizado com sucesso.',
                                  )
                                }
                              >
                                <Save size={16} aria-hidden="true" />
                                Escalas
                              </button>
                              <button
                                className="button button--secondary"
                                type="button"
                                onClick={() =>
                                  void runAction(
                                    () => role.active
                                      ? roleMutations.deactivate.mutateAsync(role.id)
                                      : roleMutations.reactivate.mutateAsync(role.id),
                                    role.active ? 'Cargo inativado com sucesso.' : 'Cargo reativado com sucesso.',
                                  )
                                }
                              >
                                <RefreshCcw size={16} aria-hidden="true" />
                                {role.active ? 'Inativar' : 'Reativar'}
                              </button>
                            </div>
                          </td>
                        ) : null}
                      </tr>
                    ))}
                    {roles.length === 0 ? (
                      <tr><td colSpan={canManageRoles ? 5 : 4} className="table-muted">Nenhum cargo cadastrado.</td></tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="profile-section">
              <div className="section-heading-row">
                <h2>Configuracao de escala</h2>
                {requirementsQuery.isFetching ? <span className="table-muted">Atualizando...</span> : null}
              </div>
              <div className="table-shell table-shell--section">
                <table className="people-table">
                  <thead>
                    <tr>
                      <th>Cargo</th>
                      <th>Minimo</th>
                      <th>Recomendado</th>
                      <th>Status</th>
                      {canManageSchedules ? <th className="people-table__actions-header">Acoes</th> : null}
                    </tr>
                  </thead>
                  <tbody>
                    {activeRoles.map((role) => {
                      const requirement = requirementsByRole.get(role.id) ?? null
                      return (
                        <tr key={role.id}>
                          <td>{role.name}</td>
                          <td>{requirement ? requirement.minimum_quantity : 'Sem configuracao'}</td>
                          <td>{requirement ? requirement.recommended_quantity : 'Sem configuracao'}</td>
                          <td>{requirement ? requirement.active ? 'Ativa' : 'Inativa' : '-'}</td>
                          {canManageSchedules ? (
                            <td>
                              <div className="table-actions">
                                <button
                                  className="button button--secondary"
                                  type="button"
                                  onClick={() => setRequirementDialog({ mode: requirement ? 'edit' : 'create', role, requirement })}
                                >
                                  <Save size={16} aria-hidden="true" />
                                  {requirement ? 'Editar' : 'Configurar'}
                                </button>
                                {requirement ? (
                                  <button
                                    className="button button--secondary"
                                    type="button"
                                    onClick={() =>
                                      void runAction(
                                        () => requirement.active
                                          ? requirementMutations.deactivate.mutateAsync(requirement.id)
                                          : requirementMutations.reactivate.mutateAsync(requirement.id),
                                        requirement.active ? 'Configuracao inativada.' : 'Configuracao reativada.',
                                      )
                                    }
                                  >
                                    <RefreshCcw size={16} aria-hidden="true" />
                                    {requirement.active ? 'Inativar' : 'Reativar'}
                                  </button>
                                ) : null}
                              </div>
                            </td>
                          ) : null}
                        </tr>
                      )
                    })}
                    {activeRoles.length === 0 ? (
                      <tr><td colSpan={canManageSchedules ? 5 : 4} className="table-muted">Nenhum cargo ativo para configurar.</td></tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="profile-section">
              <div className="section-heading-row">
                <h2>Pessoas</h2>
                {membershipsQuery.isFetching ? <span className="table-muted">Atualizando...</span> : null}
              </div>
              {canManageMembers ? (
                <MembershipForm
                  activeRoles={activeRoles}
                  candidates={eligiblePeopleQuery.data ?? []}
                  isPending={membershipMutations.create.isPending}
                  onSubmit={(payload) =>
                    void runAction(
                      () => membershipMutations.create.mutateAsync(payload),
                      'Pessoa adicionada ao departamento.',
                    )
                  }
                />
              ) : null}
              <div className="table-shell table-shell--section">
                <table className="people-table">
                  <thead>
                    <tr>
                      <th>Pessoa</th>
                      <th>Cargo</th>
                      <th>Status</th>
                      <th>Elegibilidade</th>
                      <th>Entrada</th>
                      {canManageMembers ? <th className="people-table__actions-header">Acoes</th> : null}
                    </tr>
                  </thead>
                  <tbody>
                    {memberships.map((membership) => (
                      <tr key={membership.id}>
                        <td>{membership.person.display_name}</td>
                        <td>
                          <select
                            disabled={!canManageMembers || membership.status !== 'ACTIVE'}
                            value={membership.role.id}
                            onChange={(event) =>
                              void runAction(
                                () => membershipMutations.update.mutateAsync({
                                  membershipId: membership.id,
                                  payload: { role_id: Number(event.target.value) },
                                }),
                                'Cargo da pessoa atualizado.',
                              )
                            }
                          >
                            {activeRoles.map((role) => (
                              <option key={role.id} value={role.id}>{role.name}</option>
                            ))}
                            {!membership.role.active ? (
                              <option value={membership.role.id}>{membership.role.name}</option>
                            ) : null}
                          </select>
                        </td>
                        <td>{membership.status === 'ACTIVE' ? 'Ativa' : 'Inativa'}</td>
                        <td>
                          {membership.eligibility.eligible ? 'Apta' : (
                            <span title={membership.eligibility.reasons.map((reason) => reason.message).join('\n')}>
                              Inelegivel - {membership.eligibility.reasons.map((reason) => reason.message).join(' ')}
                            </span>
                          )}
                        </td>
                        <td>{formatDate(membership.joined_at)}</td>
                        {canManageMembers ? (
                          <td>
                            <button
                              className="button button--secondary"
                              type="button"
                              onClick={() =>
                                void runAction(
                                  () => membership.status === 'ACTIVE'
                                    ? membershipMutations.deactivate.mutateAsync(membership.id)
                                    : membershipMutations.reactivate.mutateAsync(membership.id),
                                  membership.status === 'ACTIVE'
                                    ? 'Pessoa inativada no departamento.'
                                    : 'Pessoa reativada no departamento.',
                                )
                              }
                            >
                              <RefreshCcw size={16} aria-hidden="true" />
                              {membership.status === 'ACTIVE' ? 'Inativar' : 'Reativar'}
                            </button>
                          </td>
                        ) : null}
                      </tr>
                    ))}
                    {memberships.length === 0 ? (
                      <tr><td colSpan={canManageMembers ? 6 : 5} className="table-muted">Nenhuma pessoa vinculada.</td></tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
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
          {requirementDialog ? (
            <RequirementDialog
              isPending={requirementMutations.create.isPending || requirementMutations.update.isPending}
              mode={requirementDialog.mode}
              onClose={() => setRequirementDialog(null)}
              onSubmit={(payload) => void handleRequirementSubmit(payload)}
              requirement={requirementDialog.requirement}
              role={requirementDialog.role}
            />
          ) : null}
        </>
      ) : null}
    </section>
  )
}

export default DepartmentDetailPage
