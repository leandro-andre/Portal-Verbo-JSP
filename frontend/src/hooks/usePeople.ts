import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createPerson, getPeople } from '../api/people'
import type { CreatePersonInput } from '../types/person'

export const peopleQueryKey = ['people']

export function usePeople() {
  return useQuery({
    queryKey: peopleQueryKey,
    queryFn: getPeople,
  })
}

export function useCreatePerson() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreatePersonInput) => createPerson(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: peopleQueryKey })
    },
  })
}
