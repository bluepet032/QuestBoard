import { useEffect, useState } from 'react'
import { loadOpportunities, loadStatuses } from '../data'
import type { CrawlStatus, Opportunity } from '../types'

export function StatusPage() {
  const [statuses, setStatuses] = useState<CrawlStatus[]>([])
  const [review, setReview] = useState<Opportunity[]>([])
  const [generated, setGenerated] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    Promise.all([loadStatuses(), loadOpportunities('review')])
      .then(([sourcePayload, reviewPayload]) => { setStatuses(sourcePayload.items); setReview(reviewPayload.items); setGenerated(sourcePayload.generated_at) })
      .catch(reason => setError(reason instanceof Error ? reason.message : '상태 데이터를 불러오지 못했습니다'))
  }, [])
  const stale = (item: CrawlStatus) => !item.last_success_at || Date.now() - Date.parse(item.last_success_at) > 24 * 60 * 60 * 1000 || item.consecutive_failures >= 3
  return (
    <main id="main-content" className="container status-page">
      <div className="page-heading"><div><p className="eyebrow">PIPELINE HEALTH</p><h1>수집 상태</h1><p>공개 수집기의 최근 실행과 수동 검토 대상을 확인합니다.</p></div></div>
      {error && <div className="message error" role="alert">{error}</div>}
      <p className="updated-at">마지막 상태 생성: {generated ? new Date(generated).toLocaleString('ko-KR') : '없음'}</p>
      <section><h2>출처별 상태</h2><div className="status-grid">{statuses.map(item => <article key={item.source_id} className={`source-card ${item.status} ${stale(item) ? 'stale' : ''}`}><div><h3>{item.source_name}</h3><span className={`status status-${item.status === 'success' && !stale(item) ? 'open' : 'urgent'}`}>{stale(item) ? '주의' : item.status === 'success' ? '정상' : '실패'}</span></div><dl><div><dt>수집</dt><dd>{item.collected_count}건</dd></div><div><dt>공개</dt><dd>{item.published_count}건</dd></div><div><dt>검토</dt><dd>{item.review_count}건</dd></div><div><dt>연속 실패</dt><dd>{item.consecutive_failures}회</dd></div></dl>{item.error && <p className="source-error">{item.error}</p>}</article>)}</div></section>
      <section className="review-section"><div className="section-heading"><div><h2>수동 검토 큐</h2><p>관련성 점수 50~69점 후보입니다. 승인·제외는 <code>manual/overrides.yml</code>과 <code>manual/exclusions.yml</code>에서 처리합니다.</p></div><strong>{review.length}건</strong></div><div className="review-list">{review.map(item => <article key={item.id}><div><a href={item.source_url} target="_blank" rel="noopener noreferrer">{item.title}</a><span>{item.source_name} · {item.organizer}</span></div><strong>{item.relevance.score}점</strong><ul>{item.relevance.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul></article>)}</div>{!review.length && <div className="message">검토 대기 공고가 없습니다.</div>}</section>
    </main>
  )
}

