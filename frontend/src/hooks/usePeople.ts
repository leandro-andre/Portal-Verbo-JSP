import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createPerson, getPeople, getPerson, updatePerson } from '../api/people'
import type { CreatePersonInput, UpdatePersonInput } from '../types/person'

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

export function useUpdatePerson(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: UpdatePersonInput) => updatePerson(id, payload),
    onSuccess: async (person) => {
      queryClient.setQueryData(personQueryKey(id), person)
      await queryClient.invalidateQueries({ queryKey: peopleQueryKey })
      await queryClient.invalidateQueries({ queryKey: personQueryKey(id) })
    },
  })
}
