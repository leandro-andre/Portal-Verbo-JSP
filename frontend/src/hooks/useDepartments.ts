import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createDepartment,
  createDepartmentMembership,
  createDepartmentRole,
  deactivateDepartment,
  deactivateDepartmentMembership,
  deactivateDepartmentRole,
  getDepartment,
  getDepartmentEligiblePeople,
  getDepartmentMemberships,
  getDepartmentRoles,
  getDepartments,
  reactivateDepartment,
  reactivateDepartmentMembership,
  reactivateDepartmentRole,
  updateDepartment,
  updateDepartmentMembership,
  updateDepartmentRole,
} from '../api/departments'
import type {
  CreateDepartmentInput,
  CreateDepartmentMembershipInput,
  CreateDepartmentRoleInput,
  Department,
  UpdateDepartmentInput,
  UpdateDepartmentMembershipInput,
  UpdateDepartmentRoleInput,
} from '../types/department'

export const departmentsQueryKey = ['departments'] as const

export function departmentQueryKey(id: number) {
  return ['departments', id] as const
}

export function departmentRolesQueryKey(id: number) {
  return ['departments', id, 'roles'] as const
}

export function departmentMembershipsQueryKey(id: number) {
  return ['departments', id, 'members'] as const
}

export function departmentEligiblePeopleQueryKey(id: number) {
  return ['departments', id, 'eligible-people'] as const
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

export function useDepartmentRoles(id: number, enabled = true) {
  return useQuery({
    queryKey: departmentRolesQueryKey(id),
    queryFn: () => getDepartmentRoles(id),
    enabled: enabled && Number.isFinite(id),
  })
}

export function useDepartmentMemberships(id: number, enabled = true) {
  return useQuery({
    queryKey: departmentMembershipsQueryKey(id),
    queryFn: () => getDepartmentMemberships(id),
    enabled: enabled && Number.isFinite(id),
  })
}

export function useDepartmentEligiblePeople(id: number, enabled = true) {
  return useQuery({
    queryKey: departmentEligiblePeopleQueryKey(id),
    queryFn: () => getDepartmentEligiblePeople(id),
    enabled: enabled && Number.isFinite(id),
  })
}

export function useDepartmentRoleMutations(id: number) {
  const queryClient = useQueryClient()

  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: departmentRolesQueryKey(id) })
    await queryClient.invalidateQueries({ queryKey: departmentQueryKey(id) })
  }

  return {
    create: useMutation({
      mutationFn: (payload: CreateDepartmentRoleInput) => createDepartmentRole(id, payload),
      onSuccess,
    }),
    update: useMutation({
      mutationFn: ({ roleId, payload }: { roleId: number; payload: UpdateDepartmentRoleInput }) =>
        updateDepartmentRole(id, roleId, payload),
      onSuccess,
    }),
    deactivate: useMutation({
      mutationFn: (roleId: number) => deactivateDepartmentRole(id, roleId),
      onSuccess,
    }),
    reactivate: useMutation({
      mutationFn: (roleId: number) => reactivateDepartmentRole(id, roleId),
      onSuccess,
    }),
  }
}

export function useDepartmentMembershipMutations(id: number) {
  const queryClient = useQueryClient()

  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: departmentMembershipsQueryKey(id) })
    await queryClient.invalidateQueries({ queryKey: departmentEligiblePeopleQueryKey(id) })
    await queryClient.invalidateQueries({ queryKey: departmentRolesQueryKey(id) })
    await queryClient.invalidateQueries({ queryKey: departmentQueryKey(id) })
  }

  return {
    create: useMutation({
      mutationFn: (payload: CreateDepartmentMembershipInput) => createDepartmentMembership(id, payload),
      onSuccess,
    }),
    update: useMutation({
      mutationFn: ({ membershipId, payload }: { membershipId: number; payload: UpdateDepartmentMembershipInput }) =>
        updateDepartmentMembership(id, membershipId, payload),
      onSuccess,
    }),
    deactivate: useMutation({
      mutationFn: (membershipId: number) => deactivateDepartmentMembership(id, membershipId),
      onSuccess,
    }),
    reactivate: useMutation({
      mutationFn: (membershipId: number) => reactivateDepartmentMembership(id, membershipId),
      onSuccess,
    }),
  }
}
