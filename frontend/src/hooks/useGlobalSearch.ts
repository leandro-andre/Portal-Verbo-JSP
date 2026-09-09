import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getGlobalSearch } from '../api/globalSearch'

export const globalSearchQueryKey = ['global-search'] as const
export const GLOBAL_SEARCH_MIN_LENGTH = 2

export function useDebouncedValue<T>(value: T, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedValue(value), delay)
    return () => window.clearTimeout(timer)
  }, [delay, value])

  return debouncedValue
}

export function useGlobalSearch(query: string, enabled = true) {
  const normalizedQuery = query.trim()
  return useQuery({
    queryKey: [...globalSearchQueryKey, normalizedQuery],
    queryFn: ({ signal }) => getGlobalSearch(normalizedQuery, signal),
    enabled: enabled && normalizedQuery.length >= GLOBAL_SEARCH_MIN_LENGTH,
    staleTime: 15_000,
  })
}
