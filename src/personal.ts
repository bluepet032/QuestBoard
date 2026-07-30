import { useCallback, useEffect, useState } from 'react'
import type { PersonalState } from './types'

const KEY = 'questboard.personal.v1'
const EMPTY: PersonalState = { version: 1, favorites: [], read: [], hidden: [] }

function load(): PersonalState {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) || '') as Partial<PersonalState>
    if (parsed.version !== 1) return EMPTY
    return {
      version: 1,
      favorites: Array.isArray(parsed.favorites) ? parsed.favorites : [],
      read: Array.isArray(parsed.read) ? parsed.read : [],
      hidden: Array.isArray(parsed.hidden) ? parsed.hidden : [],
    }
  } catch {
    return EMPTY
  }
}

export function usePersonalState() {
  const [state, setState] = useState<PersonalState>(load)
  useEffect(() => localStorage.setItem(KEY, JSON.stringify(state)), [state])
  const toggle = useCallback((bucket: 'favorites' | 'read' | 'hidden', id: string) => {
    setState(current => {
      const values = new Set(current[bucket])
      if (values.has(id)) values.delete(id); else values.add(id)
      return { ...current, [bucket]: [...values] }
    })
  }, [])
  return { state, toggle }
}

