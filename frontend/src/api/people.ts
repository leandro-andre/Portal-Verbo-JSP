import type { Person } from '../types/person'

export async function getPeople(): Promise<Person[]> {
  const response = await fetch('/api/people/')

  if (!response.ok) {
    throw new Error('Nao foi possivel carregar as pessoas.')
  }

  return response.json() as Promise<Person[]>
}
