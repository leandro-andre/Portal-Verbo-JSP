import { useState } from 'react'
import PersonCard from '../components/PersonCard'

type Person = {
  id: number
  name: string
  department: string
  role: string
}

const people: Person[] = [
  {
    id: 1,
    name: 'Geysika',
    department: 'Juniores',
    role: 'Professora',
  },
  {
    id: 2,
    name: 'Gledson',
    department: 'Juniores',
    role: 'Professor',
  },
  {
    id: 3,
    name: 'Vânia',
    department: 'Juniores',
    role: 'Professora',
  },
]

function PeoplePage() {
  const [search, setSearch] = useState('')

  const filteredPeople = people.filter((person) =>
    person.name.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <section className="people-page" id="pessoas">
      <div className="page-heading">
        <div>
          <p className="page-heading__eyebrow">Gestão de pessoas</p>
          <h1>Pessoas</h1>
          <p className="page-heading__description">
            Gerencie pessoas, vínculos e participação nos departamentos da igreja.
          </p>
        </div>

        <button className="button button--primary" type="button">
          Nova pessoa
        </button>
      </div>

      <div className="people-toolbar">
        <label className="search-field" htmlFor="people-search">
          <span>Buscar pessoa</span>
          <input
            id="people-search"
            type="search"
            placeholder="Buscar por nome"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <p className="people-count">
          {filteredPeople.length}{' '}
          {filteredPeople.length === 1 ? 'pessoa encontrada' : 'pessoas encontradas'}
        </p>
      </div>

      {filteredPeople.length > 0 ? (
        <div className="people-list">
          {filteredPeople.map((person) => (
            <PersonCard
              key={person.id}
              name={person.name}
              department={person.department}
              role={person.role}
            />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <h2>Nenhuma pessoa encontrada</h2>
          <p>Tente buscar por outro nome.</p>
        </div>
      )}
    </section>
  )
}

export default PeoplePage
