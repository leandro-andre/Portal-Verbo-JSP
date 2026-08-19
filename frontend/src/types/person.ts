export type PersonStatus = 'ACTIVE' | 'INACTIVE'

export type Person = {
  id: number
  full_name: string
  preferred_name: string
  display_name: string
  birth_date: string
  email: string
  phone: string
  status: PersonStatus
  created_at: string
  updated_at: string
}

export type CreatePersonInput = {
  full_name: string
  preferred_name?: string
  birth_date: string
  email?: string
  phone?: string
  allow_possible_duplicate?: boolean
}

export type UpdatePersonInput = Partial<Omit<CreatePersonInput, 'allow_possible_duplicate'>> & {
  status?: PersonStatus
  allow_possible_duplicate?: boolean
}

export type PossibleDuplicateCandidate = Pick<
  Person,
  'id' | 'display_name' | 'full_name' | 'birth_date'
>

export type PossibleDuplicateResponse = {
  code: 'POSSIBLE_DUPLICATE'
  message: string
  candidates: PossibleDuplicateCandidate[]
}

export type ApiValidationErrors = Partial<Record<keyof CreatePersonInput, string[]>>
