import { useState, type FormEvent } from 'react'
import { Mail } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useRequestPasswordReset } from '../hooks/useAuth'

const neutralMessage =
  'Se o e-mail informado estiver vinculado a uma conta ativa, enviaremos as instrucoes de redefinicao.'

function ForgotPasswordPage() {
  const requestPasswordReset = useRequestPasswordReset()
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState<string | null>(null)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setMessage(null)

    try {
      await requestPasswordReset.mutateAsync({ email })
    } finally {
      setMessage(neutralMessage)
    }
  }

  return (
    <main className="public-access-page">
      <section className="access-request-shell auth-shell" aria-labelledby="forgot-password-title">
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
          <h1 id="forgot-password-title">Recuperar senha</h1>
          <p>Informe o e-mail usado no Portal.</p>
        </div>

        <form className="access-request-form" onSubmit={(event) => void handleSubmit(event)}>
          {message ? (
            <div className="form-alert form-alert--success" role="status">
              {message}
            </div>
          ) : null}

          <div className="field-group">
            <label htmlFor="password_reset_email">E-mail *</label>
            <input
              id="password_reset_email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>

          <button className="button button--primary" type="submit" disabled={requestPasswordReset.isPending}>
            <Mail size={17} aria-hidden="true" />
            {requestPasswordReset.isPending ? 'Enviando...' : 'Enviar instrucoes'}
          </button>

          <Link className="public-link" to="/login">
            Voltar para login
          </Link>
        </form>
      </section>
    </main>
  )
}

export default ForgotPasswordPage
