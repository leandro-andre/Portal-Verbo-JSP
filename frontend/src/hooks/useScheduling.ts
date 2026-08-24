import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  addScheduleAssignment,
  createSchedule,
  deleteScheduleAssignment,
  getSchedule,
  getScheduleCandidates,
  getMonthlySchedule,
  getSchedulingDepartments,
  getSchedules,
  runScheduleLifecycle,
} from '../api/scheduling'
import type { ScheduleCreateInput } from '../types/scheduling'

export function schedulesQueryKey(year: number, month: number, departmentId: string, status: string) {
  return ['scheduling', 'schedules', year, month, departmentId, status] as const
}

export const schedulingDepartmentsQueryKey = ['scheduling', 'departments'] as const

export function monthlyScheduleQueryKey(year: number, month: number, departmentId: string) {
  return ['scheduling', 'monthly', year, month, departmentId] as const
}

export function scheduleQueryKey(id: number) {
  return ['scheduling', 'schedule', id] as const
}

export function scheduleCandidatesQueryKey(id: number) {
  return ['scheduling', 'schedule', id, 'candidates'] as const
}

export function useSchedules(year: number, month: number, departmentId: string, status: string) {
  return useQuery({
    queryKey: schedulesQueryKey(year, month, departmentId, status),
    queryFn: () => getSchedules({ year, month, departmentId, status }),
  })
}

export function useSchedulingDepartments() {
  return useQuery({
    queryKey: schedulingDepartmentsQueryKey,
    queryFn: getSchedulingDepartments,
  })
}

export function useMonthlySchedule(year: number, month: number, departmentId: string) {
  return useQuery({
    queryKey: monthlyScheduleQueryKey(year, month, departmentId),
    queryFn: () => getMonthlySchedule(year, month, departmentId),
    enabled: Boolean(departmentId),
  })
}

export function useCreateSchedule(year: number, month: number, departmentId: string, status: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ScheduleCreateInput) => createSchedule(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: schedulesQueryKey(year, month, departmentId, status) })
      await queryClient.invalidateQueries({ queryKey: monthlyScheduleQueryKey(year, month, departmentId) })
    },
  })
}

export function useSchedule(id: number) {
  return useQuery({
    queryKey: scheduleQueryKey(id),
    queryFn: () => getSchedule(id),
    enabled: Number.isFinite(id),
  })
}

export function useScheduleCandidates(id: number, roleId?: number, enabled = true) {
  return useQuery({
    queryKey: [...scheduleCandidatesQueryKey(id), roleId ?? 'all'] as const,
    queryFn: () => getScheduleCandidates(id, roleId),
    enabled: enabled && Number.isFinite(id),
  })
}

export function useScheduleMutations(id: number) {
  const queryClient = useQueryClient()
  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: scheduleQueryKey(id) })
    await queryClient.invalidateQueries({ queryKey: scheduleCandidatesQueryKey(id) })
    await queryClient.invalidateQueries({ queryKey: ['scheduling', 'schedules'] })
    await queryClient.invalidateQueries({ queryKey: ['scheduling', 'monthly'] })
  }
  return {
    publish: useMutation({ mutationFn: () => runScheduleLifecycle(id, 'publish'), onSuccess }),
    reopen: useMutation({ mutationFn: () => runScheduleLifecycle(id, 'reopen'), onSuccess }),
    cancel: useMutation({ mutationFn: () => runScheduleLifecycle(id, 'cancel'), onSuccess }),
    reactivate: useMutation({ mutationFn: () => runScheduleLifecycle(id, 'reactivate'), onSuccess }),
    addAssignment: useMutation({ mutationFn: (departmentMembershipId: number) => addScheduleAssignment(id, departmentMembershipId), onSuccess }),
    deleteAssignment: useMutation({ mutationFn: (assignmentId: number) => deleteScheduleAssignment(id, assignmentId), onSuccess }),
  }
}
