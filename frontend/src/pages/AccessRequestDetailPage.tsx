import { useState } from 'react'
import { ArrowLeft, CheckCircle2, XCircle } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import AccessRequestStatusBadge from '../components/accessRequests/AccessRequestStatusBadge'
import { AccessRequestBusinessError, AccessRequestHttpError } from '../api/accessRequests'
import {
  useAccessRequest,
  useApproveAccessRequest,
  useRejectAccessRequest,
} from '../hooks/useAccessRequests'
import { useCan } from '../hooks/useAuth'
import type { AccessRequest, AccessRequestPerson } from '../types/accessRequest'
import { formatBrazilianMobile } from '../utils/phone'

type IdentityResolution =
  | { type: 'existing'; personId: number }
  | { type: 'new' }
  | null

function formatDate(value?: string | null) {
  if (!value) {
    return '-'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    const [year, month, day] = value.split('-')
    return year && month && day ? `${day}/${month}/${year}` : value
  }

  return new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' }).format(date)
}

function DetailItem({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="profile-detail">
      <dt>{label}</dt>
      <dd>{value || '-'}</dd>
    </div>
  )
}

function CandidateCard({
  candidate,
  isSelected,
  onSelect,
}: {
  candidate: AccessRequestPerson
  isSelected: boolean
  onSelect: () => void
}) {
  return (
    <label className={`identity-option${isSelected ? ' identity-option--selected' : ''}`}>
      <input type="radio" checked={isSelected} onChange={onSelect} />
      <span>
        <strong>{candidate.display_name}</strong>
        <span>{formatDate(candidate.birth_date)}</span>
        <span>{candidate.email || '-'}</span>
        <span>{formatBrazilianMobile(candidate.phone) || '-'}</span>
      </span>
    </label>
  )
}

function ReviewDialog({
  error,
  isOpen,
  isPending,
  mode,
  onClose,
  onConfirmApprove,
  onConfirmReject,
  rejectionReason,
  request,
  resolution,
  setRejectionReason,
}: {
  error: string | null
  isOpen: boolean
  isPending: boolean
  mode: 'approve' | 'reject'
  onClose: () => void
  onConfirmApprove: () => void
  onConfirmReject: () => void
  rejectionReason: string
  request: AccessRequest
  resolution: IdentityResolution
  setRejectionReason: (value: string) => void
}) {
  if (!isOpen) {
    return null
  }

  const isApprove = mode === 'approve'
  const selectedCandidate = resolution?.type === 'existing'
    ? request.candidates.find((candidate) => candidate.id === resolution.personId)
    : null

  return (
    <div className="dialog-backdrop" role="presentation">
      <div
        className="confirm-dialog"
        role="dialog"
        aria-labelledby="access-review-dialog-title"
        aria-modal="true"
      >
        <h2 id="access-review-dialog-title">
          {isApprove
            ? `Aprovar acesso para ${request.full_name}?`
            : `Rejeitar solicitacao de ${request.full_name}?`}
        </h2>
        <p>
          {isApprove && resolution?.type === 'new'
            ? 'Uma nova pessoa sera cadastrada. O usuario solicitado sera ativado apos a aprovacao.'
            : null}
          {isApprove && selectedCandidate
            ? `O acesso sera vinculado a ${selectedCandidate.display_name} ja cadastrada. O usuario solicitado sera ativado apos a aprovacao.`
            : null}
          {!isApprove ? 'A solicitacao sera preservada com status rejeitado.' : null}
        </p>

        {!isApprove ? (
          <label className="field-group" htmlFor="rejection_reason">
            <span>Motivo opcional</span>
            <textarea
              id="rejection_reason"
              className="textarea-control"
              rows={4}
              value={rejectionReason}
              onChange={(event) => setRejectionReason(event.target.value)}
            />
          </label>
        ) : null}

        {error ? (
          <div className="form-alert form-alert--error" role="alert">
            {error}
          </div>
        ) : null}

        <div className="form-actions">
          <button className="button button--secondary" type="button" disabled={isPending} onClick={onClose}>
            Cancelar
          </button>
          <button
            className="button button--primary"
            type="button"
            disabled={isPending}
            onClick={isApprove ? onConfirmApprove : onConfirmReject}
          >
            {isApprove ? <CheckCircle2 size={17} aria-hidden="true" /> : <XCircle size={17} aria-hidden="true" />}
            {isPending
              ? isApprove ? 'Aprovando...' : 'Rejeitando...'
              : isApprove ? 'Aprovar acesso' : 'Confirmar rejeicao'}
          </button>
        </div>
      </div>
    </div>
  )
}

