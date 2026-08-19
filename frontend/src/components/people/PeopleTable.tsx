import { MoreVertical } from 'lucide-react'
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
              Acoes
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
                      <strong>{person.display_name}</strong>
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
                  <button className="icon-button icon-button--table" type="button" aria-label={`Acoes de ${person.display_name}`}>
                    <MoreVertical size={18} aria-hidden="true" />
                  </button>
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
