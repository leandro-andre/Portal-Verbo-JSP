import { useState, type FormEvent } from 'react'
import { CheckCircle2, KeyRound } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { AuthValidationError } from '../api/auth'
import { useConfirmPasswordReset, useValidatePasswordResetToken } from '../hooks/useAuth'

function ResetPasswordPage() {
  const { uid = '', token = '' } = useParams()
  const tokenValidation = useValidatePasswordResetToken(uid, token)
  const confirmPasswordReset = useConfirmPasswordReset()
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
      await confirmPasswordReset.mutateAsync({
        uid,
        token,
        new_password: password,
        new_password_confirm: passwordConfirm,
      })
      setIsSuccess(true)
    } catch (error) {
      if (error instanceof AuthValidationError) {
        setPasswordError(
          error.fieldErrors.new_password?.[0] || error.fieldErrors.new_password_confirm?.[0] || null,
        )
        setTokenError(error.fieldErrors.token?.[0] || error.fieldErrors.uid?.[0] || null)
        return
      }

      setGeneralError('Nao foi possivel redefinir sua senha. Tente novamente.')
    }
  }

  const isInvalidLink = tokenValidation.isError || tokenValidation.data?.valid === false

  return (
    <main className="public-access-page">
      <section className="access-request-shell auth-shell" aria-labelledby="reset-password-title">
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
            <h1>Senha redefinida</h1>
            <p>Agora voce ja pode entrar no Portal com a nova senha.</p>
            <Link className="button button--primary" to="/login">
              Ir para login
            </Link>
          </div>
        ) : (
          <>
            <div className="access-request-heading">
              <h1 id="reset-password-title">Redefinir senha</h1>
              <p>Defina uma nova senha para acessar o Portal.</p>
            </div>

            {tokenValidation.isLoading ? (
              <div className="state-panel">
                <h2>Validando link...</h2>
                <p>Aguarde enquanto verificamos sua solicitacao.</p>
              </div>
            ) : isInvalidLink ? (
              <div className="access-request-success" role="status">
                <KeyRound size={36} aria-hidden="true" />
                <h1>Link invalido</h1>
                <p>Solicite uma nova redefinicao de senha para continuar.</p>
                <Link className="button button--primary" to="/esqueci-minha-senha">
                  Solicitar novo link
                </Link>
              </div>
            ) : (
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
                  <label htmlFor="reset_password">Nova senha *</label>
                  <input
                    id="reset_password"
                    type="password"
                    autoComplete="new-password"
                    aria-invalid={Boolean(passwordError)}
                    aria-describedby={passwordError ? 'reset_password-error' : undefined}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                  {passwordError ? (
                    <span className="field-error" id="reset_password-error">
                      {passwordError}
                    </span>
                  ) : null}
                </div>

                <div className="field-group">
                  <label htmlFor="reset_password_confirm">Confirmar senha *</label>
                  <input
                    id="reset_password_confirm"
                    type="password"
                    autoComplete="new-password"
                    value={passwordConfirm}
                    onChange={(event) => setPasswordConfirm(event.target.value)}
                    required
                  />
                </div>

                <button className="button button--primary" type="submit" disabled={confirmPasswordReset.isPending}>
                  <CheckCircle2 size={17} aria-hidden="true" />
                  {confirmPasswordReset.isPending ? 'Redefinindo...' : 'Redefinir senha'}
                </button>
              </form>
            )}
          </>
        )}
      </section>
    </main>
  )
}

export default ResetPasswordPage
