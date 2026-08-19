import { useState, type FormEvent } from 'react'
import { CheckCircle2 } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { AuthValidationError } from '../api/auth'
import { useActivateAccount } from '../hooks/useAuth'

function ActivateAccountPage() {
  const { uid = '', token = '' } = useParams()
  const activateAccount = useActivateAccount()
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [tokenError, setTokenError] = useState<string | null>(null)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [isSuccess, setIsSuccess] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setPasswordError(null)
    setTokenError(null)
    setGeneralError(null)

    if (!password) {
      setPasswordError('Informe a nova senha.')
      return
    }

    if (password !== passwordConfirm) {
      setPasswordError('As senhas nao conferem.')
      return
    }

    try {
      await activateAccount.mutateAsync({
        uid,
        token,
        password,
        password_confirm: passwordConfirm,
      })
      setIsSuccess(true)
    } catch (error) {
      if (error instanceof AuthValidationError) {
        setPasswordError(error.fieldErrors.password?.[0] || error.fieldErrors.password_confirm?.[0] || null)
        setTokenError(error.fieldErrors.token?.[0] || error.fieldErrors.uid?.[0] || null)
        return
      }

      setGeneralError('Nao foi possivel ativar sua conta. Tente novamente.')
    }
  }

  return (
    <main className="public-access-page">
      <section className="access-request-shell auth-shell" aria-labelledby="activate-account-title">
        <div className="access-request-brand">
          <div className="access-request-brand__mark" aria-hidden="true">
            VV
          </div>
          <div>
            <strong>Verbo da Vida</strong>
            <span>Jardim Sao Paulo</span>
          </div>
        </div>

        {isSuccess ? (
          <div className="access-request-success" role="status">
            <CheckCircle2 size={36} aria-hidden="true" />
            <h1>Conta ativada</h1>
            <p>Sua senha foi definida. Agora voce ja pode entrar no Portal.</p>
            <Link className="button button--primary" to="/login">
              Ir para login
            </Link>
          </div>
        ) : (
          <>
            <div className="access-request-heading">
              <h1 id="activate-account-title">Ativar minha conta</h1>
              <p>Defina uma senha para acessar o Portal.</p>
            </div>

            <form className="access-request-form" onSubmit={(event) => void handleSubmit(event)}>
              {tokenError ? (
                <div className="form-alert form-alert--error" role="alert">
                  {tokenError}
                </div>
              ) : null}

              {generalError ? (
                <div className="form-alert form-alert--error" role="alert">
                  {generalError}
                </div>
              ) : null}

              <div className="field-group">
                <label htmlFor="activate_password">Nova senha *</label>
                <input
                  id="activate_password"
                  type="password"
                  autoComplete="new-password"
                  aria-invalid={Boolean(passwordError)}
                  aria-describedby={passwordError ? 'activate_password-error' : undefined}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
                {passwordError ? (
                  <span className="field-error" id="activate_password-error">
                    {passwordError}
                  </span>
                ) : null}
              </div>

              <div className="field-group">
                <label htmlFor="activate_password_confirm">Confirmar senha *</label>
                <input
                  id="activate_password_confirm"
                  type="password"
                  autoComplete="new-password"
                  value={passwordConfirm}
                  onChange={(event) => setPasswordConfirm(event.target.value)}
                  required
                />
              </div>

              <button className="button button--primary" type="submit" disabled={activateAccount.isPending}>
                <CheckCircle2 size={17} aria-hidden="true" />
                {activateAccount.isPending ? 'Ativando...' : 'Ativar conta'}
              </button>
            </form>
          </>
        )}
      </section>
    </main>
  )
}

export default ActivateAccountPage
