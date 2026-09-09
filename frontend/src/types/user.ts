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

export type UserAdminProfile = {
  id: number
  display_name: string
  access_status: {
    value: AccessStatus
    label: string
  }
  account: {
    id: number
    username: string
    email: string
    is_active: boolean
    is_superuser: boolean
    has_usable_password: boolean
    date_joined: string
    last_login: string | null
    person_linked: boolean
  }
  person: (PortalUserPerson & {
    photo_url: string | null
    status_label: string
    profile_url: string
  }) | null
  activation: {
    status: AccessStatus
    label: string
    message: string
  }
  security: {
    has_usable_password: boolean
    is_active: boolean
    status: AccessStatus
    status_label: string
    message: string
  }
  access_request: {
    id: number
    status: 'PENDING' | 'APPROVED' | 'REJECTED'
    status_label: string
    created_at: string
    updated_at: string
    reviewed_at: string | null
    detail_url: string
  } | null
  actions: {
    can_view_person_profile: boolean
    person_profile_url: string | null
    can_link_person: boolean
    link_person_url: string | null
    can_block: boolean
    block_url: string | null
    can_unblock: boolean
    unblock_url: string | null
    can_resend_activation: boolean
    resend_activation_url: string | null
    can_send_password_reset: boolean
    password_reset_url: string | null
  }
}

export type UserAdminOperationResponse = {
  status?: 'ok'
  access_status?: AccessStatus
  notification?: {
    email_sent: boolean
    type?: 'activation' | 'password_reset' | 'approval-active-account'
    reason?: 'provider_disabled' | 'delivery_failed' | 'missing_recipient' | 'missing_app_base_url'
  }
}

export type UserAccessBusinessErrorResponse = {
  code:
    | 'CANNOT_DISABLE_OWN_ACCOUNT'
    | 'CANNOT_DISABLE_SUPERUSER'
    | 'USER_ACCESS_NOT_ACTIVE'
    | 'USER_ACCESS_NOT_BLOCKED'
    | 'PERSON_NOT_FOUND'
    | 'PERSON_ALREADY_HAS_USER'
    | 'USER_ALREADY_LINKED_TO_PERSON'
    | 'USER_ACTIVATION_EMAIL_NOT_ALLOWED'
    | 'USER_PASSWORD_RESET_EMAIL_NOT_ALLOWED'
    | 'USER_EMAIL_MISSING'
    | 'USER_EMAIL_CONFIGURATION_ERROR'
    | 'USER_EMAIL_DELIVERY_ERROR'
  message: string
  notification?: UserAdminOperationResponse['notification']
}

export type LinkUserPersonInput = {
  person_id: number
}

export type UserPersonCandidate = {
  id: number
  display_name: string
  full_name: string
  photo_url: string | null
  email: string
  phone: string
  status: 'ACTIVE' | 'INACTIVE'
  status_label: string
  church_status: 'UNKNOWN' | 'VISITOR' | 'MEMBER' | 'INACTIVE_MEMBER'
  church_status_label: string
}
