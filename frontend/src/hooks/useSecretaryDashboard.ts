import { useQuery } from '@tanstack/react-query'
import { getSecretaryDashboard } from '../api/secretaryDashboard'

export const secretaryDashboardQueryKey = ['secretaria', 'dashboard'] as const

export function useSecretaryDashboard() {
  return useQuery({
    queryKey: secretaryDashboardQueryKey,
    queryFn: getSecretaryDashboard,
  })
}
