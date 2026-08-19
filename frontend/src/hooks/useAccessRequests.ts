import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  approveAccessRequest,
  createAccessRequest,
  getAccessRequest,
  getAccessRequests,
  rejectAccessRequest,
} from '../api/accessRequests'
import type {
  AccessRequestStatus,
  ApproveAccessRequestInput,
  CreateAccessRequestInput,
  RejectAccessRequestInput,
} from '../types/accessRequest'

export const accessRequestsQueryKey = ['access-requests']

export function accessRequestQueryKey(id: number) {
  return ['access-requests', id] as const
}

export function useCreateAccessRequest() {
  return useMutation({
    mutationFn: (payload: CreateAccessRequestInput) => createAccessRequest(payload),
  })
}

export function useAccessRequests(status: AccessRequestStatus) {
  return useQuery({
    queryKey: [...accessRequestsQueryKey, status],
    queryFn: () => getAccessRequests(status),
  })
}

export function useAccessRequest(id: number) {
  return useQuery({
    queryKey: accessRequestQueryKey(id),
    queryFn: () => getAccessRequest(id),
    enabled: Number.isFinite(id),
  })
}

export function useApproveAccessRequest(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: ApproveAccessRequestInput) => approveAccessRequest(id, payload),
    onSuccess: async (accessRequest) => {
      queryClient.setQueryData(accessRequestQueryKey(id), accessRequest)
      await queryClient.invalidateQueries({ queryKey: accessRequestsQueryKey })
      await queryClient.invalidateQueries({ queryKey: accessRequestQueryKey(id) })
    },
  })
}

export function useRejectAccessRequest(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: RejectAccessRequestInput) => rejectAccessRequest(id, payload),
    onSuccess: async (accessRequest) => {
      queryClient.setQueryData(accessRequestQueryKey(id), accessRequest)
      await queryClient.invalidateQueries({ queryKey: accessRequestsQueryKey })
      await queryClient.invalidateQueries({ queryKey: accessRequestQueryKey(id) })
    },
  })
}
