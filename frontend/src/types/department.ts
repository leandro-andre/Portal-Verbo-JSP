export type Department = {
  id: number
  nome: string
  codigo: string
  descricao: string
  ativo: boolean
  criado_em: string
}

export type CreateDepartmentInput = {
  nome: string
  codigo: string
  descricao: string
}

export type UpdateDepartmentInput = {
  nome: string
  descricao: string
}

export type DepartmentValidationErrors = Partial<
  Record<keyof CreateDepartmentInput, string[]>
>
