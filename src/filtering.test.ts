import { describe, expect, it } from 'vitest'
import { matchesOpportunity, type OpportunityFilters } from './filtering'
import type { Opportunity } from './types'

const filters: OpportunityFilters = {
  type: 'all', quick: '', search: '', field: '', status: '',
}

const item = {
  id: 'sample', title: 'AI 인디게임 공모전', source_name: '테스트', source_url: 'https://example.com',
  organizer: '게임재단', summary: '대학생 개발자를 위한 공모전', primary_type: 'contest', field_tags: ['AI', '인디'],
  audience_tags: ['대학생'], status: 'open', relevance: { score: 80, reasons: [], decision: 'publish' },
  first_seen_at: '2026-01-01T00:00:00+09:00', last_seen_at: '2026-01-01T00:00:00+09:00', sources: [],
  date_kind: 'exact', location: '서울', mode: 'online', fee: 'free', is_adjacent: false,
} satisfies Opportunity

describe('matchesOpportunity', () => {
  it('combines search and basic filters', () => {
    expect(matchesOpportunity(item, { ...filters, search: '게임재단', field: 'AI' })).toBe(true)
    expect(matchesOpportunity(item, { ...filters, search: '게임재단', field: '데이터' })).toBe(false)
  })

  it('hides adjacent opportunities by default but exposes their selected type', () => {
    const adjacent = { ...item, primary_type: 'employment', is_adjacent: true } satisfies Opportunity
    expect(matchesOpportunity(adjacent, filters)).toBe(false)
    expect(matchesOpportunity(adjacent, { ...filters, type: 'employment' })).toBe(true)
  })
})
