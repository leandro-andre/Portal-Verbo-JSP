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

export type DiscipleshipEnrollmentStatus = 'ENROLLED' | 'WITHDRAWN' | 'COMPLETED'

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
  completed_at: string | null
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

export type DiscipleshipAttendanceStatus = 'PRESENT' | 'ABSENT' | 'JUSTIFIED'

export type DiscipleshipAttendance = {
  id: number
  status: DiscipleshipAttendanceStatus
  recorded_by: {
    id: number
    display_name: string
  } | null
  created_at: string
  updated_at: string
}

export type DiscipleshipAttendanceStudent = {
  enrollment_id: number
  person: {
    id: number
    display_name: string
  }
  attendance: DiscipleshipAttendance | null
}

export type DiscipleshipAttendanceSummary = {
  eligible: number
  recorded: number
  not_recorded: number
  present: number
  absent: number
  justified: number
}

export type DiscipleshipAttendancePayload = {
  lesson: {
    id: number
    title: string
    lesson_date: string
    status: DiscipleshipLessonStatus
  }
  summary: DiscipleshipAttendanceSummary
  permissions: {
    can_view_attendance: boolean
    can_manage_attendance: boolean
  }
  students: DiscipleshipAttendanceStudent[]
}

export type SaveDiscipleshipAttendanceInput = {
  records: Array<{
    enrollment_id: number
    status: DiscipleshipAttendanceStatus
  }>
}

export type DiscipleshipCompletionReason =
  | 'CLASS_NOT_COMPLETED'
  | 'ENROLLMENT_WITHDRAWN'
  | 'ATTENDANCE_INCOMPLETE'
  | 'NO_FREQUENCY_DENOMINATOR'
  | 'MINIMUM_ATTENDANCE_NOT_REACHED'
  | 'ALREADY_COMPLETED'

export type DiscipleshipCompletionSummary = {
  enrollment_id: number
  status: DiscipleshipEnrollmentStatus
  completed_at: string | null
  frequency: {
    eligible_lessons: number
    present: number
    absent: number
    justified: number
    not_recorded: number
    denominator: number
    percentage: number | null
    attendance_complete: boolean
  }
  completion: {
    can_complete: boolean
    minimum_percentage: number
    reason: DiscipleshipCompletionReason | null
  }
  membership_eligibility: boolean
}
