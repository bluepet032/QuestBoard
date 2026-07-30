import { expect, test } from '@playwright/test'

const opportunity = (overrides: Record<string, unknown>) => ({
  id: 'contest-1', title: 'AI 인디게임 공모전', source_name: '테스트 출처', source_url: 'https://example.com/contest',
  organizer: '게임재단', summary: '대학생 개발팀이 AI 인디게임을 제작해 출품하는 공모전으로 자세한 참가 조건과 일정은 원문에서 확인합니다.',
  primary_type: 'contest', field_tags: ['게임', 'AI', '인디'], audience_tags: ['대학생'], status: 'open',
  relevance: { score: 90, reasons: ['테스트'], decision: 'publish' }, first_seen_at: '2026-07-30T10:00:00+09:00',
  last_seen_at: '2026-07-30T10:00:00+09:00', sources: [{ source_id: 'test', source_name: '테스트 출처', source_url: 'https://example.com/contest', kind: 'official', priority: 100 }],
  recruit_start: '2026-07-20', recruit_end: '2026-08-20', date_kind: 'exact', d_day: 21, fee: 'free', mode: 'online',
  ...overrides,
})

test('loads opportunity dashboard and changes theme', async ({ page }) => {
  await page.goto('/#/')
  await expect(page.getByRole('heading', { name: '지금 도전할 기회' })).toBeVisible()
  await page.getByLabel('화면 테마').selectOption('dark')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
})

test('status route is reachable', async ({ page }) => {
  await page.goto('/#/status')
  await expect(page.getByRole('heading', { name: '수집 상태' })).toBeVisible()
})

test('restores URL filters and personal state after reload', async ({ page }) => {
  await page.route('**/data/active.json', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({
      schema_version: 1,
      generated_at: '2026-07-30T12:00:00+09:00',
      items: [
        opportunity({}),
        opportunity({ id: 'support-1', title: '게임 스타트업 제작지원', summary: '게임 스타트업의 사업화와 콘텐츠 제작비를 지원하며 자세한 대상과 신청 절차는 원문 공고에서 확인합니다.', primary_type: 'support', source_url: 'https://example.com/support', field_tags: ['게임', '창업'], audience_tags: ['창업자·기업'] }),
      ],
    }),
  }))
  await page.goto('/#/')
  await page.getByLabel('통합 검색').fill('인디')
  await expect(page).toHaveURL(/q=%EC%9D%B8%EB%94%94/)
  await expect(page.locator('.result-toolbar strong')).toHaveText('1개')
  await expect(page.getByRole('button', { name: '지원사업 0' })).toBeVisible()
  await page.getByRole('button', { name: '관심 등록' }).click()
  await expect(page.getByRole('button', { name: '관심 해제' })).toBeVisible()

  await page.reload()

  await expect(page.getByLabel('통합 검색')).toHaveValue('인디')
  await expect(page.getByRole('button', { name: '관심 해제' })).toBeVisible()
  await expect(page).toHaveURL(/q=%EC%9D%B8%EB%94%94/)
})
