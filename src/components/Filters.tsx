import { useEffect, useRef, useState } from 'react'
import { QUICK_TAGS, TYPE_LABELS, TYPES } from '../constants'
import { matchesOpportunity, type OpportunityFilters } from '../filtering'
import type { Opportunity, OpportunityType } from '../types'

interface Props extends OpportunityFilters {
  items: Opportunity[]
  type: string
  quick: string
  search: string
  field: string
  status: string
  onChange: (key: string, value: string) => void
}

export function Filters(props: Props) {
  const [draftSearch, setDraftSearch] = useState(props.search)
  const composing = useRef(false)

  useEffect(() => {
    if (!composing.current) setDraftSearch(props.search)
  }, [props.search])

  const filterValues: OpportunityFilters = {
    type: props.type, quick: props.quick, search: props.search, field: props.field, status: props.status,
  }
  const counts = (type: OpportunityType | 'all') => props.items.filter(item => matchesOpportunity(item, { ...filterValues, type })).length
  const tagCount = (quick: string) => props.items.filter(item => matchesOpportunity(item, { ...filterValues, quick })).length
  const fields = [...new Set(props.items.flatMap(item => item.field_tags))].sort()
  return (
    <section className="filter-panel" aria-label="공고 검색과 필터">
      <div className="type-tabs" role="group" aria-label="공고 유형">
        <button className={props.type === 'all' ? 'active' : ''} onClick={() => props.onChange('type', 'all')}>전체 <span>{counts('all')}</span></button>
        {TYPES.map(type => <button key={type} className={props.type === type ? `active type-${type}` : ''} onClick={() => props.onChange('type', type)}>{TYPE_LABELS[type]} <span>{counts(type)}</span></button>)}
      </div>
      <div className="quick-tags" role="group" aria-label="빠른 필터">
        {QUICK_TAGS.map(tag => <button key={tag} className={props.quick === tag ? 'active' : ''} onClick={() => props.onChange('quick', props.quick === tag ? '' : tag)}>{tag} <span>{tagCount(tag)}</span></button>)}
      </div>
      <div className="search-row">
        <label className="search-box"><span className="sr-only">통합 검색</span><input
          value={draftSearch}
          onCompositionStart={() => { composing.current = true }}
          onCompositionEnd={event => {
            composing.current = false
            setDraftSearch(event.currentTarget.value)
            props.onChange('q', event.currentTarget.value)
          }}
          onChange={event => {
            setDraftSearch(event.target.value)
            if (!composing.current) props.onChange('q', event.target.value)
          }}
          placeholder="공고명, 기관, 요약, 태그 검색"
        /></label>
        <select value={props.field} onChange={event => props.onChange('field', event.target.value)} aria-label="기술 분야"><option value="">모든 분야</option>{fields.map(field => <option key={field}>{field}</option>)}</select>
        <select value={props.status} onChange={event => props.onChange('status', event.target.value)} aria-label="접수 상태"><option value="">모든 상태</option><option value="upcoming">접수예정</option><option value="open">접수중</option><option value="urgent">긴급</option><option value="today">오늘마감</option><option value="ongoing">상시모집</option><option value="closed">마감</option><option value="unknown">날짜 미상</option></select>
      </div>
    </section>
  )
}
