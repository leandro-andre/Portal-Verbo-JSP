import type { Department, DepartmentMembership } from './department'
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
