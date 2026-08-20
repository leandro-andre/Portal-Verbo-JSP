import type {
  DiscipleshipClassStatus,
  DiscipleshipEnrollmentStatus,
  DiscipleshipLessonStatus,
} from '../types/discipleship'

export function discipleshipStatusLabel(status: DiscipleshipClassStatus) {
  if (status === 'PLANNED') return 'Planejada'
  if (status === 'IN_PROGRESS') return 'Em andamento'
  if (status === 'COMPLETED') return 'Concluida'
  return 'Cancelada'
}

export function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  return year && month && day ? `${day}/${month}/${year}` : value
}

export function enrollmentStatusLabel(status: DiscipleshipEnrollmentStatus) {
  if (status === 'ENROLLED') return 'Matriculado'
  return 'Desistente'
}

export function lessonStatusLabel(status: DiscipleshipLessonStatus) {
  if (status === 'SCHEDULED') return 'Agendada'
  return 'Cancelada'
}
