export type WorshipWeekday = 0 | 1 | 2 | 3 | 4 | 5 | 6
export type WorshipServiceStatus = 'SCHEDULED' | 'CANCELLED'
export type WorshipServiceKind = 'REGULAR' | 'EXTRAORDINARY'

export type WorshipServiceTemplate = {
  id: number
  name: string
  weekday: WorshipWeekday
  weekday_label: string
  time: string
  active: boolean
  created_at: string
  updated_at: string
}

export type WorshipServiceTemplateSummary = {
  id: number
  name: string
  weekday: WorshipWeekday
  weekday_label: string
  time: string
  active: boolean
}

export type WorshipService = {
  id: number
  template: WorshipServiceTemplateSummary | null
  name: string
  date: string
  source_date: string | null
  time: string
  status: WorshipServiceStatus
  status_label: string
  kind: WorshipServiceKind
  kind_label: string
  notes: string
  created_at: string
  updated_at: string
}

export type WorshipTemplateInput = {
  name: string
  weekday: WorshipWeekday
  time: string
}

export type WorshipServiceInput = {
  name: string
  date: string
  time: string
  notes?: string
}

export type GenerateWorshipServicesInput = {
  year: number
  month: number
}

export type GenerateWorshipServicesResult = {
  created_count: number
  existing_count: number
}
