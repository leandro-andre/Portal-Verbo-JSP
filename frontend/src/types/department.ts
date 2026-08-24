export type Department = {
  id: number
  nome: string
  codigo: string
  descricao: string
  ativo: boolean
  criado_em: string
  permissions?: DepartmentPermissions
}

export type DepartmentPermissions = {
  can_manage_department: boolean
  can_manage_roles: boolean
  can_manage_members: boolean
  can_manage_schedules: boolean
}

export type CreateDepartmentInput = {
  nome: string
  codigo: string
  descricao: string
}

export type UpdateDepartmentInput = {
  nome: string
  descricao: string
}

export type DepartmentValidationErrors = Partial<
  Record<string, string[]>
>

export type DepartmentEligibilityReason = {
  code: string
  message: string
}

export type DepartmentEligibilityResult = {
  eligible: boolean
  reasons: DepartmentEligibilityReason[]
}

export type DepartmentRole = {
  id: number
  department: number
  name: string
  code: string
  active: boolean
  can_manage_department: boolean
  can_manage_members: boolean
  can_manage_schedules: boolean
  created_at: string
  updated_at: string
}

export type CreateDepartmentRoleInput = {
  name: string
  can_manage_department: boolean
  can_manage_members: boolean
  can_manage_schedules: boolean
}

export type UpdateDepartmentRoleInput = {
  name?: string
  can_manage_department?: boolean
  can_manage_members?: boolean
  can_manage_schedules?: boolean
}

export type DepartmentMemberPerson = {
  id: number
  full_name: string
  display_name: string
  email: string
  phone: string
}

export type DepartmentMembershipStatus = 'ACTIVE' | 'INACTIVE'

export type DepartmentMembership = {
  id: number
  department: number
  person: DepartmentMemberPerson
  role: DepartmentRole
  status: DepartmentMembershipStatus
  joined_at: string
  left_at: string | null
  eligibility: DepartmentEligibilityResult
  operationally_eligible: boolean
  created_at: string
  updated_at: string
}

export type CreateDepartmentMembershipInput = {
  person_id: number
  role_id: number
  joined_at?: string
}

export type UpdateDepartmentMembershipInput = {
  role_id: number
}
