import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { EMPTY_ADVANCED } from '../advancedFilters'
import type { Opportunity } from '../types'
import { Filters } from './Filters'

const base = {
  id: 'a', title: '공고', source_name: '출처', source_url: 'https://example.com/a', organizer: '기관', summary: '요약',
  primary_type: 'contest', field_tags: [], audience_tags: [], status: 'open',
  relevance: { score: 80, reasons: [], decision: 'publish' }, first_seen_at: '2026-01-01T00:00:00+09:00',
  last_seen_at: '2026-01-01T00:00:00+09:00', sources: [], date_kind: 'exact',
} satisfies Opportunity

const items: Opportunity[] = [
  { ...base, id: 'seoul', regions: ['서울'], fee: 'free', audience_tags: ['대학생'], prize_manwon: 500 },
  { ...base, id: 'all', regions: ['전국'], fee: 'paid', audience_tags: ['누구나'], prize_manwon: 0 },
  { ...base, id: 'busan', regions: ['부산'], mode: 'online' },
  { ...base, id: 'unknown' },
]

const renderFilters = (advanced = EMPTY_ADVANCED, handlers = { onChange: vi.fn(), onChangeMany: vi.fn() }) => {
  render(<Filters items={items} domain="all" type="all" quick="" search="" field="" status="" advanced={advanced} {...handlers} />)
  return handlers
}

describe('advanced filter panel', () => {
  afterEach(() => cleanup())

  it('starts closed without active conditions and opens on demand', () => {
    renderFilters()
    const toggle = screen.getByRole('button', { name: /^상세 조건\s*\d*$/ })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByLabelText('지역')).toBeNull()
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByLabelText('지역')).toBeInTheDocument()
  })

  it('shows how many items each option would leave, counting nationwide and open-to-all notices', () => {
    renderFilters()
    fireEvent.click(screen.getByRole('button', { name: /^상세 조건\s*\d*$/ }))
    const region = within(screen.getByLabelText('지역'))
    expect(region.getByRole('option', { name: '서울 (2)' })).toBeInTheDocument()
    expect(region.getByRole('option', { name: '전국 공고만 (1)' })).toBeInTheDocument()
    const audience = within(screen.getByLabelText('참가 대상'))
    expect(audience.getByRole('option', { name: '대학생 (2)' })).toBeInTheDocument()
    expect(audience.getByRole('option', { name: '청소년 (1)' })).toBeInTheDocument()
    const prize = within(screen.getByLabelText('상금'))
    expect(prize.getByRole('option', { name: '상금 있음 (2)' })).toBeInTheDocument()
    expect(prize.getByRole('option', { name: '500만원 이상 (1)' })).toBeInTheDocument()
  })

  it('reports changes with the URL parameter names', () => {
    const handlers = renderFilters()
    fireEvent.click(screen.getByRole('button', { name: /^상세 조건\s*\d*$/ }))
    fireEvent.change(screen.getByLabelText('참가 대상'), { target: { value: '청소년' } })
    expect(handlers.onChange).toHaveBeenLastCalledWith('aud', '청소년')
    fireEvent.click(screen.getByRole('checkbox', { name: '정보가 없는 공고도 함께 보기' }))
    expect(handlers.onChange).toHaveBeenLastCalledWith('unknown', '1')
  })

  it('opens automatically with active conditions and resets them in one update', () => {
    const handlers = renderFilters({ ...EMPTY_ADVANCED, region: '서울', fee: 'free', includeUnknown: true })
    expect(screen.getByRole('button', { name: /^상세 조건\s*\d*$/ })).toHaveTextContent('2')
    expect(screen.getByLabelText('지역')).toHaveValue('서울')
    fireEvent.click(screen.getByRole('button', { name: '상세 조건 초기화' }))
    expect(handlers.onChangeMany).toHaveBeenCalledTimes(1)
    expect(handlers.onChangeMany).toHaveBeenCalledWith({ region: '', mode: '', fee: '', aud: '', prize: '', unknown: '' })
  })
})
