import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createPerson, getPeople, getPerson } from '../api/people'
import type { CreatePersonInput } from '../types/person'

export const peopleQueryKey = ['people']

export function personQueryKey(id: number) {
  return ['people', id] as const
}

export function usePeople() {
  return useQuery({
    queryKey: peopleQueryKey,
    queryFn: getPeople,
  })
}

export function usePerson(id: number) {
  return useQuery({
    queryKey: personQueryKey(id),
    queryFn: () => getPerson(id),
    enabled: Number.isFinite(id),
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
