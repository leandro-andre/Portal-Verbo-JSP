import type {
  ActivateAccountInput,
  AuthValidationErrors,
  CurrentUserResponse,
  LoginInput,
  PasswordResetConfirmInput,
  PasswordResetRequestInput,
  PasswordResetValidateResponse,
} from '../types/auth'
import { csrfJsonHeaders } from './http'

export class AuthValidationError extends Error {
  fieldErrors: AuthValidationErrors
  code?: string

  constructor(fieldErrors: AuthValidationErrors, code?: string) {
    super('Nao foi possivel validar os dados de autenticacao.')
    this.name = 'AuthValidationError'
    this.fieldErrors = fieldErrors
    this.code = code
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function parseAuthErrors(value: unknown): AuthValidationErrors {
  if (!isRecord(value)) {
    return {}
  }

  const errors: AuthValidationErrors = {}
  const fields: Array<keyof AuthValidationErrors> = [
    'username',
    'password',
    'password_confirm',
    'uid',
    'token',
    'new_password',
    'new_password_confirm',
  ]

  fields.forEach((field) => {
    const fieldValue = value[field]
    if (isStringArray(fieldValue)) {
      errors[field] = fieldValue
    } else if (typeof fieldValue === 'string') {
      errors[field] = [fieldValue]
    }
  })

  if (typeof value.message === 'string') {
    errors.username = [value.message]
  }

  return errors
}

async function parseJson(response: Response): Promise<unknown> {
  return response.json().catch(() => null)
}

export async function getCurrentUser(): Promise<CurrentUserResponse> {
  const response = await fetch('/api/auth/current-user/', {
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error('Nao foi possivel carregar a sessao atual.')
  }

  return response.json() as Promise<CurrentUserResponse>
}

export async function login(payload: LoginInput): Promise<CurrentUserResponse> {
  const headers = await csrfJsonHeaders({ refresh: true })
  const response = await fetch('/api/auth/login/', {
    method: 'POST',
    credentials: 'include',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseJson(response)

  if (response.status === 400) {
    throw new AuthValidationError(
      parseAuthErrors(data),
      isRecord(data) && typeof data.code === 'string' ? data.code : undefined,
    )
  }

  if (!response.ok) {
    throw new Error('Nao foi possivel entrar no Portal.')
  }

  return data as CurrentUserResponse
}

export async function logout(): Promise<void> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/auth/logout/', {
    method: 'POST',
    credentials: 'include',
    headers,
  })

  if (!response.ok) {
    throw new Error('Nao foi possivel sair do Portal.')
  }
}

export async function activateAccount(payload: ActivateAccountInput): Promise<void> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/auth/activate/', {
    method: 'POST',
    credentials: 'include',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseJson(response)

  if (response.status === 400) {
    throw new AuthValidationError(parseAuthErrors(data))
  }

  if (!response.ok) {
    throw new Error('Nao foi possivel ativar sua conta.')
  }
}

export async function requestPasswordReset(payload: PasswordResetRequestInput): Promise<void> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/auth/password-reset/request/', {
    method: 'POST',
    credentials: 'include',
    headers,
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error('Nao foi possivel solicitar a redefinicao de senha.')
  }
}

export async function validatePasswordResetToken(uid: string, token: string): Promise<PasswordResetValidateResponse> {
  const response = await fetch(`/api/auth/password-reset/validate/${uid}/${token}/`, {
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error('Nao foi possivel validar o link de redefinicao.')
  }

  return response.json() as Promise<PasswordResetValidateResponse>
}

export async function confirmPasswordReset(payload: PasswordResetConfirmInput): Promise<void> {
  const headers = await csrfJsonHeaders()
  const response = await fetch('/api/auth/password-reset/confirm/', {
    method: 'POST',
    credentials: 'include',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await parseJson(response)

  if (response.status === 400) {
    throw new AuthValidationError(parseAuthErrors(data))
  }

  if (!response.ok) {
    throw new Error('Nao foi possivel redefinir sua senha.')
  }
}
