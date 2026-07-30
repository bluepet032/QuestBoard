import { describe, expect, it } from 'vitest'
import type { Opportunity } from './types'
import { isIndieGameContest } from './utils'

function opportunity(overrides: Partial<Opportunity> = {}): Opportunity {
  return {
    id: 'sample',
    title: '인디게임 공모전',
    source_name: '테스트',
    source_url: 'https://example.com',
    organizer: '게임재단',
    summary: '인디 게임 개발자를 위한 공모전',
    primary_type: 'contest',
    field_tags: ['게임', '인디'],
    audience_tags: [],
    status: 'open',
    relevance: { score: 80, reasons: [], decision: 'publish' },
    first_seen_at: '2026-07-31T00:00:00+09:00',
    last_seen_at: '2026-07-31T00:00:00+09:00',
    sources: [],
    date_kind: 'exact',
    ...overrides,
  }
}

describe('isIndieGameContest', () => {
  it('identifies indie game contests from classified tags', () => {
    expect(isIndieGameContest(opportunity())).toBe(true)
  })

  it('identifies indie game contests from their text', () => {
    expect(isIndieGameContest(opportunity({ field_tags: [], title: 'Indie Game Challenge' }))).toBe(true)
  })

  it('does not label non-contests or unrelated indie contests', () => {
    expect(isIndieGameContest(opportunity({ primary_type: 'support' }))).toBe(false)
    expect(isIndieGameContest(opportunity({ title: '인디음악 공모전', summary: '신인 음악가 모집', field_tags: ['인디', '음악'] }))).toBe(false)
  })
})
