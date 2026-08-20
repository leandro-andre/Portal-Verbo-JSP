import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  cancelDiscipleshipClass,
  completeDiscipleshipClass,
  createDiscipleshipClass,
  getDiscipleshipClass,
  getDiscipleshipClasses,
  startDiscipleshipClass,
  updateDiscipleshipClass,
} from '../api/discipleship'
import type {
  CreateDiscipleshipClassInput,
  UpdateDiscipleshipClassInput,
} from '../types/discipleship'

export const discipleshipClassesQueryKey = ['discipleship', 'classes'] as const

export function discipleshipClassQueryKey(id: number) {
  return ['discipleship', 'classes', id] as const
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
