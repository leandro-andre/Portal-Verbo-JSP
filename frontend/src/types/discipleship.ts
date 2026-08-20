export type DiscipleshipClassStatus = 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'

export type DiscipleshipClassTeacher = {
  id: number
  display_name: string
}

export type DiscipleshipClass = {
  id: number
  name: string
  teacher: DiscipleshipClassTeacher
  start_date: string
  expected_end_date: string
  planned_sessions: number
  status: DiscipleshipClassStatus
  created_at: string
  updated_at: string
}

export type CreateDiscipleshipClassInput = {
  name: string
  teacher_id: number
  start_date: string
  expected_end_date: string
  planned_sessions: number
}

export type UpdateDiscipleshipClassInput = Partial<CreateDiscipleshipClassInput>

export type DiscipleshipValidationErrors = Partial<Record<keyof CreateDiscipleshipClassInput, string[]>>
