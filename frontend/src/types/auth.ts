export type RoleCode = 'PORTAL_ADMIN' | 'SECRETARY' | 'PASTOR'

export type Capability =
  | 'PEOPLE_VIEW'
  | 'PEOPLE_CREATE'
  | 'PEOPLE_CHANGE'
  | 'ACCESS_REQUEST_VIEW'
  | 'ACCESS_REQUEST_APPROVE'
  | 'ACCESS_REQUEST_REJECT'
  | 'USER_VIEW'
  | 'USER_DISABLE'
  | 'USER_ENABLE'

export type CurrentUser = {
  id: number
  username: string
  display_name: string
  email: string
  is_active: boolean
  is_staff: boolean
  is_superuser: boolean
  person_id: number | null
  roles: RoleCode[]
  capabilities: Capability[]
}

export type CurrentUserResponse = {
  is_authenticated: boolean
  user: CurrentUser | null
}

export type LoginInput = {
  username: string
  password: string
}

export type ActivateAccountInput = {
  uid: string
  token: string
  password: string
  password_confirm: string
}

export type AuthValidationErrors = Partial<
  Record<'username' | 'password' | 'password_confirm' | 'uid' | 'token', string[]>
>
