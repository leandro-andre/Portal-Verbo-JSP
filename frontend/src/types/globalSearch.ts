export type GlobalSearchGroupType = 'people' | 'users' | 'departments'

export type GlobalSearchItem = {
  id: number
  title: string
  subtitle: string
  photo_url: string | null
  url: string
}

export type GlobalSearchGroup = {
  type: GlobalSearchGroupType
  label: string
  items: GlobalSearchItem[]
}

export type GlobalSearchResponse = {
  query: string
  groups: GlobalSearchGroup[]
}
