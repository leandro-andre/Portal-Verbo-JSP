import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createPerson,
  getChurchJourney,
  getPeople,
  getPerson,
  startChurchJourney,
  updatePerson,
} from '../api/people'
import type { CreatePersonInput, StartChurchJourneyInput, UpdatePersonInput } from '../types/person'

export const peopleQueryKey = ['people']

export function personQueryKey(id: number) {
  return ['people', id] as const
}

export function churchJourneyQueryKey(personId: number) {
  return ['people', personId, 'church-journey'] as const
}

export function usePeople() {
  return useQuery({
    queryKey: peopleQueryKey,
    queryFn: () => getPeople(),
  })
}

export function usePeopleSearch(search: string, enabled = true) {
  const normalizedSearch = search.trim()
  return useQuery({
    queryKey: [...peopleQueryKey, 'search', normalizedSearch],
    queryFn: () => getPeople(normalizedSearch),
    enabled: enabled && normalizedSearch.length >= 2,
  })
}

export function usePerson(id: number) {
  return useQuery({
    queryKey: personQueryKey(id),
    queryFn: () => getPerson(id),
    enabled: Number.isFinite(id),
  })
}

export function useChurchJourney(personId: number, enabled: boolean) {
  return useQuery({
    queryKey: churchJourneyQueryKey(personId),
    queryFn: () => getChurchJourney(personId),
    enabled: enabled && Number.isFinite(personId),
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

export function useStartChurchJourney(personId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: StartChurchJourneyInput) => startChurchJourney(personId, payload),
    onSuccess: async (journey) => {
      queryClient.setQueryData(churchJourneyQueryKey(personId), journey)
      await queryClient.invalidateQueries({ queryKey: churchJourneyQueryKey(personId) })
      await queryClient.invalidateQueries({ queryKey: personQueryKey(personId) })
    },
  })
}
