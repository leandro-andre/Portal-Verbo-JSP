import { useEffect, useMemo, useRef, useState, type ChangeEvent, type KeyboardEvent as ReactKeyboardEvent } from 'react'
import { AlertCircle, Building2, LoaderCircle, Search, UserCog, UserRound, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { GLOBAL_SEARCH_MIN_LENGTH, useDebouncedValue, useGlobalSearch } from '../../hooks/useGlobalSearch'
import type { GlobalSearchGroup, GlobalSearchGroupType, GlobalSearchItem } from '../../types/globalSearch'

const groupIcons: Record<GlobalSearchGroupType, typeof UserRound> = {
  people: UserRound,
  users: UserCog,
  departments: Building2,
}

const emptyGroups: GlobalSearchGroup[] = []

function GlobalSearchResults({
  groups,
  isError,
  isLoading,
  flatItems,
  normalizedQuery,
  onNavigate,
  selectedIndex,
}: {
  groups: GlobalSearchGroup[]
  isError: boolean
  isLoading: boolean
  flatItems: GlobalSearchItem[]
  normalizedQuery: string
  onNavigate: (item: GlobalSearchItem) => void
  selectedIndex: number
}) {
  const hasResults = groups.some((group) => group.items.length > 0)

  if (normalizedQuery.length < GLOBAL_SEARCH_MIN_LENGTH) {
    return <p className="global-search__state">Digite ao menos 2 caracteres.</p>
  }

  if (isLoading) {
    return (
      <p className="global-search__state global-search__state--inline">
        <LoaderCircle size={16} aria-hidden="true" />
        Buscando...
      </p>
    )
  }

  if (isError) {
    return (
      <p className="global-search__state global-search__state--inline">
        <AlertCircle size={16} aria-hidden="true" />
        Nao foi possivel buscar agora.
      </p>
    )
  }

  if (!hasResults) {
    return <p className="global-search__state">Nenhum resultado para "{normalizedQuery}".</p>
  }

  return (
    <div className="global-search__groups" role="listbox" aria-label="Resultados da busca global">
      {groups.map((group) => (
        group.items.length > 0 ? (
          <section className="global-search__group" key={group.type}>
            <h2>{group.label}</h2>
            <div className="global-search__items">
              {group.items.map((item) => {
                const index = flatItems.findIndex((candidate) => candidate === item)
                const Icon = groupIcons[group.type]
                const isSelected = index === selectedIndex
                return (
                  <button
                    className={`global-search__result${isSelected ? ' global-search__result--selected' : ''}`}
                    id={`global-search-result-${index}`}
                    key={`${group.type}-${item.id}`}
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => onNavigate(item)}
                  >
                    <span className="global-search__avatar" aria-hidden="true">
                      {item.photo_url ? <img src={item.photo_url} alt="" /> : <Icon size={17} />}
                    </span>
                    <span className="global-search__copy">
                      <strong>{item.title}</strong>
                      <small>{item.subtitle}</small>
                    </span>
                  </button>
                )
              })}
            </div>
          </section>
        ) : null
      ))}
    </div>
  )
}

