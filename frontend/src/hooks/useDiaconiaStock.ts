import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createAttendanceCount,
  createStockCategory,
  createCountingEnvironment,
  createStockItem,
  createStockMovement,
  deactivateStockCategory,
  deactivateCountingEnvironment,
  deactivateStockItem,
  getAttendanceCount,
  getAttendanceCounts,
  getStockCategories,
  getCountingEnvironments,
  getStockItem,
  getStockItems,
  getStockMovements,
  getStockSummary,
  getStockUnits,
  reactivateStockCategory,
  reactivateCountingEnvironment,
  reactivateStockItem,
  updateStockCategory,
  updateCountingEnvironment,
  updateAttendanceCount,
  updateStockItem,
} from '../api/diaconia'
import type {
  AttendanceCount,
  AttendanceCountFilters,
  CreateStockCategoryInput,
  CreateAttendanceCountInput,
  CreateCountingEnvironmentInput,
  CountingEnvironmentFilters,
  CreateStockItemInput,
  CreateStockMovementInput,
  StockCategory,
  StockItem,
  StockItemFilters,
  StockMovementFilters,
  UpdateStockCategoryInput,
  UpdateAttendanceCountInput,
  UpdateCountingEnvironmentInput,
  UpdateStockItemInput,
} from '../types/diaconia'

export const stockItemsQueryKey = ['diaconia', 'stock', 'items'] as const
export const stockCategoriesQueryKey = ['diaconia', 'stock', 'categories'] as const
export const stockUnitsQueryKey = ['diaconia', 'stock', 'units'] as const
export const stockMovementsQueryKey = ['diaconia', 'stock', 'movements'] as const
export const stockSummaryQueryKey = ['diaconia', 'stock', 'summary'] as const
export const countingEnvironmentsQueryKey = ['diaconia', 'counting', 'environments'] as const
export const attendanceCountsQueryKey = ['diaconia', 'counting', 'counts'] as const

export function stockItemQueryKey(id: number) {
  return ['diaconia', 'stock', 'items', id] as const
}

export function attendanceCountQueryKey(id: number) {
  return ['diaconia', 'counting', 'counts', id] as const
}

export function useStockItems(filters?: StockItemFilters) {
  return useQuery({ queryKey: filters ? [...stockItemsQueryKey, filters] : stockItemsQueryKey, queryFn: () => getStockItems(filters) })
}

export function useStockItem(id: number) {
  return useQuery({
    queryKey: stockItemQueryKey(id),
    queryFn: () => getStockItem(id),
    enabled: Number.isFinite(id),
  })
}

export function useStockCategories() {
  return useQuery({ queryKey: stockCategoriesQueryKey, queryFn: getStockCategories })
}

export function useStockUnits() {
  return useQuery({ queryKey: stockUnitsQueryKey, queryFn: getStockUnits })
}

export function useStockSummary() {
  return useQuery({ queryKey: stockSummaryQueryKey, queryFn: getStockSummary })
}

export function useCountingEnvironments(filters?: CountingEnvironmentFilters) {
  return useQuery({
    queryKey: filters ? [...countingEnvironmentsQueryKey, filters] : countingEnvironmentsQueryKey,
    queryFn: () => getCountingEnvironments(filters),
  })
}

export function useAttendanceCount(id: number) {
  return useQuery({
    queryKey: attendanceCountQueryKey(id),
    queryFn: () => getAttendanceCount(id),
    enabled: Number.isFinite(id),
  })
}

export function useAttendanceCounts(filters?: AttendanceCountFilters) {
  return useQuery({
    queryKey: filters ? [...attendanceCountsQueryKey, filters] : attendanceCountsQueryKey,
    queryFn: () => getAttendanceCounts(filters),
  })
}

export function useStockMovements(filters?: StockMovementFilters) {
  return useQuery({
    queryKey: filters ? [...stockMovementsQueryKey, filters] : stockMovementsQueryKey,
    queryFn: () => getStockMovements(filters),
  })
}

export function useCreateStockItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateStockItemInput) => createStockItem(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: stockItemsQueryKey })
    },
  })
}

