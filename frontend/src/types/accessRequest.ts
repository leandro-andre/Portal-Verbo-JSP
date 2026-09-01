export type CreateAccessRequestInput = {
  full_name: string
  birth_date: string
  email: string
  phone: string
  username: string
  password: string
  password_confirm: string
}

export type AccessRequestStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export type AccessRequestPerson = {
  id: number
  display_name: string
  full_name: string
  birth_date: string
  email: string
  phone: string
  status: string
}

export type AccessRequestUser = {
  id: number
  username: string
  display_name: string
}

export type AccessRequestPendingUser = {
  id: number
  username: string
  is_active: boolean
  access_status: 'PENDING_APPROVAL' | 'PENDING_ACTIVATION' | 'ACTIVE' | 'BLOCKED'
}

export type AccessRequestResponse = {
  id: number
  full_name: string
  birth_date: string
  email: string
  phone: string
  status: AccessRequestStatus
  created_at: string
  updated_at?: string
  reviewed_at?: string | null
  rejection_reason?: string
  person?: AccessRequestPerson | null
  usuario?: AccessRequestPendingUser | null
  reviewed_by?: AccessRequestUser | null
  candidates?: AccessRequestPerson[]
}

export type AccessRequest = Required<
  Pick<
    AccessRequestResponse,
    | 'id'
    | 'full_name'
    | 'birth_date'
    | 'email'
    | 'phone'
    | 'status'
    | 'created_at'
  >
> & {
  updated_at: string
  reviewed_at: string | null
  rejection_reason: string
  person: AccessRequestPerson | null
  usuario: AccessRequestPendingUser | null
  reviewed_by: AccessRequestUser | null
  candidates: AccessRequestPerson[]
}

export type ApproveAccessRequestInput =
  | { person_id: number; create_new_person?: false }
  | { create_new_person: true; person_id?: never }

export type ApproveAccessRequestResponse = AccessRequest & {
  created_user: {
    id: number
    username: string
    is_active: boolean
    activation_url?: string
  }
  notification?: {
    email_sent: boolean
    reason?: 'provider_disabled' | 'delivery_failed' | 'missing_recipient' | 'missing_app_base_url'
    type?: 'activation' | 'approval-active-account'
  }
}

export type RejectAccessRequestInput = {
  rejection_reason?: string
}

export type AccessRequestBusinessErrorResponse = {
  code:
    | 'PERSON_ALREADY_HAS_USER'
    | 'ACCESS_REQUEST_NOT_PENDING'
    | 'PERSON_NOT_FOUND'
    | 'INVALID_WHATSAPP'
    | 'ACCESS_REQUEST_APPROVAL_INTEGRITY_ERROR'
    | 'USERNAME_ALREADY_EXISTS'
  message: string
}

export type PendingAccessRequestExistsResponse = {
  code: 'PENDING_ACCESS_REQUEST_EXISTS' | 'USERNAME_ALREADY_EXISTS'
  message: string
}

export type AccessRequestValidationErrors = Partial<
  Record<keyof CreateAccessRequestInput, string[]>
>