function GlobalSearch() {
  const [query, setQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const debouncedQuery = useDebouncedValue(query, 300)
  const normalizedQuery = query.trim()
  const debouncedNormalizedQuery = debouncedQuery.trim()
  const rootRef = useRef<HTMLDivElement>(null)
  const mobileInputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const searchQuery = useGlobalSearch(debouncedNormalizedQuery, isOpen || isMobileOpen)
  const groups = searchQuery.data?.groups ?? emptyGroups
  const flatItems = useMemo(
    () => groups.flatMap((group) => group.items),
    [groups],
  )
  const safeSelectedIndex = flatItems[selectedIndex] ? selectedIndex : 0
  const activeDescendant = flatItems[safeSelectedIndex] ? `global-search-result-${safeSelectedIndex}` : undefined

  useEffect(() => {
    if (!isOpen && !isMobileOpen) {
      return
    }

    const handleMouseDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setIsOpen(false)
        setIsMobileOpen(false)
      }
    }
    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
        setIsMobileOpen(false)
      }
    }

    document.addEventListener('mousedown', handleMouseDown)
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handleMouseDown)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, isMobileOpen])

  useEffect(() => {
    if (!isMobileOpen) {
      return
    }
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const timer = window.setTimeout(() => mobileInputRef.current?.focus(), 0)
    return () => {
      window.clearTimeout(timer)
      document.body.style.overflow = previousOverflow
    }
  }, [isMobileOpen])

  const handleNavigate = (item: GlobalSearchItem) => {
    navigate(item.url)
    setIsOpen(false)
    setIsMobileOpen(false)
    setQuery('')
  }

  const handleInputKeyDown = (event: ReactKeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Escape') {
      setIsOpen(false)
      setIsMobileOpen(false)
      return
    }

    if (event.key === 'ArrowDown' && flatItems.length > 0) {
      event.preventDefault()
      setSelectedIndex((current) => Math.min(current + 1, flatItems.length - 1))
      return
    }

    if (event.key === 'ArrowUp' && flatItems.length > 0) {
      event.preventDefault()
      setSelectedIndex((current) => Math.max(current - 1, 0))
      return
    }

    if (event.key === 'Enter' && flatItems[safeSelectedIndex]) {
      event.preventDefault()
      handleNavigate(flatItems[safeSelectedIndex])
    }
  }

  const inputProps = {
    type: 'search',
    value: query,
    onChange: (event: ChangeEvent<HTMLInputElement>) => {
      setQuery(event.target.value)
      setSelectedIndex(0)
      if (!isMobileOpen) {
        setIsOpen(true)
      }
    },
    onFocus: () => {
      if (!isMobileOpen) {
        setIsOpen(true)
      }
    },
    onKeyDown: handleInputKeyDown,
    role: 'combobox',
    'aria-expanded': isOpen || isMobileOpen,
    'aria-controls': 'global-search-results',
    'aria-activedescendant': activeDescendant,
  }

  return (
    <div className="global-search" ref={rootRef}>
      <label className="global-search__desktop">
        <span className="sr-only">Buscar no Portal</span>
        <Search size={17} aria-hidden="true" />
        <input
          {...inputProps}
          aria-label="Buscar no Portal"
          placeholder="Buscar no Portal..."
        />
      </label>

      <button
        className="icon-button global-search__mobile-button"
        type="button"
        aria-label="Buscar no Portal"
        aria-expanded={isMobileOpen}
        onClick={() => {
          setIsOpen(false)
          setIsMobileOpen(true)
        }}
      >
        <Search size={18} aria-hidden="true" />
      </button>

      {isOpen ? (
        <div className="global-search__popover" id="global-search-results">
          <GlobalSearchResults
            groups={groups}
            flatItems={flatItems}
            isError={searchQuery.isError}
            isLoading={searchQuery.isFetching && debouncedNormalizedQuery.length >= GLOBAL_SEARCH_MIN_LENGTH}
            normalizedQuery={normalizedQuery}
            onNavigate={handleNavigate}
            selectedIndex={safeSelectedIndex}
          />
        </div>
      ) : null}

      {isMobileOpen ? (
        <div className="global-search__mobile-overlay" role="dialog" aria-modal="true" aria-label="Busca global">
          <div className="global-search__mobile-panel">
            <div className="global-search__mobile-field">
              <Search size={18} aria-hidden="true" />
              <input
                {...inputProps}
                ref={mobileInputRef}
                aria-label="Buscar no Portal"
                aria-controls="global-search-results-mobile"
                placeholder="Buscar no Portal..."
              />
              <button
                className="icon-button"
                type="button"
                aria-label="Fechar busca"
                onClick={() => setIsMobileOpen(false)}
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>
            <div className="global-search__mobile-results" id="global-search-results-mobile">
              <GlobalSearchResults
                groups={groups}
                flatItems={flatItems}
                isError={searchQuery.isError}
                isLoading={searchQuery.isFetching && debouncedNormalizedQuery.length >= GLOBAL_SEARCH_MIN_LENGTH}
                normalizedQuery={normalizedQuery}
                onNavigate={handleNavigate}
                selectedIndex={safeSelectedIndex}
              />
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default GlobalSearch