function AccessRequestDetail({ request }: { request: AccessRequest }) {
  const approveRequest = useApproveAccessRequest(request.id)
  const rejectRequest = useRejectAccessRequest(request.id)
  const [resolution, setResolution] = useState<IdentityResolution>(null)
  const [dialogMode, setDialogMode] = useState<'approve' | 'reject' | null>(null)
  const [dialogError, setDialogError] = useState<string | null>(null)
  const [rejectionReason, setRejectionReason] = useState('')
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [approvedUsername, setApprovedUsername] = useState<string | null>(null)
  const canApproveRequest = useCan('ACCESS_REQUEST_APPROVE')
  const canRejectRequest = useCan('ACCESS_REQUEST_REJECT')
  const isPending = request.status === 'PENDING'
  const canApprove = isPending && canApproveRequest && resolution !== null

  const handleBusinessError = (error: unknown) => {
    if (error instanceof AccessRequestBusinessError) {
      if (error.details.code === 'PERSON_ALREADY_HAS_USER') {
        setDialogError('Esta pessoa ja possui acesso ao Portal.')
        return
      }
      if (error.details.code === 'ACCESS_REQUEST_NOT_PENDING') {
        setDialogError('Esta solicitacao ja foi revisada.')
        return
      }
      if (error.details.code === 'INVALID_WHATSAPP') {
        setDialogError('Nao foi possivel aprovar: o celular/WhatsApp informado e invalido.')
        return
      }
    }

    setDialogError('Nao foi possivel processar a solicitacao. Tente novamente.')
  }

  const handleApprove = async () => {
    if (!resolution) {
      return
    }

    setDialogError(null)
    try {
      const response = await approveRequest.mutateAsync(
        resolution.type === 'existing'
          ? { person_id: resolution.personId }
          : { create_new_person: true },
      )
      setDialogMode(null)
      setSuccessMessage(
        response.notification?.email_sent
          ? 'Acesso aprovado e e-mail enviado.'
          : 'Acesso aprovado. Nao foi possivel enviar o e-mail agora.',
      )
      setApprovedUsername(response.created_user.username)
    } catch (error) {
      handleBusinessError(error)
    }
  }

  const handleReject = async () => {
    setDialogError(null)
    try {
      await rejectRequest.mutateAsync({ rejection_reason: rejectionReason })
      setDialogMode(null)
      setSuccessMessage('Solicitacao rejeitada.')
      setApprovedUsername(null)
    } catch (error) {
      handleBusinessError(error)
    }
  }

  return (
    <>
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/solicitacoes-acesso">Solicitacoes</Link>
        <span aria-hidden="true">/</span>
        <strong>{request.full_name}</strong>
      </nav>

      <Link className="back-link" to="/solicitacoes-acesso">
        <ArrowLeft size={17} aria-hidden="true" />
        Voltar para solicitacoes
      </Link>

      <div className="page-heading">
        <div>
          <h1>{request.full_name}</h1>
          <p className="page-heading__description">Revise a solicitacao de acesso ao Portal.</p>
        </div>
        <AccessRequestStatusBadge status={request.status} />
      </div>

      {successMessage ? (
        <div className="form-alert form-alert--success" role="status">
          {successMessage}
          {approvedUsername ? (
            <span className="activation-link">
              Username: <strong>{approvedUsername}</strong>
            </span>
          ) : null}
        </div>
      ) : null}

      <div className="profile-content">
        <section className="profile-section">
          <h2>Dados informados</h2>
          <dl className="profile-details">
            <DetailItem label="Nome completo" value={request.full_name} />
            <DetailItem label="Data de nascimento" value={formatDate(request.birth_date)} />
            <DetailItem label="E-mail" value={request.email} />
            <DetailItem label="Celular / WhatsApp" value={formatBrazilianMobile(request.phone) || '-'} />
            <DetailItem label="Solicitado em" value={formatDate(request.created_at)} />
          </dl>
        </section>

        <section className="profile-section">
          <h2>Acesso solicitado</h2>
          <dl className="profile-details">
            <DetailItem label="Usuario" value={request.usuario?.username || '-'} />
            <DetailItem
              label="Status do acesso"
              value={request.usuario?.access_status === 'PENDING_APPROVAL' ? 'Aguardando aprovacao' : '-'}
            />
          </dl>
        </section>

        <section className="profile-section">
          <h2>Status</h2>
          <dl className="profile-details">
            <DetailItem label="Status" value={<AccessRequestStatusBadge status={request.status} />} />
            <DetailItem label="Revisado por" value={request.reviewed_by?.display_name || '-'} />
            <DetailItem label="Revisado em" value={formatDate(request.reviewed_at)} />
            {request.status === 'REJECTED' ? (
              <DetailItem label="Motivo da rejeicao" value={request.rejection_reason || '-'} />
            ) : null}
          </dl>
        </section>

        {isPending && canApproveRequest ? (
          <section className="profile-section">
            <h2>Resolucao de identidade</h2>
            <div className="identity-resolution">
              {request.candidates.length > 0 ? (
                <div className="identity-options">
                  {request.candidates.map((candidate) => (
                    <CandidateCard
                      candidate={candidate}
                      isSelected={resolution?.type === 'existing' && resolution.personId === candidate.id}
                      key={candidate.id}
                      onSelect={() => setResolution({ type: 'existing', personId: candidate.id })}
                    />
                  ))}
                </div>
              ) : (
                <p className="page-heading__description">Nenhuma pessoa correspondente encontrada.</p>
              )}

              <label className={`identity-option${resolution?.type === 'new' ? ' identity-option--selected' : ''}`}>
                <input
                  type="radio"
                  checked={resolution?.type === 'new'}
                  onChange={() => setResolution({ type: 'new' })}
                />
                <span>
                  <strong>Criar nova pessoa</strong>
                  <span>Usar nome, nascimento, e-mail e celular/WhatsApp informados nesta solicitacao.</span>
                </span>
              </label>
            </div>
          </section>
        ) : null}
      </div>

      {isPending && (canRejectRequest || canApproveRequest) ? (
        <div className="review-actions">
          {canRejectRequest ? (
            <button
              className="button button--secondary"
              type="button"
              onClick={() => {
                setDialogError(null)
                setDialogMode('reject')
              }}
            >
              <XCircle size={17} aria-hidden="true" />
              Rejeitar solicitacao
            </button>
          ) : null}
          {canApproveRequest ? (
            <button
              className="button button--primary"
              type="button"
              disabled={!canApprove}
              onClick={() => {
                setDialogError(null)
                setDialogMode('approve')
              }}
            >
              <CheckCircle2 size={17} aria-hidden="true" />
              Aprovar acesso
            </button>
          ) : null}
        </div>
      ) : null}

      <ReviewDialog
        error={dialogError}
        isOpen={dialogMode !== null}
        isPending={approveRequest.isPending || rejectRequest.isPending}
        mode={dialogMode ?? 'approve'}
        onClose={() => setDialogMode(null)}
        onConfirmApprove={() => void handleApprove()}
        onConfirmReject={() => void handleReject()}
        rejectionReason={rejectionReason}
        request={request}
        resolution={resolution}
        setRejectionReason={setRejectionReason}
      />
    </>
  )
}

