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
  | 'CHURCH_JOURNEY_VIEW'
  | 'CHURCH_JOURNEY_CREATE'
  | 'CHURCH_JOURNEY_CHANGE'
  | 'MEMBERSHIP_VIEW'
  | 'MEMBERSHIP_APPROVE'
  | 'MEMBERSHIP_DEACTIVATE'
  | 'MEMBERSHIP_REACTIVATE'
  | 'DEPARTMENT_VIEW'
  | 'DEPARTMENT_CREATE'
  | 'DEPARTMENT_CHANGE'
  | 'DEPARTMENT_DEACTIVATE'
  | 'DEPARTMENT_REACTIVATE'
  | 'DISCIPLESHIP_CLASS_VIEW'
  | 'DISCIPLESHIP_CLASS_CREATE'
  | 'DISCIPLESHIP_CLASS_CHANGE'
  | 'DISCIPLESHIP_CLASS_START'
  | 'DISCIPLESHIP_CLASS_COMPLETE'
  | 'DISCIPLESHIP_CLASS_CANCEL'
  | 'DISCIPLESHIP_ENROLLMENT_VIEW'
  | 'DISCIPLESHIP_ENROLLMENT_CREATE'
  | 'DISCIPLESHIP_ENROLLMENT_WITHDRAW'
  | 'DISCIPLESHIP_LESSON_VIEW'
  | 'DISCIPLESHIP_LESSON_CREATE'
  | 'DISCIPLESHIP_LESSON_CHANGE'
  | 'DISCIPLESHIP_LESSON_CANCEL'
  | 'DISCIPLESHIP_ATTENDANCE_VIEW'
  | 'DISCIPLESHIP_ATTENDANCE_MANAGE'
  | 'DISCIPLESHIP_COMPLETION_VIEW'
  | 'DISCIPLESHIP_COMPLETION_MANAGE'

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
