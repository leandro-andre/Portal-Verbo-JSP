import { z } from 'zod'

function isValidDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  if (!year || !month || !day) {
    return false
  }

  const date = new Date(year, month - 1, day)
  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day
}

export const discipleshipLessonSchema = z.object({
  title: z.string().trim().min(1, 'Informe o titulo da aula.'),
  lesson_date: z.string().min(1, 'Informe a data da aula.').refine(isValidDate, 'Informe uma data valida.'),
})

export type DiscipleshipLessonFormValues = z.input<typeof discipleshipLessonSchema>
export type DiscipleshipLessonFormData = z.output<typeof discipleshipLessonSchema>

export const discipleshipLessonDefaultValues: DiscipleshipLessonFormValues = {
  title: '',
  lesson_date: '',
}
