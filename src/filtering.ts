import { matchesAdvanced, type AdvancedFilters } from './advancedFilters'
import { domainOf } from './constants'
import { buildIndex, matchesSearch, searchTerms, type SearchIndex } from './search'
import type { Opportunity } from './types'
import { matchesQuickTag } from './utils'

export interface OpportunityFilters {
  domain: string
  type: string
  quick: string
  search: string
  field: string
  status: string
  /** Optional detail conditions (region, mode, fee, audience, prize). */
  advanced?: AdvancedFilters
}

// Items are immutable once loaded, so their search index is built once and reused.
const indexes = new WeakMap<Opportunity, SearchIndex>()
function indexOf(item: Opportunity) {
  let index = indexes.get(item)
  if (!index) {
    index = buildIndex([item.title, item.organizer, item.summary, item.source_name, ...item.field_tags, ...item.audience_tags])
    indexes.set(item, index)
  }
  return index
}

export function matchesOpportunity(item: Opportunity, filters: OpportunityFilters, options: { fuzzy?: boolean } = {}) {
  if (filters.domain !== 'all' && domainOf(item) !== filters.domain) return false
  if (item.is_adjacent && filters.type === 'all') return false
  if (filters.type !== 'all' && item.primary_type !== filters.type) return false
  if (filters.quick && !matchesQuickTag(item, filters.quick)) return false
  if (filters.field && !item.field_tags.includes(filters.field)) return false
  if (filters.status && item.status !== filters.status) return false
  if (filters.advanced && !matchesAdvanced(item, filters.advanced)) return false

  const terms = searchTerms(filters.search)
  return !terms.length || matchesSearch(indexOf(item), terms, options.fuzzy)
}
