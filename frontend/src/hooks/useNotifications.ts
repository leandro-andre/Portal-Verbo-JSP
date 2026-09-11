import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getNotifications,
  getRecentNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../api/notifications'

export const notificationsQueryKey = ['notifications'] as const
export const recentNotificationsQueryKey = ['notifications', 'recent'] as const

export function useNotifications() {
  return useQuery({
    queryKey: notificationsQueryKey,
    queryFn: getNotifications,
  })
}

export function useRecentNotifications() {
  return useQuery({
    queryKey: recentNotificationsQueryKey,
    queryFn: getRecentNotifications,
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  })
}

export function useNotificationMutations() {
  const queryClient = useQueryClient()
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: notificationsQueryKey })
    await queryClient.invalidateQueries({ queryKey: recentNotificationsQueryKey })
  }

  return {
    markRead: useMutation({ mutationFn: markNotificationRead, onSuccess: invalidate }),
    markAllRead: useMutation({ mutationFn: markAllNotificationsRead, onSuccess: invalidate }),
  }
}
