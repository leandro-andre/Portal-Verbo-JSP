import type { AccessStatus } from './user'

export type PersonStatus = 'ACTIVE' | 'INACTIVE'

export type PersonPortalUser = {
  id: number
  username: string
  access_status: AccessStatus
}

export type Person = {
  id: number
  full_name: string
  preferred_name: string
  display_name: string
  birth_date: string
  email: string
  phone: string
  status: PersonStatus
  portal_user: PersonPortalUser | null
  has_church_journey: boolean
  discipleship: {
    completed: boolean
    completed_at: string | null
    completed_class: {
      id: number
      name: string
    } | null
    membership_eligible: boolean
  }
  created_at: string
  updated_at: string
}

export type ChurchJourneyStatus = 'VISITOR' | 'MEMBER' | 'UNKNOWN'

export type ChurchJourney = {
  id: number
  person_id: number
  started_at: string
  church_status: ChurchJourneyStatus
  created_at: string
  updated_at: string
}

export type StartChurchJourneyInput = {
  started_at?: string
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
