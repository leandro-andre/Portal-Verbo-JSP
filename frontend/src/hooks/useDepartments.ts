import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createDepartment,
  deactivateDepartment,
  getDepartment,
  getDepartments,
  reactivateDepartment,
  updateDepartment,
} from '../api/departments'
import type { CreateDepartmentInput, Department, UpdateDepartmentInput } from '../types/department'

export const departmentsQueryKey = ['departments'] as const

export function departmentQueryKey(id: number) {
  return ['departments', id] as const
}

export function useDepartments() {
  return useQuery({
    queryKey: departmentsQueryKey,
    queryFn: getDepartments,
  })
}

export function useDepartment(id: number) {
  return useQuery({
    queryKey: departmentQueryKey(id),
    queryFn: () => getDepartment(id),
    enabled: Number.isFinite(id),
  })
}

export function useCreateDepartment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreateDepartmentInput) => createDepartment(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: departmentsQueryKey })
    },
  })
}

export function useUpdateDepartment(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: UpdateDepartmentInput) => updateDepartment(id, payload),
    onSuccess: async (department) => {
      queryClient.setQueryData(departmentQueryKey(id), department)
      await queryClient.invalidateQueries({ queryKey: departmentsQueryKey })
      await queryClient.invalidateQueries({ queryKey: departmentQueryKey(id) })
    },
  })
}

export function useDepartmentLifecycle(id: number) {
  const queryClient = useQueryClient()

  const onSuccess = async (department: Department) => {
    queryClient.setQueryData(departmentQueryKey(id), department)
    await queryClient.invalidateQueries({ queryKey: departmentsQueryKey })
    await queryClient.invalidateQueries({ queryKey: departmentQueryKey(id) })
  }

  return {
    deactivate: useMutation({ mutationFn: () => deactivateDepartment(id), onSuccess }),
    reactivate: useMutation({ mutationFn: () => reactivateDepartment(id), onSuccess }),
  }
}
