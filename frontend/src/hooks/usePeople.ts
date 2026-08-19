import { useQuery } from '@tanstack/react-query'
import { getPeople } from '../api/people'

export function usePeople() {
  return useQuery({
    queryKey: ['people'],
    queryFn: getPeople,
  })
}
