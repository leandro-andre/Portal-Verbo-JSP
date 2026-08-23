import { z } from 'zod'

export const departmentCreateSchema = z.object({
  nome: z.string().trim().min(1, 'Informe o nome do departamento.'),
  codigo: z.string().trim().min(1, 'Informe o codigo do departamento.'),
  descricao: z.string().trim(),
})

export const departmentUpdateSchema = z.object({
  nome: z.string().trim().min(1, 'Informe o nome do departamento.'),
  descricao: z.string().trim(),
})

export type DepartmentCreateFormValues = z.input<typeof departmentCreateSchema>
export type DepartmentCreateFormData = z.output<typeof departmentCreateSchema>
export type DepartmentUpdateFormValues = z.input<typeof departmentUpdateSchema>
export type DepartmentUpdateFormData = z.output<typeof departmentUpdateSchema>

export const departmentCreateDefaultValues: DepartmentCreateFormValues = {
  nome: '',
  codigo: '',
  descricao: '',
}
