import { ArrowLeft } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiHttpError } from '../api/people'
import PersonAvatar from '../components/people/PersonAvatar'
import PersonStatusBadge from '../components/people/PersonStatusBadge'
import { usePerson } from '../hooks/usePeople'
import type { Person } from '../types/person'

function formatDate(value: string) {
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

function ProfileSection({
  children,
  title,
}: {
  children: ReactNode
  title: string
}) {
  const titleId = title.toLowerCase().replace(/\s+/g, '-')

  return (
    <section className="profile-section" aria-labelledby={`profile-section-${titleId}`}>
      <h2 id={`profile-section-${titleId}`}>{title}</h2>
      <dl className="profile-details">{children}</dl>
    </section>
  )
}

function PersonProfile({ person }: { person: Person }) {
  const hasDifferentFullName = person.full_name !== person.display_name

  return (
    <>
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/pessoas">Pessoas</Link>
        <span aria-hidden="true">/</span>
        <strong>{person.display_name}</strong>
      </nav>

      <header className="profile-header">
        <PersonAvatar name={person.display_name} />
        <div className="profile-header__identity">
          <h1>{person.display_name}</h1>
          {hasDifferentFullName ? <p>{person.full_name}</p> : null}
          <PersonStatusBadge status={person.status} />
        </div>
      </header>

      <div className="profile-content">
        <ProfileSection title="Dados pessoais">
          <DetailItem label="Nome completo" value={person.full_name} />
          <DetailItem label="Nome preferido" value={person.preferred_name || '-'} />
          <DetailItem label="Data de nascimento" value={formatDate(person.birth_date)} />
        </ProfileSection>

        <ProfileSection title="Contato">
          <DetailItem label="E-mail" value={person.email || '-'} />
          <DetailItem label="Telefone" value={person.phone || '-'} />
        </ProfileSection>

        <ProfileSection title="Controle">
          <DetailItem label="Status" value={<PersonStatusBadge status={person.status} />} />
          <DetailItem label="Criado em" value={formatDate(person.created_at)} />
          <DetailItem label="Atualizado em" value={formatDate(person.updated_at)} />
        </ProfileSection>
      </div>
    </>
  )
}

function PersonProfilePage() {
  const { id } = useParams()
  const personId = Number(id)
  const isValidId = Number.isInteger(personId) && personId > 0
  const { data: person, error, isError, isLoading, refetch } = usePerson(personId)
  const isNotFound = !isValidId || (error instanceof ApiHttpError && error.status === 404)

  return (
    <section className="person-profile-page">
      {isLoading && isValidId ? (
        <div className="state-panel">
          <h1>Carregando pessoa...</h1>
          <p>Aguarde enquanto os dados sao carregados.</p>
        </div>
      ) : isNotFound ? (
        <div className="state-panel">
          <h1>Pessoa nao encontrada</h1>
          <p>Nao encontramos a pessoa solicitada.</p>
          <Link className="button button--secondary" to="/pessoas">
            <ArrowLeft size={17} aria-hidden="true" />
            Voltar para Pessoas
          </Link>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h1>Nao foi possivel carregar os dados da pessoa.</h1>
          <p>Verifique a conexao com o backend e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            Tentar novamente
          </button>
        </div>
      ) : person ? (
        <PersonProfile person={person} />
      ) : null}
    </section>
  )
}

export default PersonProfilePage
