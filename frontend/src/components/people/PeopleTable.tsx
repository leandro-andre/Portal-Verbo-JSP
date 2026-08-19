import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Person } from '../../types/person'
import PersonAvatar from './PersonAvatar'
import PersonStatusBadge from './PersonStatusBadge'

type PeopleTableProps = {
  people: Person[]
}

function formatBirthDate(value: string) {
  if (!value) {
    return '-'
  }

  const [year, month, day] = value.split('-')
  if (!year || !month || !day) {
    return value
  }

  return `${day}/${month}/${year}`
}

function PeopleTable({ people }: PeopleTableProps) {
  return (
    <div className="table-shell">
      <table className="people-table">
        <thead>
          <tr>
            <th scope="col">Pessoa</th>
            <th scope="col">Contato</th>
            <th scope="col">Nascimento</th>
            <th scope="col">Status</th>
            <th scope="col" className="people-table__actions-header">
              Perfil
            </th>
          </tr>
        </thead>
        <tbody>
          {people.map((person) => {
            const hasDifferentFullName = person.full_name !== person.display_name

            return (
              <tr key={person.id}>
                <td>
                  <div className="person-cell">
                    <PersonAvatar name={person.display_name} />
                    <div>
                      <Link className="person-name-link" to={`/pessoas/${person.id}`}>
                        {person.display_name}
                      </Link>
                      {hasDifferentFullName ? <span>{person.full_name}</span> : null}
                    </div>
                  </div>
                </td>
                <td>
                  <div className="contact-cell">
                    <span>{person.email || '-'}</span>
                    {person.phone ? <span>{person.phone}</span> : null}
                  </div>
                </td>
                <td>{formatBirthDate(person.birth_date)}</td>
                <td>
                  <PersonStatusBadge status={person.status} />
                </td>
                <td>
                  <Link
                    className="icon-button icon-button--table"
                    to={`/pessoas/${person.id}`}
                    aria-label={`Abrir perfil de ${person.display_name}`}
                  >
                    <ChevronRight size={18} aria-hidden="true" />
                  </Link>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default PeopleTable
