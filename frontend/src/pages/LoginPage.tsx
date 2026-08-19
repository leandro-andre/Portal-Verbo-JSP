import { useState, type FormEvent } from 'react'
import { LogIn } from 'lucide-react'
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { AuthValidationError } from '../api/auth'
import { useCurrentUser, useLogin } from '../hooks/useAuth'

function LoginPage() {
  const login = useLogin()
  const { data: currentUser, isLoading } = useCurrentUser()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [fieldError, setFieldError] = useState<string | null>(null)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const nextPath = searchParams.get('next') || '/pessoas'

  if (!isLoading && currentUser?.is_authenticated) {
    return <Navigate to={nextPath} replace />
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFieldError(null)
    setGeneralError(null)

    try {
      await login.mutateAsync({ username, password })
      navigate(nextPath, { replace: true, state: { from: location } })
    } catch (error) {
      if (error instanceof AuthValidationError) {
        setFieldError(
          error.fieldErrors.username?.[0] ||
            error.fieldErrors.password?.[0] ||
            'Usuario/e-mail ou senha invalidos.',
        )
        return
      }

      setGeneralError('Nao foi possivel entrar no Portal. Tente novamente.')
    }
  }

  return (
    <main className="public-access-page">
      <section className="access-request-shell auth-shell" aria-labelledby="login-title">
        <div className="access-request-brand">
          <div className="access-request-brand__mark" aria-hidden="true">
            VV
          </div>
          <div>
            <strong>Verbo da Vida</strong>
            <span>Jardim Sao Paulo</span>
          </div>
        </div>

        <div className="access-request-heading">
          <h1 id="login-title">Entrar no Portal</h1>
          <p>Use seu usuario ou e-mail e a senha definida na ativacao da conta.</p>
        </div>

        <form className="access-request-form" onSubmit={(event) => void handleSubmit(event)}>
          {fieldError ? (
            <div className="form-alert form-alert--error" role="alert">
              {fieldError}
            </div>
          ) : null}

          {generalError ? (
            <div className="form-alert form-alert--error" role="alert">
              {generalError}
            </div>
          ) : null}

          <div className="field-group">
            <label htmlFor="login_username">Usuario ou e-mail *</label>
            <input
              id="login_username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </div>

          <div className="field-group">
            <label htmlFor="login_password">Senha *</label>
            <input
              id="login_password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          <button className="button button--primary" type="submit" disabled={login.isPending}>
            <LogIn size={17} aria-hidden="true" />
            {login.isPending ? 'Entrando...' : 'Entrar'}
          </button>

          <Link className="public-link" to="/pedir-acesso">
            Ainda nao tenho acesso
          </Link>
        </form>
      </section>
    </main>
  )
}

export default LoginPage
