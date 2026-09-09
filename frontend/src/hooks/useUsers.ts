import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  disableUser,
  enableUser,
  getUser,
  getUserAdminProfile,
  getUserPersonCandidates,
  getUsers,
  linkUserPerson,
  resendUserActivation,
  sendUserPasswordReset,
} from '../api/users'
import { currentUserQueryKey } from './useAuth'
import type { LinkUserPersonInput } from '../types/user'

export const usersQueryKey = ['users'] as const

export function userQueryKey(id: number) {
  return ['users', id] as const
}

export function userAdminProfileQueryKey(id: number) {
  return ['users', id, 'admin-profile'] as const
}

export function userPersonCandidatesQueryKey(id: number, search: string) {
  return ['users', id, 'person-candidates', search.trim()] as const
}

export function useUsers() {
  return useQuery({
    queryKey: usersQueryKey,
    queryFn: getUsers,
  })
}

export function useUser(id: number) {
  return useQuery({
    queryKey: userQueryKey(id),
    queryFn: () => getUser(id),
    enabled: Number.isFinite(id) && id > 0,
  })
}

export function useUserAdminProfile(id: number) {
  return useQuery({
    queryKey: userAdminProfileQueryKey(id),
    queryFn: () => getUserAdminProfile(id),
    enabled: Number.isFinite(id) && id > 0,
  })
}

export function useUserPersonCandidates(id: number, search: string, enabled = true) {
  const normalizedSearch = search.trim()
  return useQuery({
    queryKey: userPersonCandidatesQueryKey(id, normalizedSearch),
    queryFn: () => getUserPersonCandidates(id, normalizedSearch),
    enabled: enabled && Number.isFinite(id) && id > 0 && normalizedSearch.length >= 2,
  })
}

export function useDisableUser(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => disableUser(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: userQueryKey(id) })
      await queryClient.invalidateQueries({ queryKey: userAdminProfileQueryKey(id) })
      await queryClient.invalidateQueries({ queryKey: usersQueryKey })
      await queryClient.invalidateQueries({ queryKey: currentUserQueryKey })
    },
  })
}

export function useEnableUser(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => enableUser(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: userQueryKey(id) })
      await queryClient.invalidateQueries({ queryKey: userAdminProfileQueryKey(id) })
      await queryClient.invalidateQueries({ queryKey: usersQueryKey })
      await queryClient.invalidateQueries({ queryKey: currentUserQueryKey })
    },
  })
}

export function useResendUserActivation(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => resendUserActivation(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: userAdminProfileQueryKey(id) })
    },
  })
}

export function useSendUserPasswordReset(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => sendUserPasswordReset(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: userAdminProfileQueryKey(id) })
    },
  })
}

export function useLinkUserPerson(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: LinkUserPersonInput) => linkUserPerson(id, payload),
    onSuccess: async (user) => {
      queryClient.setQueryData(userQueryKey(id), user)
      await queryClient.invalidateQueries({ queryKey: usersQueryKey })
      await queryClient.invalidateQueries({ queryKey: userAdminProfileQueryKey(id) })
      await queryClient.invalidateQueries({ queryKey: ['people'] })
    },
  })
}
