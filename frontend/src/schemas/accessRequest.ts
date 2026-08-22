import { z } from 'zod'

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

export const accessRequestSchema = z.object({
  full_name: z
    .string()
    .trim()
    .min(1, 'Informe o nome completo.'),
  birth_date: z
    .string()
    .min(1, 'Informe a data de nascimento.')
    .refine(isValidDate, 'Informe uma data valida.')
    .refine((value) => !isFutureDate(value), 'A data de nascimento nao pode ser futura.'),
  email: z
    .string()
    .trim()
    .min(1, 'Informe o e-mail.')
    .refine((value) => z.email().safeParse(value).success, 'E-mail invalido.'),
  phone: z
    .string()
    .trim()
    .min(1, 'Informe o telefone.'),
  username: z
    .string()
    .trim()
    .min(1, 'Informe o usuario.')
    .regex(/^[\w.@+-]+$/, 'Use apenas letras, numeros e @/./+/-/_.'),
  password: z
    .string()
    .min(1, 'Informe a senha.'),
  password_confirm: z
    .string()
    .min(1, 'Confirme a senha.'),
}).refine((value) => value.password === value.password_confirm, {
  message: 'As senhas nao conferem.',
  path: ['password_confirm'],
})

export type AccessRequestFormValues = z.input<typeof accessRequestSchema>
export type AccessRequestFormData = z.output<typeof accessRequestSchema>

export const accessRequestDefaultValues: AccessRequestFormValues = {
  full_name: '',
  birth_date: '',
  email: '',
  phone: '',
  username: '',
  password: '',
  password_confirm: '',
}
