import { z } from 'zod'

function isValidDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  if (!year || !month || !day) {
    return false
  }

  const date = new Date(year, month - 1, day)
  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day
}

export const discipleshipClassSchema = z
  .object({
    name: z.string().trim().min(1, 'Informe o nome da turma.'),
    teacher_id: z.coerce.number().int('Selecione um professor.').positive('Selecione um professor.'),
    start_date: z.string().min(1, 'Informe a data de inicio.').refine(isValidDate, 'Informe uma data valida.'),
    expected_end_date: z
      .string()
      .min(1, 'Informe o termino previsto.')
      .refine(isValidDate, 'Informe uma data valida.'),
    planned_sessions: z.coerce.number().int('Informe um numero inteiro.').positive('Informe uma quantidade positiva.'),
  })
  .refine((values) => values.expected_end_date >= values.start_date, {
    message: 'O termino previsto nao pode ser anterior ao inicio.',
    path: ['expected_end_date'],
  })

export type DiscipleshipClassFormValues = z.input<typeof discipleshipClassSchema>
export type DiscipleshipClassFormData = z.output<typeof discipleshipClassSchema>

export const discipleshipClassDefaultValues: DiscipleshipClassFormValues = {
  name: '',
  teacher_id: 0,
  start_date: '',
  expected_end_date: '',
  planned_sessions: 12,
}
