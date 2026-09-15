import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createInventoryCount,
  createInventoryCategory,
  createInventoryItem,
  createInventoryLocation,
  deactivateInventoryCategory,
  deactivateInventoryItem,
  deactivateInventoryLocation,
  getInventoryCategories,
  getInventoryCount,
  getInventoryCountComparison,
  getInventoryCounts,
  getInventoryItem,
  getInventoryItems,
  getInventoryLocations,
  reactivateInventoryCategory,
  reactivateInventoryItem,
  reactivateInventoryLocation,
  updateInventoryCategory,
  updateInventoryCount,
  updateInventoryItem,
  updateInventoryLocation,
} from '../api/diaconiaInventory'
import type {
  CreateInventoryCategoryInput,
  CreateInventoryCountInput,
  CreateInventoryItemInput,
  CreateInventoryLocationInput,
  InventoryFilters,
  InventoryCount,
  InventoryCountFilters,
  InventoryItem,
  InventoryItemFilters,
  UpdateInventoryCategoryInput,
  UpdateInventoryCountInput,
  UpdateInventoryItemInput,
  UpdateInventoryLocationInput,
} from '../types/diaconiaInventory'

export const inventoryCategoriesQueryKey = ['diaconia', 'inventory', 'categories'] as const
export const inventoryCountsQueryKey = ['diaconia', 'inventory', 'counts'] as const
export const inventoryItemsQueryKey = ['diaconia', 'inventory', 'items'] as const
export const inventoryLocationsQueryKey = ['diaconia', 'inventory', 'locations'] as const

export function inventoryCountQueryKey(id: number) {
  return ['diaconia', 'inventory', 'counts', id] as const
}

export function inventoryItemQueryKey(id: number) {
  return ['diaconia', 'inventory', 'items', id] as const
}

export function useInventoryItems(filters?: InventoryItemFilters) {
  return useQuery({
    queryKey: filters ? [...inventoryItemsQueryKey, filters] : inventoryItemsQueryKey,
    queryFn: () => getInventoryItems(filters),
  })
}

export function useInventoryItem(id: number) {
  return useQuery({
    queryKey: inventoryItemQueryKey(id),
    queryFn: () => getInventoryItem(id),
    enabled: Number.isFinite(id),
  })
}

export function useInventoryCategories(filters?: InventoryFilters) {
  return useQuery({
    queryKey: filters ? [...inventoryCategoriesQueryKey, filters] : inventoryCategoriesQueryKey,
    queryFn: () => getInventoryCategories(filters),
  })
}

export function useInventoryLocations(filters?: InventoryFilters) {
  return useQuery({
    queryKey: filters ? [...inventoryLocationsQueryKey, filters] : inventoryLocationsQueryKey,
    queryFn: () => getInventoryLocations(filters),
  })
}

export function useInventoryCount(id: number) {
  return useQuery({
    queryKey: inventoryCountQueryKey(id),
    queryFn: () => getInventoryCount(id),
    enabled: Number.isFinite(id),
  })
}

export function useInventoryCounts(filters?: InventoryCountFilters) {
  return useQuery({
    queryKey: filters ? [...inventoryCountsQueryKey, filters] : inventoryCountsQueryKey,
    queryFn: () => getInventoryCounts(filters),
  })
}

export function useInventoryCountComparison(id: number) {
  return useQuery({
    queryKey: [...inventoryCountQueryKey(id), 'comparison'],
    queryFn: () => getInventoryCountComparison(id),
    enabled: Number.isFinite(id),
  })
}

export function useCreateInventoryCount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateInventoryCountInput) => createInventoryCount(payload),
    onSuccess: async (inventoryCount: InventoryCount) => {
      queryClient.setQueryData(inventoryCountQueryKey(inventoryCount.id), inventoryCount)
      await queryClient.invalidateQueries({ queryKey: inventoryCountsQueryKey })
    },
  })
}

export function useUpdateInventoryCount(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateInventoryCountInput) => updateInventoryCount(id, payload),
    onSuccess: async (inventoryCount: InventoryCount) => {
      queryClient.setQueryData(inventoryCountQueryKey(id), inventoryCount)
      await queryClient.invalidateQueries({ queryKey: inventoryCountsQueryKey })
      await queryClient.invalidateQueries({ queryKey: inventoryCountQueryKey(id) })
    },
  })
}

export function useInventoryCategoryMutations() {
  const queryClient = useQueryClient()
  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: inventoryCategoriesQueryKey })
  }

  return {
    create: useMutation({ mutationFn: (payload: CreateInventoryCategoryInput) => createInventoryCategory(payload), onSuccess }),
    update: useMutation({
      mutationFn: ({ id, payload }: { id: number; payload: UpdateInventoryCategoryInput }) =>
        updateInventoryCategory(id, payload),
      onSuccess,
    }),
    deactivate: useMutation({ mutationFn: (id: number) => deactivateInventoryCategory(id), onSuccess }),
    reactivate: useMutation({ mutationFn: (id: number) => reactivateInventoryCategory(id), onSuccess }),
  }
}

export function useInventoryLocationMutations() {
  const queryClient = useQueryClient()
  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: inventoryLocationsQueryKey })
  }

  return {
    create: useMutation({ mutationFn: (payload: CreateInventoryLocationInput) => createInventoryLocation(payload), onSuccess }),
    update: useMutation({
      mutationFn: ({ id, payload }: { id: number; payload: UpdateInventoryLocationInput }) =>
        updateInventoryLocation(id, payload),
      onSuccess,
    }),
    deactivate: useMutation({ mutationFn: (id: number) => deactivateInventoryLocation(id), onSuccess }),
    reactivate: useMutation({ mutationFn: (id: number) => reactivateInventoryLocation(id), onSuccess }),
  }
}

export function useCreateInventoryItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateInventoryItemInput) => createInventoryItem(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: inventoryItemsQueryKey })
    },
  })
}

export function useUpdateInventoryItem(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateInventoryItemInput) => updateInventoryItem(id, payload),
    onSuccess: async (item: InventoryItem) => {
      queryClient.setQueryData(inventoryItemQueryKey(id), item)
      await queryClient.invalidateQueries({ queryKey: inventoryItemsQueryKey })
      await queryClient.invalidateQueries({ queryKey: inventoryItemQueryKey(id) })
    },
  })
}

export function useInventoryItemLifecycle(id: number) {
  const queryClient = useQueryClient()
  const onSuccess = async (item: InventoryItem) => {
    queryClient.setQueryData(inventoryItemQueryKey(id), item)
    await queryClient.invalidateQueries({ queryKey: inventoryItemsQueryKey })
    await queryClient.invalidateQueries({ queryKey: inventoryItemQueryKey(id) })
  }

  return {
    deactivate: useMutation({ mutationFn: () => deactivateInventoryItem(id), onSuccess }),
    reactivate: useMutation({ mutationFn: () => reactivateInventoryItem(id), onSuccess }),
  }
}
