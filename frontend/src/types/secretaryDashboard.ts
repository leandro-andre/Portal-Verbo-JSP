export type SecretaryDashboardPerson = {
  id: number
  display_name: string
  full_name: string
  email: string
  phone: string
  profile_url: string
  edit_url: string
}

export type SecretaryDashboardPreview<T> = {
  count: number
  items: T[]
  list_url: string
}

export type SecretaryAccessRequestItem = {
  id: number
  full_name: string
  email: string
  phone: string
  created_at: string | null
  review_url: string
}

export type SecretaryMembershipApprovalItem = {
  person: SecretaryDashboardPerson
  completed_at: string | null
  detail: string
  resolution_url: string
}

export type SecretaryActivationItem = {
  user: {
    id: number
    username: string
    email: string
    detail_url: string
  }
  person: SecretaryDashboardPerson | null
  date_joined: string | null
  resolution_url: string
}

export type SecretaryIncompleteProfileItem = {
  person: SecretaryDashboardPerson
  missing: Array<'MISSING_EMAIL' | 'MISSING_WHATSAPP'>
  resolution_url: string
}

export type SecretaryDepartmentEligibilityItem = {
  id: number
  person: SecretaryDashboardPerson
  department: {
    id: number
    name: string
    code: string
  }
  role: {
    id: number
    name: string
    code: string
  }
  status: 'ACTIVE'
  reasons: Array<{
    code: string
    message: string
  }>
  resolution_url: string
}

export type SecretaryWithoutJourneyItem = {
  person: SecretaryDashboardPerson
  created_at: string | null
  resolution_url: string
}

export type SecretaryWithoutPortalAccessItem = {
  person: SecretaryDashboardPerson
  resolution_url: string
}

export type SecretaryInactiveMembershipItem = {
  person: SecretaryDashboardPerson
  member_since: string | null
  resolution_url: string
}

export type SecretaryDashboardResponse = {
  summary: {
    action_required: number
    pending_activation: number
    incomplete_profiles: number
    people_total: number
  }
  action_required: {
    access_requests: SecretaryDashboardPreview<SecretaryAccessRequestItem>
    membership_approvals: SecretaryDashboardPreview<SecretaryMembershipApprovalItem>
  }
  pending: {
    activation: SecretaryDashboardPreview<SecretaryActivationItem>
    incomplete_profiles: SecretaryDashboardPreview<SecretaryIncompleteProfileItem> & {
      missing_email_count: number
      missing_whatsapp_count: number
    }
    department_eligibility: SecretaryDashboardPreview<SecretaryDepartmentEligibilityItem>
    without_journey: SecretaryDashboardPreview<SecretaryWithoutJourneyItem>
  }
  monitoring: {
    without_portal_access: SecretaryDashboardPreview<SecretaryWithoutPortalAccessItem>
    inactive_memberships: SecretaryDashboardPreview<SecretaryInactiveMembershipItem>
  }
  overview: {
    people_total: number
    visitors: number
    active_members: number
    inactive_members: number
    active_portal_accounts: number
    pending_activation_accounts: number
    generated_at: string | null
  }
  meta: {
    preview_limit: number
    action_required_semantics: 'items'
  }
}
