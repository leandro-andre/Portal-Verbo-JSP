import { useQuery } from '@tanstack/react-query'
import { getMyDashboard } from '../api/dashboard'

export const myDashboardQueryKey = ['me', 'dashboard'] as const

export function useMyDashboard() {
  return useQuery({
    queryKey: myDashboardQueryKey,
    queryFn: getMyDashboard,
  })
}
