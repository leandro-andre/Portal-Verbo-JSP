type PersonCardProps = {
  name: string
  department: string
  role: string
}

function PersonCard({ name, department, role }: PersonCardProps) {
  const avatarLetter = name.trim().charAt(0).toUpperCase()

  return (
    <article className="person-card">
      <div className="person-card__avatar" aria-hidden="true">
        {avatarLetter}
      </div>

      <div className="person-card__content">
        <h2 className="person-card__name">{name}</h2>
        <p className="person-card__meta">{department}</p>
        <p className="person-card__role">{role}</p>
      </div>

      <button className="button button--secondary" type="button">
        Ver perfil
      </button>
    </article>
  )
}

export default PersonCard