export function useCreateStockMovement() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateStockMovementInput) => createStockMovement(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: stockItemsQueryKey })
      await queryClient.invalidateQueries({ queryKey: stockMovementsQueryKey })
      await queryClient.invalidateQueries({ queryKey: stockSummaryQueryKey })
    },
  })
}

export function useCreateAttendanceCount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateAttendanceCountInput) => createAttendanceCount(payload),
    onSuccess: async (attendanceCount: AttendanceCount) => {
      queryClient.setQueryData(attendanceCountQueryKey(attendanceCount.id), attendanceCount)
      await queryClient.invalidateQueries({ queryKey: attendanceCountsQueryKey })
    },
  })
}

export function useUpdateAttendanceCount(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateAttendanceCountInput) => updateAttendanceCount(id, payload),
    onSuccess: async (attendanceCount: AttendanceCount) => {
      queryClient.setQueryData(attendanceCountQueryKey(id), attendanceCount)
      await queryClient.invalidateQueries({ queryKey: attendanceCountsQueryKey })
      await queryClient.invalidateQueries({ queryKey: attendanceCountQueryKey(id) })
    },
  })
}

export function useUpdateStockItem(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateStockItemInput) => updateStockItem(id, payload),
    onSuccess: async (item) => {
      queryClient.setQueryData(stockItemQueryKey(id), item)
      await queryClient.invalidateQueries({ queryKey: stockItemsQueryKey })
      await queryClient.invalidateQueries({ queryKey: stockSummaryQueryKey })
      await queryClient.invalidateQueries({ queryKey: stockItemQueryKey(id) })
    },
  })
}

export function useStockItemLifecycle(id: number) {
  const queryClient = useQueryClient()
  const onSuccess = async (item: StockItem) => {
    queryClient.setQueryData(stockItemQueryKey(id), item)
    await queryClient.invalidateQueries({ queryKey: stockItemsQueryKey })
    await queryClient.invalidateQueries({ queryKey: stockSummaryQueryKey })
    await queryClient.invalidateQueries({ queryKey: stockItemQueryKey(id) })
  }

  return {
    deactivate: useMutation({ mutationFn: () => deactivateStockItem(id), onSuccess }),
    reactivate: useMutation({ mutationFn: () => reactivateStockItem(id), onSuccess }),
  }
}

export function useStockCategoryMutations() {
  const queryClient = useQueryClient()
  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: stockCategoriesQueryKey })
    await queryClient.invalidateQueries({ queryKey: stockItemsQueryKey })
  }

  return {
    create: useMutation({ mutationFn: (payload: CreateStockCategoryInput) => createStockCategory(payload), onSuccess }),
    update: useMutation({
      mutationFn: ({ id, payload }: { id: number; payload: UpdateStockCategoryInput }) =>
        updateStockCategory(id, payload),
      onSuccess,
    }),
    deactivate: useMutation({ mutationFn: (id: number) => deactivateStockCategory(id), onSuccess }),
    reactivate: useMutation({
      mutationFn: (id: number) => reactivateStockCategory(id),
      onSuccess: async (category: StockCategory) => {
        queryClient.setQueryData(stockCategoriesQueryKey, (current: StockCategory[] | undefined) =>
          current?.map((item) => (item.id === category.id ? category : item)),
        )
        await onSuccess()
      },
    }),
  }
}

export function useCountingEnvironmentMutations() {
  const queryClient = useQueryClient()
  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: countingEnvironmentsQueryKey })
  }

  return {
    create: useMutation({
      mutationFn: (payload: CreateCountingEnvironmentInput) => createCountingEnvironment(payload),
      onSuccess,
    }),
    update: useMutation({
      mutationFn: ({ id, payload }: { id: number; payload: UpdateCountingEnvironmentInput }) =>
        updateCountingEnvironment(id, payload),
      onSuccess,
    }),
    deactivate: useMutation({ mutationFn: (id: number) => deactivateCountingEnvironment(id), onSuccess }),
    reactivate: useMutation({ mutationFn: (id: number) => reactivateCountingEnvironment(id), onSuccess }),
  }
}
