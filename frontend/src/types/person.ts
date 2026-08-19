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
