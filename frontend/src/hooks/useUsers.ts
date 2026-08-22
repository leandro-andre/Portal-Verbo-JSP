import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { disableUser, enableUser, getUser, getUsers, linkUserPerson, unlinkUserPerson } from '../api/users'
import { currentUserQueryKey } from './useAuth'
import type { LinkUserPersonInput } from '../types/user'

export const usersQueryKey = ['users'] as const

export function userQueryKey(id: number) {
  return ['users', id] as const
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

export function useDisableUser(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => disableUser(id),
    onSuccess: async (user) => {
      queryClient.setQueryData(userQueryKey(id), user)
      await queryClient.invalidateQueries({ queryKey: usersQueryKey })
      await queryClient.invalidateQueries({ queryKey: currentUserQueryKey })
    },
  })
}

export function useEnableUser(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => enableUser(id),
    onSuccess: async (user) => {
      queryClient.setQueryData(userQueryKey(id), user)
      await queryClient.invalidateQueries({ queryKey: usersQueryKey })
      await queryClient.invalidateQueries({ queryKey: currentUserQueryKey })
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
      await queryClient.invalidateQueries({ queryKey: ['people'] })
    },
  })
}

export function useUnlinkUserPerson(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => unlinkUserPerson(id),
    onSuccess: async (user) => {
      queryClient.setQueryData(userQueryKey(id), user)
      await queryClient.invalidateQueries({ queryKey: usersQueryKey })
      await queryClient.invalidateQueries({ queryKey: ['people'] })
    },
  })
}
