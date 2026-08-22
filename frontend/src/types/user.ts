export type AccessStatus = 'PENDING_APPROVAL' | 'PENDING_ACTIVATION' | 'ACTIVE' | 'BLOCKED'

export type PortalUserPerson = {
  id: number
  display_name: string
  full_name: string
  email: string
  status: 'ACTIVE' | 'INACTIVE'
}

export type PortalUser = {
  id: number
  username: string
  is_active: boolean
  access_status: AccessStatus
  last_login: string | null
  date_joined: string
  person: PortalUserPerson | null
  is_superuser: boolean
}

export type UserAccessBusinessErrorResponse = {
  code:
    | 'CANNOT_DISABLE_OWN_ACCOUNT'
    | 'CANNOT_DISABLE_SUPERUSER'
    | 'USER_ACCESS_NOT_ACTIVE'
    | 'USER_ACCESS_NOT_BLOCKED'
    | 'PERSON_NOT_FOUND'
    | 'PERSON_ALREADY_HAS_USER'
  message: string
}

export type LinkUserPersonInput = {
  person_id: number
}
