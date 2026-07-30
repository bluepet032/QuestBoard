import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Filters } from '../components/Filters'
import { OpportunityRow } from '../components/OpportunityRow'
import { PAGE_SIZE } from '../constants'
import { loadOpportunities } from '../data'
import { matchesOpportunity } from '../filtering'
import { usePersonalState } from '../personal'
import type { Opportunity } from '../types'
import { isDeadlineSoon, isNew, isUpdated } from '../utils'

type Dataset = 'active' | 'undated' | 'closed'
type Sort = 'deadline' | 'newest' | 'updated' | 'relevance'

interface Props { dataset: Dataset; title: string; description: string }

export function OpportunityPage({ dataset, title, description }: Props) {
  const [payload, setPayload] = useState<{ generated: string; items: Opportunity[] }>({ generated: '', items: [] })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [params, setParams] = useSearchParams()
  const { state: personal, toggle } = usePersonalState()

  useEffect(() => {
    let active = true
    setLoading(true); setError(''); setPayload({ generated: '', items: [] })
    loadOpportunities(dataset)
      .then(data => { if (active) setPayload({ generated: data.generated_at, items: data.items }) })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : '데이터를 불러오지 못했습니다') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [dataset])

  const value = (key: string, fallback = '') => params.get(key) || fallback
  const update = (key: string, next: string) => {
    const copy = new URLSearchParams(params)
    if (next) copy.set(key, next); else copy.delete(key)
    if (key !== 'page') copy.delete('page')
    setParams(copy, { replace: true })
  }
  const filters = {
    type: value('type', 'all'), quick: value('quick'), search: value('q'), field: value('field'), status: value('status'),
    sort: value('sort', 'deadline') as Sort, page: Math.max(1, Number(value('page', '1')) || 1),
  }

  const visible = (() => {
    const hidden = new Set(personal.hidden)
    return payload.items.filter(item => {
      if (hidden.has(item.id)) return false
      return matchesOpportunity(item, filters)
    }).sort((left, right) => {
      if (filters.sort === 'newest') return Date.parse(right.first_seen_at) - Date.parse(left.first_seen_at)
      if (filters.sort === 'updated') return Date.parse(right.last_changed_at || right.last_seen_at) - Date.parse(left.last_changed_at || left.last_seen_at)
      if (filters.sort === 'relevance') return right.relevance.score - left.relevance.score
      return (left.d_day ?? 99999) - (right.d_day ?? 99999)
    })
  })()

  const totalPages = Math.max(1, Math.ceil(visible.length / PAGE_SIZE))
  const page = Math.min(filters.page, totalPages)
  const pageItems = visible.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const filterItems = payload.items.filter(item => !personal.hidden.includes(item.id))
  const freshness = payload.items.reduce((counts, item) => ({
    new: counts.new + Number(isNew(item)), updated: counts.updated + Number(isUpdated(item)), urgent: counts.urgent + Number(isDeadlineSoon(item)),
  }), { new: 0, updated: 0, urgent: 0 })

  return (
    <main id="main-content" className="container">
      <div className="page-heading">
        <div><p className="eyebrow">IT · GAME · AI OPPORTUNITIES</p><h1>{title}</h1><p>{description}</p></div>
        <div className="summary-cards" aria-label="공고 요약"><span><strong>{freshness.new}</strong> 신규</span><span><strong>{freshness.updated}</strong> 변경</span><span><strong>{freshness.urgent}</strong> 마감임박</span></div>
      </div>
      <Filters items={filterItems} {...filters} onChange={update} />
      <div className="result-toolbar">
        <p><strong>{visible.length}개</strong> 공고 · {payload.generated ? `${new Date(payload.generated).toLocaleString('ko-KR')} 갱신` : '갱신 정보 없음'}</p>
        <label>정렬 <select value={filters.sort} onChange={event => update('sort', event.target.value)}><option value="deadline">마감임박순</option><option value="newest">신규등록순</option><option value="updated">최근갱신순</option><option value="relevance">관련도순</option></select></label>
      </div>
      <div className="legend" aria-label="분류 색상 안내"><span><i className="type-support" /> 지원사업</span><span><i className="type-contest" /> 공모전</span><span><i className="type-hackathon" /> 해커톤·게임잼</span><span><b className="badge badge-new">NEW</b> 최초 수집 72시간</span><span><b className="badge badge-updated">UPDATED</b> 중요 변경 48시간</span></div>
      {loading && <div className="message" role="status">공고 데이터를 불러오는 중입니다…</div>}
      {error && <div className="message error" role="alert"><strong>데이터 로드 실패</strong><span>{error}</span><small>먼저 <code>python -m pipeline.cli</code>를 실행해 데이터를 생성하세요.</small></div>}
      {!loading && !error && pageItems.length === 0 && <div className="message"><strong>조건에 맞는 공고가 없습니다.</strong><span>필터를 줄이거나 수집 파이프라인을 실행해보세요.</span></div>}
      <section className="opportunity-list" aria-label="공고 목록">{pageItems.map(item => <OpportunityRow key={item.id} item={item} personal={personal} onToggle={toggle} />)}</section>
      {totalPages > 1 && <nav className="pagination" aria-label="페이지 이동"><button disabled={page <= 1} onClick={() => update('page', String(page - 1))}>이전</button><span>{page} / {totalPages}</span><button disabled={page >= totalPages} onClick={() => update('page', String(page + 1))}>다음</button></nav>}
      {personal.hidden.length > 0 && <button className="restore-hidden" onClick={() => personal.hidden.forEach(id => toggle('hidden', id))}>숨긴 공고 {personal.hidden.length}개 모두 복원</button>}
    </main>
  )
}
