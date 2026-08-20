import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  cancelDiscipleshipClass,
  completeDiscipleshipClass,
  createDiscipleshipEnrollment,
  createDiscipleshipClass,
  getDiscipleshipClass,
  getDiscipleshipClasses,
  getDiscipleshipEnrollment,
  getDiscipleshipEnrollments,
  startDiscipleshipClass,
  updateDiscipleshipClass,
  withdrawDiscipleshipEnrollment,
} from '../api/discipleship'
import type {
  CreateDiscipleshipClassInput,
  CreateDiscipleshipEnrollmentInput,
  UpdateDiscipleshipClassInput,
} from '../types/discipleship'

export const discipleshipClassesQueryKey = ['discipleship', 'classes'] as const

export function discipleshipClassQueryKey(id: number) {
  return ['discipleship', 'classes', id] as const
}

export function discipleshipEnrollmentsQueryKey(classId: number) {
  return ['discipleship', 'classes', classId, 'enrollments'] as const
}

export function discipleshipEnrollmentQueryKey(classId: number, enrollmentId: number) {
  return ['discipleship', 'classes', classId, 'enrollments', enrollmentId] as const
}

export function useDiscipleshipClasses() {
  return useQuery({
    queryKey: discipleshipClassesQueryKey,
    queryFn: getDiscipleshipClasses,
  })
}

export function useDiscipleshipClass(id: number) {
  return useQuery({
    queryKey: discipleshipClassQueryKey(id),
    queryFn: () => getDiscipleshipClass(id),
    enabled: Number.isFinite(id),
  })
}

export function useCreateDiscipleshipClass() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreateDiscipleshipClassInput) => createDiscipleshipClass(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: discipleshipClassesQueryKey })
    },
  })
}

export function useUpdateDiscipleshipClass(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: UpdateDiscipleshipClassInput) => updateDiscipleshipClass(id, payload),
    onSuccess: async (discipleshipClass) => {
      queryClient.setQueryData(discipleshipClassQueryKey(id), discipleshipClass)
      await queryClient.invalidateQueries({ queryKey: discipleshipClassesQueryKey })
      await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(id) })
    },
  })
}

export function useDiscipleshipClassLifecycle(id: number) {
  const queryClient = useQueryClient()

  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: discipleshipClassesQueryKey })
    await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(id) })
  }

  return {
    start: useMutation({ mutationFn: () => startDiscipleshipClass(id), onSuccess }),
    complete: useMutation({ mutationFn: () => completeDiscipleshipClass(id), onSuccess }),
    cancel: useMutation({ mutationFn: () => cancelDiscipleshipClass(id), onSuccess }),
  }
}

export function useDiscipleshipEnrollments(classId: number) {
  return useQuery({
    queryKey: discipleshipEnrollmentsQueryKey(classId),
    queryFn: () => getDiscipleshipEnrollments(classId),
    enabled: Number.isFinite(classId),
  })
}

export function useDiscipleshipEnrollment(classId: number, enrollmentId: number) {
  return useQuery({
    queryKey: discipleshipEnrollmentQueryKey(classId, enrollmentId),
    queryFn: () => getDiscipleshipEnrollment(classId, enrollmentId),
    enabled: Number.isFinite(classId) && Number.isFinite(enrollmentId),
  })
}

export function useCreateDiscipleshipEnrollment(classId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreateDiscipleshipEnrollmentInput) => createDiscipleshipEnrollment(classId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: discipleshipEnrollmentsQueryKey(classId) })
      await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(classId) })
    },
  })
}

export function useWithdrawDiscipleshipEnrollment(classId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (enrollmentId: number) => withdrawDiscipleshipEnrollment(classId, enrollmentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: discipleshipEnrollmentsQueryKey(classId) })
      await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(classId) })
    },
  })
}
