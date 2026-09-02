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
  photo_url: string | null
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

export type PersonUnavailabilityStatus = 'ACTIVE' | 'INACTIVE'

export type PersonUnavailability = {
  id: number
  person: number
  start_date: string
  end_date: string
  start_time: string | null
  end_time: string | null
  reason: string
  status: PersonUnavailabilityStatus
  created_at: string
  updated_at: string
}

export type PersonUnavailabilityInput = {
  start_date: string
  end_date: string
  start_time?: string | null
  end_time?: string | null
  reason?: string
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

export type MyProfileResponse = {
  person_linked: boolean
  message: string
  account: {
    id: number
    username: string
    display_name: string
    email: string
    is_active: boolean
  }
  person: {
    id: number
    full_name: string
    preferred_name: string
    display_name: string
    birth_date: string
    email: string
    phone: string
    status: PersonStatus
    photo_url: string | null
  } | null
  church: {
    person_status: PersonStatus
    has_church_journey: boolean
    membership_status: MembershipStatus | null
    member_since: string | null
    discipleship_completed: boolean
    discipleship_completed_at: string | null
  } | null
  departments: Array<{
    id: number
    status: string
    joined_at: string
    department: {
      id: number
      name: string
      code: string
    }
    role: {
      id: number
      name: string
      code: string
    }
  }>
}

export type MyProfileUpdateInput = {
  phone: string
}

export type Person360PendingSeverity = 'info' | 'warning' | 'danger'

export type Person360PendingItem = {
  code: string
  severity: Person360PendingSeverity
  label: string
}

export type Person360DepartmentMembership = {
  id: number
  status: 'ACTIVE' | 'INACTIVE'
  joined_at: string | null
  left_at: string | null
  department: {
    id: number
    name: string
    code: string
    active: boolean
  }
  role: {
    id: number
    name: string
    code: string
    active: boolean
    can_manage_department: boolean
    can_manage_members: boolean
    can_manage_schedules: boolean
  }
  operationally_eligible: boolean
  eligibility: {
    eligible: boolean
    reasons: Array<{
      code: string
      message: string
    }>
  }
}

export type Person360 = {
  person: {
    id: number
    full_name: string
    preferred_name: string
    display_name: string
    birth_date: string | null
    age: number | null
    email: string
    phone: string
    photo_url: string | null
    status: PersonStatus
    created_at: string | null
    updated_at: string | null
  }
  church: {
    status: ChurchJourneyStatus
    label: string
    has_church_journey: boolean
    started_at: string | null
  }
  discipleship: {
    status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'WITHDRAWN'
    label: string
    enrolled_at: string | null
    completed_at: string | null
    withdrawn_at: string | null
    class: {
      id: number
      name: string
      status: string
      start_date: string | null
      expected_end_date: string | null
    } | null
    membership_eligible: boolean
    membership_can_create: boolean
  }
  membership: {
    has_membership: boolean
    status: MembershipStatus | null
    label: string
    member_since: string | null
    approved_at: string | null
    approved_by: {
      id: number
      display_name: string
    } | null
    created_at: string | null
    updated_at: string | null
  }
  access: {
    has_user: boolean
    id: number | null
    username: string | null
    email: string | null
    status: AccessStatus | 'NO_ACCESS'
    label: string
    is_active: boolean
    last_login: string | null
    date_joined: string | null
  }
  departments: {
    active: Person360DepartmentMembership[]
    inactive: Person360DepartmentMembership[]
  }
  pending_items: Person360PendingItem[]
  summary: {
    church_label: string
    discipleship_label: string
    membership_label: string
    access_label: string
    active_departments_count: number
  }
  actions: {
    edit_person_url: string
    manage_access_url: string | null
  }
}
