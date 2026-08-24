import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  cancelWorshipService,
  createExtraordinaryWorshipService,
  createWorshipTemplate,
  deactivateWorshipTemplate,
  generateWorshipServices,
  getWorshipServices,
  getWorshipTemplates,
  reactivateWorshipService,
  reactivateWorshipTemplate,
  updateWorshipService,
  updateWorshipTemplate,
} from '../api/worship'
import type { WorshipServiceInput, WorshipTemplateInput } from '../types/worship'

export const worshipTemplatesQueryKey = ['worship', 'templates'] as const

export function worshipServicesQueryKey(year: number, month: number) {
  return ['worship', 'services', year, month] as const
}

export function useWorshipTemplates() {
  return useQuery({
    queryKey: worshipTemplatesQueryKey,
    queryFn: getWorshipTemplates,
  })
}

export function useWorshipTemplateMutations() {
  const queryClient = useQueryClient()

  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: worshipTemplatesQueryKey })
  }

  return {
    create: useMutation({ mutationFn: (payload: WorshipTemplateInput) => createWorshipTemplate(payload), onSuccess }),
    update: useMutation({
      mutationFn: ({ id, payload }: { id: number; payload: WorshipTemplateInput }) => updateWorshipTemplate(id, payload),
      onSuccess,
    }),
    deactivate: useMutation({ mutationFn: (id: number) => deactivateWorshipTemplate(id), onSuccess }),
    reactivate: useMutation({ mutationFn: (id: number) => reactivateWorshipTemplate(id), onSuccess }),
  }
}

export function useWorshipServices(year: number, month: number) {
  return useQuery({
    queryKey: worshipServicesQueryKey(year, month),
    queryFn: () => getWorshipServices(year, month),
  })
}

export function useWorshipServiceMutations(year: number, month: number) {
  const queryClient = useQueryClient()

  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: worshipServicesQueryKey(year, month) })
  }

  return {
    generate: useMutation({
      mutationFn: () => generateWorshipServices({ year, month }),
      onSuccess,
    }),
    createExtraordinary: useMutation({
      mutationFn: (payload: WorshipServiceInput) => createExtraordinaryWorshipService(payload),
      onSuccess,
    }),
    update: useMutation({
      mutationFn: ({ id, payload }: { id: number; payload: WorshipServiceInput }) => updateWorshipService(id, payload),
      onSuccess,
    }),
    cancel: useMutation({
      mutationFn: (id: number) => cancelWorshipService(id),
      onSuccess,
    }),
    reactivate: useMutation({
      mutationFn: (id: number) => reactivateWorshipService(id),
      onSuccess,
    }),
  }
}
