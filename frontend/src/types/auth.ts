export type CurrentUser = {
  id: number
  username: string
  display_name: string
  email: string
  is_active: boolean
  is_staff: boolean
  is_superuser: boolean
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
