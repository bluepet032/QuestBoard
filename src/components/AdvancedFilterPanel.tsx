import { useId, useState } from 'react'
import {
  activeAdvancedCount, ADVANCED_PARAMS, AUDIENCE_OPTIONS, FEE_OPTIONS, MODE_OPTIONS, NATIONWIDE, PRIZE_OPTIONS, REGION_OPTIONS,
  type AdvancedFilters, type AdvancedKey,
} from '../advancedFilters'

interface Props {
  advanced: AdvancedFilters
  /** Number of items that would remain with ``key`` set to ``value`` and every other filter unchanged. */
  countWith: (key: AdvancedKey, value: string) => number
  onChange: (param: string, value: string) => void
  /** Apply several URL changes at once; sequential single updates would each start from stale params. */
  onChangeMany: (changes: Record<string, string>) => void
}

const FIELDS: { key: AdvancedKey; label: string; empty: string; options: [string, string][]; hint?: string }[] = [
  { key: 'audience', label: '참가 대상', empty: '모든 대상', options: AUDIENCE_OPTIONS.map(value => [value, value]), hint: '대상 제한이 없는 공고도 함께 보여 줍니다.' },
  { key: 'region', label: '지역', empty: '모든 지역', options: [[NATIONWIDE, '전국 공고만'], ...REGION_OPTIONS.map((value): [string, string] => [value, value])], hint: '지역을 고르면 전국 공고도 함께 보여 줍니다.' },
  { key: 'mode', label: '진행 방식', empty: '모든 방식', options: Object.entries(MODE_OPTIONS), hint: '온·오프라인 병행은 양쪽 모두에 나옵니다.' },
  { key: 'fee', label: '참가비', empty: '모든 참가비', options: Object.entries(FEE_OPTIONS) },
  { key: 'prize', label: '상금', empty: '상금 조건 없음', options: Object.entries(PRIZE_OPTIONS) },
]

export function AdvancedFilterPanel({ advanced, countWith, onChange, onChangeMany }: Props) {
  const active = activeAdvancedCount(advanced)
  const [open, setOpen] = useState(active > 0)
  const panelId = useId()
  const reset = () => onChangeMany(Object.fromEntries([...Object.values(ADVANCED_PARAMS), 'unknown'].map(param => [param, ''])))

  return (
    <div className="advanced-filters">
      <div className="advanced-toggle-row">
        <button type="button" className={`advanced-toggle ${active ? 'has-active' : ''}`} aria-expanded={open} aria-controls={panelId} onClick={() => setOpen(value => !value)}>
          상세 조건{active > 0 && <span className="advanced-count">{active}</span>}
          <span aria-hidden="true">{open ? '▴' : '▾'}</span>
        </button>
        {active > 0 && <button type="button" className="text-button" onClick={reset}>상세 조건 초기화</button>}
      </div>
      {open && (
        <div className="advanced-panel" id={panelId}>
          {FIELDS.map(field => (
            <label key={field.key} className="advanced-field">
              <span>{field.label}</span>
              <select aria-label={field.label} value={advanced[field.key]} onChange={event => onChange(ADVANCED_PARAMS[field.key], event.target.value)}>
                <option value="">{field.empty}</option>
                {field.options.map(([value, text]) => <option key={value} value={value}>{`${text} (${countWith(field.key, value)})`}</option>)}
              </select>
              {field.hint && <small>{field.hint}</small>}
            </label>
          ))}
          <label className="advanced-unknown">
            <input type="checkbox" checked={advanced.includeUnknown} onChange={event => onChange('unknown', event.target.checked ? '1' : '')} />
            <span>정보가 없는 공고도 함께 보기</span>
          </label>
        </div>
      )}
    </div>
  )
}
