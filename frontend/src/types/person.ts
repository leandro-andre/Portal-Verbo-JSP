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
    membership_can_create: boolean
  }
  created_at: string
  updated_at: string
}

export type ChurchJourneyStatus = 'UNKNOWN' | 'VISITOR' | 'MEMBER' | 'INACTIVE_MEMBER'

export type MembershipStatus = 'ACTIVE' | 'INACTIVE'

export type Membership = {
  id: number
  person_id: number
  status: MembershipStatus
  member_since: string
  approved_by: {
    id: number
    display_name: string
  } | null
  approved_at: string | null
  created_at: string
  updated_at: string
  person?: {
    id: number
    display_name: string
    full_name: string
  }
}

export type MembershipStatusHistory = {
  id: number
  from_status: MembershipStatus
  to_status: MembershipStatus
  changed_by: {
    id: number
    display_name: string
  } | null
  changed_at: string
  reason: string
}

export type EligibleMembershipPerson = {
  id: number
  display_name: string
  full_name: string
  completed_at: string
}

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
