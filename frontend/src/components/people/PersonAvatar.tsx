type PersonAvatarProps = {
  name: string
}

function getInitials(name: string) {
  const parts = name
    .trim()
    .split(/\s+/)
    .filter(Boolean)

  if (parts.length === 0) {
    return 'P'
  }

  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase()
  }

  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
}

function PersonAvatar({ name }: PersonAvatarProps) {
  return (
    <span className="person-avatar" aria-hidden="true">
      {getInitials(name)}
    </span>
  )
}

export default PersonAvatar
