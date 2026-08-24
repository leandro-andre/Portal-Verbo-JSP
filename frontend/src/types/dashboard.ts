import type { ChurchJourneyStatus } from './person'
import type { MyScheduleWarning } from './scheduling'

export type DashboardDepartment = {
  id: number
  status: string
  joined_at: string
  department: {
    id: number
    name: string
    code: string
  }
  role: {
    id: number
    name: string
    code: string
    can_manage_schedules: boolean
  }
}

export type DashboardResponse = {
  person_linked: boolean
  message: string
  account: {
    id: number
    username: string
    display_name: string
  }
  profile: {
    id: number
    name: string
    full_name: string
    photo_url: string | null
    church_status: ChurchJourneyStatus
    member_since: string | null
  } | null
  next_schedule: {
    assignment_id: number
    schedule_id: number
    date: string
    time: string
    worship_service: {
      id: number
      name: string
      kind: string
    }
    department: {
      id: number
      name: string
    }
    role: {
      id: number
      name: string
    }
    warnings: MyScheduleWarning[]
  } | null
  schedules_summary: {
    upcoming_count: number
    month_count: number
  }
  unavailability: {
    future_count: number
    next: {
      id: number
      start_date: string
      end_date: string
      start_time: string | null
      end_time: string | null
      is_full_day: boolean
    } | null
  }
  journey: {
    church_status: ChurchJourneyStatus
    discipleship_completed: boolean
    discipleship_completed_at: string | null
    departments: DashboardDepartment[]
  }
  contextual_access: {
    can_manage_schedules: boolean
    schedule_departments: Array<{
      id: number
      name: string
      role: string
    }>
  }
}
