import { z } from 'zod'
import { isValidBrazilianMobile, normalizeBrazilianMobile } from '../utils/phone'

function isValidDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  if (!year || !month || !day) {
    return false
  }

  const date = new Date(year, month - 1, day)
  return (
    date.getFullYear() === year &&
    date.getMonth() === month - 1 &&
    date.getDate() === day
  )
}

function isFutureDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  return date > today
}

export const personCreateSchema = z.object({
  full_name: z
    .string()
    .trim()
    .min(1, 'Informe o nome completo.'),
  preferred_name: z.string().trim().optional().default(''),
  birth_date: z
    .string()
    .min(1, 'Informe a data de nascimento.')
    .refine(isValidDate, 'Informe uma data valida.')
    .refine((value) => !isFutureDate(value), 'A data de nascimento nao pode ser futura.'),
  email: z
    .string()
    .trim()
    .optional()
    .default('')
    .refine((value) => !value || z.email().safeParse(value).success, 'E-mail invalido.'),
  phone: z
    .string()
    .trim()
    .optional()
    .default('')
    .refine((value) => !value || isValidBrazilianMobile(value), 'Informe um celular brasileiro valido.')
    .transform((value) => normalizeBrazilianMobile(value)),
})

export type PersonCreateFormValues = z.input<typeof personCreateSchema>
export type PersonCreateFormData = z.output<typeof personCreateSchema>

export const personCreateDefaultValues: PersonCreateFormValues = {
  full_name: '',
  preferred_name: '',
  birth_date: '',
  email: '',
  phone: '',
}
