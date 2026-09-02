import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createPerson,
  createMyUnavailability,
  createPersonUnavailability,
  approveMembership,
  deactivateMembership,
  deactivateMyUnavailability,
  deactivatePersonUnavailability,
  getEligibleMembershipPeople,
  getChurchJourney,
  getMembership,
  getMembershipHistory,
  getMemberships,
  getMyUnavailability,
  getPeople,
  getPerson,
  getPerson360,
  getPersonUnavailability,
  reactivateMembership,
  reactivateMyUnavailability,
  reactivatePersonUnavailability,
  startChurchJourney,
  updateMyUnavailability,
  updatePerson,
  updatePersonUnavailability,
} from '../api/people'
import type {
  CreatePersonInput,
  MembershipStatus,
  PersonUnavailabilityInput,
  StartChurchJourneyInput,
  UpdatePersonInput,
} from '../types/person'

export const peopleQueryKey = ['people']

export function personQueryKey(id: number) {
  return ['people', id] as const
}

export function person360QueryKey(id: number) {
  return ['people', id, '360'] as const
}

export function churchJourneyQueryKey(personId: number) {
  return ['people', personId, 'church-journey'] as const
}

export function membershipQueryKey(personId: number) {
  return ['people', personId, 'membership'] as const
}

export function membershipHistoryQueryKey(personId: number) {
  return ['people', personId, 'membership-history'] as const
}

export const eligibleMembershipPeopleQueryKey = ['membership', 'eligible'] as const
export const myUnavailabilityQueryKey = ['me', 'unavailability'] as const

export function membershipsQueryKey(status?: MembershipStatus) {
  return ['memberships', status ?? 'ALL'] as const
}

export function personUnavailabilityQueryKey(personId: number) {
  return ['people', personId, 'unavailability'] as const
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

export function usePerson360(id: number) {
  return useQuery({
    queryKey: person360QueryKey(id),
    queryFn: () => getPerson360(id),
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

export function useMembership(personId: number, enabled: boolean) {
  return useQuery({
    queryKey: membershipQueryKey(personId),
    queryFn: () => getMembership(personId),
    enabled: enabled && Number.isFinite(personId),
  })
}

export function useEligibleMembershipPeople() {
  return useQuery({
    queryKey: eligibleMembershipPeopleQueryKey,
    queryFn: getEligibleMembershipPeople,
  })
}

export function useMemberships(status?: MembershipStatus) {
  return useQuery({
    queryKey: membershipsQueryKey(status),
    queryFn: () => getMemberships(status),
  })
}

export function useMyUnavailability() {
  return useQuery({
    queryKey: myUnavailabilityQueryKey,
    queryFn: getMyUnavailability,
  })
}

export function usePersonUnavailability(personId: number, enabled: boolean) {
  return useQuery({
    queryKey: personUnavailabilityQueryKey(personId),
    queryFn: () => getPersonUnavailability(personId),
    enabled: enabled && Number.isFinite(personId),
  })
}

export function useMembershipHistory(personId: number, enabled: boolean) {
  return useQuery({
    queryKey: membershipHistoryQueryKey(personId),
    queryFn: () => getMembershipHistory(personId),
    enabled: enabled && Number.isFinite(personId),
  })
}

async function invalidateMembershipQueries(
  queryClient: ReturnType<typeof useQueryClient>,
  personId: number,
) {
  await queryClient.invalidateQueries({ queryKey: personQueryKey(personId) })
  await queryClient.invalidateQueries({ queryKey: churchJourneyQueryKey(personId) })
  await queryClient.invalidateQueries({ queryKey: membershipQueryKey(personId) })
  await queryClient.invalidateQueries({ queryKey: membershipHistoryQueryKey(personId) })
  await queryClient.invalidateQueries({ queryKey: eligibleMembershipPeopleQueryKey })
  await queryClient.invalidateQueries({ queryKey: ['memberships'] })
  await queryClient.invalidateQueries({ queryKey: peopleQueryKey })
}

export function useApproveMembership(personId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => approveMembership(personId),
    onSuccess: async (membership) => {
      queryClient.setQueryData(membershipQueryKey(personId), membership)
      await invalidateMembershipQueries(queryClient, personId)
    },
  })
}

export function useDeactivateMembership(personId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (reason: string) => deactivateMembership(personId, reason),
    onSuccess: async (membership) => {
      queryClient.setQueryData(membershipQueryKey(personId), membership)
      await invalidateMembershipQueries(queryClient, personId)
    },
  })
}

export function useReactivateMembership(personId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (reason: string) => reactivateMembership(personId, reason),
    onSuccess: async (membership) => {
      queryClient.setQueryData(membershipQueryKey(personId), membership)
      await invalidateMembershipQueries(queryClient, personId)
    },
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

export function useMyUnavailabilityMutations() {
  const queryClient = useQueryClient()

  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: myUnavailabilityQueryKey })
  }

  return {
    create: useMutation({ mutationFn: (payload: PersonUnavailabilityInput) => createMyUnavailability(payload), onSuccess }),
    update: useMutation({
      mutationFn: ({ id, payload }: { id: number; payload: PersonUnavailabilityInput }) =>
        updateMyUnavailability(id, payload),
      onSuccess,
    }),
    deactivate: useMutation({ mutationFn: (id: number) => deactivateMyUnavailability(id), onSuccess }),
    reactivate: useMutation({ mutationFn: (id: number) => reactivateMyUnavailability(id), onSuccess }),
  }
}

export function usePersonUnavailabilityMutations(personId: number) {
  const queryClient = useQueryClient()

  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: personUnavailabilityQueryKey(personId) })
  }

  return {
    create: useMutation({
      mutationFn: (payload: PersonUnavailabilityInput) => createPersonUnavailability(personId, payload),
      onSuccess,
    }),
    update: useMutation({
      mutationFn: ({ id, payload }: { id: number; payload: PersonUnavailabilityInput }) =>
        updatePersonUnavailability(personId, id, payload),
      onSuccess,
    }),
    deactivate: useMutation({ mutationFn: (id: number) => deactivatePersonUnavailability(personId, id), onSuccess }),
    reactivate: useMutation({ mutationFn: (id: number) => reactivatePersonUnavailability(personId, id), onSuccess }),
  }
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
