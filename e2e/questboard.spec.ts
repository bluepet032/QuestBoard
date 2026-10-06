import { expect, test } from '@playwright/test'

// KST dates relative to today so the fixture never ages into the closed list.
const isoDay = (offset: number) => new Date(Date.now() + 9 * 3_600_000 + offset * 86_400_000).toISOString().slice(0, 10)

const opportunity = (overrides: Record<string, unknown>) => ({
  id: 'contest-1', title: 'AI 인디게임 공모전', source_name: '테스트 출처', source_url: 'https://example.com/contest',
  organizer: '게임재단', summary: '대학생 개발팀이 AI 인디게임을 제작해 출품하는 공모전으로 자세한 참가 조건과 일정은 원문에서 확인합니다.',
  primary_type: 'contest', field_tags: ['게임', 'AI', '인디'], audience_tags: ['대학생'], status: 'open',
  relevance: { score: 90, reasons: ['테스트'], decision: 'publish' }, first_seen_at: '2026-07-30T10:00:00+09:00',
  last_seen_at: '2026-07-30T10:00:00+09:00', sources: [{ source_id: 'test', source_name: '테스트 출처', source_url: 'https://example.com/contest', kind: 'official', priority: 100 }],
  recruit_start: isoDay(-10), recruit_end: isoDay(21), date_kind: 'exact', d_day: 21, fee: 'free', mode: 'online',
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
  await expect(page.getByRole('link', { name: 'GitHub에서 지금 수집 실행' })).toHaveAttribute('href', /actions\/workflows\/collect\.yml$/)
  await expect(page.getByRole('button', { name: '최신 데이터 다시 불러오기' })).toBeEnabled()
  await expect(page.locator('details.review-section')).not.toHaveAttribute('open', '')
})

test('requires login for favorites and restores URL and hidden state after reload', async ({ page }) => {
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
  await expect(page.getByRole('dialog', { name: 'QuestBoard 계정' })).toBeVisible()
  await page.getByRole('button', { name: '닫기' }).click()
  await page.getByRole('button', { name: '숨김' }).click()
  await expect(page.getByRole('button', { name: '숨긴 공고 1개 모두 복원' })).toBeVisible()

  await page.reload()

  await expect(page.getByLabel('통합 검색')).toHaveValue('인디')
  await expect(page.getByRole('button', { name: '숨긴 공고 1개 모두 복원' })).toBeVisible()
  await page.getByRole('button', { name: '숨긴 공고 1개 모두 복원' }).click()
  await expect(page.getByRole('button', { name: '관심 등록' })).toBeVisible()
  await expect(page).toHaveURL(/q=%EC%9D%B8%EB%94%94/)
})

test('hides items whose deadline passed after the last collection', async ({ page }) => {
  await page.route('**/data/active.json', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({
      schema_version: 1,
      generated_at: '2026-07-30T12:00:00+09:00',
      items: [
        opportunity({}),
        opportunity({ id: 'stale-1', title: '이미 마감된 게임 공모전', source_url: 'https://example.com/stale', recruit_end: isoDay(-2), d_day: 5 }),
      ],
    }),
  }))
  await page.goto('/#/')
  await expect(page.locator('.result-toolbar strong')).toHaveText('1개')
  await expect(page.getByText('이미 마감된 게임 공모전')).toHaveCount(0)
  await expect(page.locator('.opportunity').first()).toContainText('D-21')
})
