import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { activateAccount, getCurrentUser, login, logout } from '../api/auth'
import type { ActivateAccountInput, Capability, CurrentUserResponse, LoginInput } from '../types/auth'

export const currentUserQueryKey = ['auth', 'current-user'] as const

export function useCurrentUser() {
  return useQuery({
    queryKey: currentUserQueryKey,
    queryFn: getCurrentUser,
    staleTime: 30_000,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: LoginInput) => login(payload),
    onSuccess: (response) => {
      queryClient.setQueryData<CurrentUserResponse>(currentUserQueryKey, response)
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData<CurrentUserResponse>(currentUserQueryKey, {
        is_authenticated: false,
        user: null,
      })
    },
  })
}

export function useActivateAccount() {
  return useMutation({
    mutationFn: (payload: ActivateAccountInput) => activateAccount(payload),
  })
}

export function useCan(capability: Capability) {
  const { data: currentUser } = useCurrentUser()
  return Boolean(currentUser?.user?.capabilities.includes(capability))
}