function AccessRequestDetailPage() {
  const { id } = useParams()
  const requestId = Number(id)
  const isValidId = Number.isInteger(requestId) && requestId > 0
  const { data: request, error, isError, isLoading, refetch } = useAccessRequest(requestId)
  const isForbidden = error instanceof AccessRequestHttpError && error.status === 403
  const isNotFound = !isValidId || (error instanceof AccessRequestHttpError && error.status === 404)

  return (
    <section className="person-profile-page">
      {isLoading && isValidId ? (
        <div className="state-panel">
          <h1>Carregando solicitacao...</h1>
          <p>Aguarde enquanto os dados sao carregados.</p>
        </div>
      ) : isNotFound ? (
        <div className="state-panel">
          <h1>Solicitacao nao encontrada</h1>
          <p>Nao encontramos a solicitacao solicitada.</p>
          <Link className="button button--secondary" to="/solicitacoes-acesso">
            Voltar para solicitacoes
          </Link>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h1>{isForbidden ? 'Acesso nao autorizado.' : 'Nao foi possivel carregar a solicitacao.'}</h1>
          <p>
            {isForbidden
              ? 'Sua sessao atual nao possui permissao para revisar solicitacoes de acesso.'
              : 'Verifique a conexao com o backend e tente novamente.'}
          </p>
          {!isForbidden ? (
            <button className="button button--secondary" type="button" onClick={() => void refetch()}>
              Tentar novamente
            </button>
          ) : null}
        </div>
      ) : request ? (
        <AccessRequestDetail request={request} />
      ) : null}
    </section>
  )
}

export default AccessRequestDetailPage
