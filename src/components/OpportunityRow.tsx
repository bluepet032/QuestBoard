import { useState } from 'react'
import { STATUS_LABELS, TYPE_LABELS } from '../constants'
import type { Opportunity, PersonalState } from '../types'
import { dDayLabel, formatDate, isIndieGameContest, isNew, isUpdated } from '../utils'

interface Props {
  item: Opportunity
  personal: PersonalState
  onToggle: (bucket: 'favorites' | 'read' | 'hidden', id: string) => void
}

export function OpportunityRow({ item, personal, onToggle }: Props) {
  const [expanded, setExpanded] = useState(false)
  const favorite = personal.favorites.includes(item.id)
  const read = personal.read.includes(item.id)
  return (
    <article className={`opportunity type-${item.primary_type} ${read ? 'is-read' : ''}`}>
      <div className="date-cell">
        <strong>{dDayLabel(item)}</strong>
        <span>{formatDate(item.recruit_start)}</span>
        <span>~ {formatDate(item.recruit_end)}</span>
      </div>
      <div className="opportunity-main">
        <div className="title-line">
          <a href={item.source_url} target="_blank" rel="noopener noreferrer" onClick={() => onToggle('read', item.id)}>{item.title}</a>
          {isIndieGameContest(item) && <span className="badge badge-indie">인디</span>}
          {isNew(item) && <span className="badge badge-new">NEW</span>}
          {isUpdated(item) && <span className="badge badge-updated">UPDATED</span>}
        </div>
        <p>{item.summary}</p>
        <div className="mobile-meta">{item.organizer} · {STATUS_LABELS[item.status]}</div>
        <div className="tags" aria-label="공고 분류">
          <span className={`badge type-badge type-${item.primary_type}`}>{TYPE_LABELS[item.primary_type]}</span>
          {[...item.field_tags, ...item.audience_tags].slice(0, 5).map(tag => <span className="badge tag" key={tag}>{tag}</span>)}
        </div>
        {expanded && (
          <div className="details">
            <dl>
              <div><dt>참가 대상</dt><dd>{item.eligibility || '원문 확인 필요'}</dd></div>
              <div><dt>혜택·지원</dt><dd>{item.benefits || '원문 확인 필요'}</dd></div>
              <div><dt>장소·방식</dt><dd>{[item.location, item.mode].filter(Boolean).join(' · ') || '원문 확인 필요'}</dd></div>
              <div><dt>출처</dt><dd>{item.sources.map(source => source.source_name).join(', ')}</dd></div>
            </dl>
            <div className="detail-links">
              <a className="button-link" href={item.source_url} target="_blank" rel="noopener noreferrer">원문 보기</a>
              {item.application_url && <a href={item.application_url} target="_blank" rel="noopener noreferrer">신청하기</a>}
              {item.document_url && <a href={item.document_url} target="_blank" rel="noopener noreferrer">첨부파일</a>}
            </div>
          </div>
        )}
      </div>
      <div className="type-cell"><span className={`badge type-badge type-${item.primary_type}`}>{TYPE_LABELS[item.primary_type]}</span></div>
      <div className="organizer-cell">{item.organizer}</div>
      <div className="state-cell">
        <span className={`status status-${item.status}`}>{STATUS_LABELS[item.status]}</span>
        <div className="row-actions">
          <button type="button" className="icon-button" aria-label={favorite ? '관심 해제' : '관심 등록'} aria-pressed={favorite} onClick={() => onToggle('favorites', item.id)}>{favorite ? '★' : '☆'}</button>
          <button type="button" className="text-button" onClick={() => setExpanded(value => !value)} aria-expanded={expanded}>{expanded ? '접기' : '펼치기'}</button>
          <button type="button" className="text-button muted" onClick={() => onToggle('hidden', item.id)}>숨김</button>
        </div>
      </div>
    </article>
  )
}

