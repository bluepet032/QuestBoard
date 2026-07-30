import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'

const payload = { schema_version: 1, generated_at: '2026-07-30T12:00:00+09:00', items: [] }

describe('QuestBoard', () => {
  beforeEach(() => {
    localStorage.clear()
    window.location.hash = '#/'
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => payload }))
  })

  it('renders the main opportunity navigation and empty state', async () => {
    render(<App />)
    expect(screen.getByRole('link', { name: /QuestBoard/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /전체/ })).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('조건에 맞는 공고가 없습니다.')).toBeInTheDocument())
  })
})

