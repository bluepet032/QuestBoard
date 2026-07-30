import type { Opportunity } from './types'
import { matchesQuickTag } from './utils'

export interface OpportunityFilters {
  type: string
  quick: string
  search: string
  field: string
  status: string
}

export function matchesOpportunity(item: Opportunity, filters: OpportunityFilters) {
  if (item.is_adjacent && filters.type === 'all') return false
  if (filters.type !== 'all' && item.primary_type !== filters.type) return false
  if (filters.quick && !matchesQuickTag(item, filters.quick)) return false
  if (filters.field && !item.field_tags.includes(filters.field)) return false
  if (filters.status && item.status !== filters.status) return false

  const terms = filters.search.trim().toLocaleLowerCase('ko-KR').split(/\s+/).filter(Boolean)
  if (terms.length) {
    const haystack = [item.title, item.organizer, item.summary, item.source_name, ...item.field_tags, ...item.audience_tags]
      .join(' ')
      .toLocaleLowerCase('ko-KR')
    if (!terms.every(term => haystack.includes(term))) return false
  }
  return true
}
