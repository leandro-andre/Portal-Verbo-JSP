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

export type DiscipleshipEnrollmentStatus = 'ENROLLED' | 'WITHDRAWN'

export type DiscipleshipEnrollmentPerson = {
  id: number
  display_name: string
  full_name: string
}

export type DiscipleshipEnrollmentClass = {
  id: number
  name: string
}

export type DiscipleshipEnrollment = {
  id: number
  person: DiscipleshipEnrollmentPerson
  discipleship_class: DiscipleshipEnrollmentClass
  status: DiscipleshipEnrollmentStatus
  enrolled_at: string
  withdrawn_at: string | null
  created_at: string
  updated_at: string
}

export type CreateDiscipleshipEnrollmentInput = {
  person_id: number
}

export type DiscipleshipLessonStatus = 'SCHEDULED' | 'CANCELLED'

export type DiscipleshipLesson = {
  id: number
  discipleship_class_id: number
  title: string
  lesson_date: string
  status: DiscipleshipLessonStatus
  created_at: string
  updated_at: string
}

export type CreateDiscipleshipLessonInput = {
  title: string
  lesson_date: string
}

export type UpdateDiscipleshipLessonInput = Partial<CreateDiscipleshipLessonInput>

export type DiscipleshipLessonValidationErrors = Partial<
  Record<keyof CreateDiscipleshipLessonInput, string[]>
>
