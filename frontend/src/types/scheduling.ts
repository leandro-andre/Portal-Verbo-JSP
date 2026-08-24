import type { Department, DepartmentMembership, DepartmentRole } from './department'
import type { WorshipService } from './worship'

export type ScheduleStatus = 'DRAFT' | 'PUBLISHED' | 'CANCELLED'

export type ScheduleSummary = {
  id: number
  department: Pick<Department, 'id' | 'nome' | 'codigo' | 'ativo'>
  worship_service: Pick<WorshipService, 'id' | 'name' | 'date' | 'time' | 'kind' | 'status'>
  status: ScheduleStatus
  created_by: { id: number; username: string; display_name: string } | null
  created_at: string
  updated_at: string
  permissions: {
    can_manage: boolean
    can_edit_assignments: boolean
  }
  assignments_count: number
}

export type ScheduleAssignment = {
  id: number
  department_membership: DepartmentMembership
  created_by: { id: number; username: string; display_name: string } | null
  created_at: string
}

export type ScheduleDetail = ScheduleSummary & {
  assignments: ScheduleAssignment[]
  active_roles: DepartmentMembership['role'][]
  validation_summary: {
    valid: boolean
    can_publish: boolean
    blocking_count: number
    warning_count: number
  }
}

export type ScheduleCreateInput = {
  department_id: number
  worship_service_id: number
}

export type ScheduleCandidate = {
  department_membership: DepartmentMembership
  eligible: boolean
  reasons: Array<{ code: string; message: string }>
}

export type MonthlyScheduleSummary = {
  services: number
  cancelled_services: number
  operational_services: number
  published: number
  draft: number
  cancelled_schedules: number
  without_schedule: number
}

export type MonthlyScheduleItem = {
  worship_service: ScheduleSummary['worship_service']
  schedule: ScheduleSummary | null
  validation_status: 'OK' | 'WARNING' | 'BLOCKED' | null
}

export type MonthlySchedule = {
  year: number
  month: number
  department: ScheduleSummary['department']
  permissions: {
    can_manage: boolean
  }
  summary: MonthlyScheduleSummary
  items: MonthlyScheduleItem[]
}

export type DepartmentScheduleRequirement = {
  id: number
  department: number
  role: DepartmentRole
  minimum_quantity: number
  recommended_quantity: number
  active: boolean
  created_at: string
  updated_at: string
}

export type CreateDepartmentScheduleRequirementInput = {
  role_id: number
  minimum_quantity: number
  recommended_quantity: number
}

export type UpdateDepartmentScheduleRequirementInput = {
  minimum_quantity?: number
  recommended_quantity?: number
}

export type ScheduleValidationIssue = {
  code: string
  message: string
  role_id?: number
  assignment_id?: number
}

export type ScheduleRequirementValidation = {
  role: Pick<DepartmentRole, 'id' | 'name' | 'code'>
  minimum_quantity: number
  recommended_quantity: number
  assigned_quantity: number
  minimum_met: boolean
  recommended_met: boolean
}

export type ScheduleValidationResult = {
  valid: boolean
  can_publish: boolean
  blocking_issues: ScheduleValidationIssue[]
  warnings: ScheduleValidationIssue[]
  requirements: ScheduleRequirementValidation[]
}
