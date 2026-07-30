import type { OpportunityStatus, OpportunityType } from './types'

export const TYPE_LABELS: Record<OpportunityType, string> = {
  contest: '공모전', support: '지원사업', hackathon: '해커톤·게임잼', event: '행사·네트워킹',
  education: '교육·프로그램', supporters: '서포터즈', employment: '채용·인턴', other: '기타',
}

export const STATUS_LABELS: Record<OpportunityStatus, string> = {
  upcoming: '접수예정', open: '접수중', urgent: '긴급', today: '오늘마감', closed: '마감', ongoing: '상시모집', unknown: '날짜 미상',
}

export const TYPES = Object.keys(TYPE_LABELS) as OpportunityType[]
export const QUICK_TAGS = ['대학생', '인디', 'AI', 'NEW', 'UPDATED', '마감임박'] as const
export const PAGE_SIZE = 50

