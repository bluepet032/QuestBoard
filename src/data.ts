import type { CrawlStatus, DataPayload, Opportunity } from './types'

const dataUrl = (name: string) => `${import.meta.env.BASE_URL}data/${name}.json`

async function loadPayload<T>(name: string): Promise<DataPayload<T>> {
  const response = await fetch(dataUrl(name))
  if (!response.ok) throw new Error(`${name} 데이터를 불러오지 못했습니다 (${response.status})`)
  const payload = await response.json() as DataPayload<T>
  if (payload.schema_version !== 1 || !Array.isArray(payload.items)) throw new Error(`${name} 데이터 형식이 올바르지 않습니다`)
  return payload
}

export const loadOpportunities = (name: 'active' | 'undated' | 'closed' | 'review') => loadPayload<Opportunity>(name)
export const loadStatuses = () => loadPayload<CrawlStatus>('sources')

