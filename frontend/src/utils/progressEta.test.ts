import { describe, expect, it } from 'vitest'
import { estimateEta, formatDuration, parseLocalStamp } from './progressEta'

describe('parseLocalStamp', () => {
  it('parses ISO datetime as local time', () => {
    const d = parseLocalStamp('2026-10-30T14:22:05')
    expect(d?.getFullYear()).toBe(2026)
    expect(d?.getMonth()).toBe(9) // Oktober (0-basiert)
    expect(d?.getDate()).toBe(30)
    expect(d?.getHours()).toBe(14)
    expect(d?.getMinutes()).toBe(22)
  })

  it('accepts a bare date and defaults time to midnight', () => {
    const d = parseLocalStamp('2026-10-30')
    expect(d?.getHours()).toBe(0)
    expect(d?.getMinutes()).toBe(0)
  })

  it('returns null for empty or garbage input', () => {
    expect(parseLocalStamp('')).toBeNull()
    expect(parseLocalStamp('not-a-date')).toBeNull()
    expect(parseLocalStamp('30.10.2026')).toBeNull()
  })
})

describe('estimateEta', () => {
  const start = '2026-10-30T10:00:00'
  const at = (minutes: number) => new Date(2026, 9, 30, 10, minutes, 0)

  it('extrapolates linearly from elapsed time and progress', () => {
    // 10 min für 25 % → 40 min gesamt → 30 min übrig
    const eta = estimateEta(25, start, at(10))
    expect(eta.state).toBe('estimating')
    expect(eta.elapsedSec).toBe(600)
    expect(eta.remainingSec).toBe(1800)
  })

  it('reports done at 100 %', () => {
    expect(estimateEta(100, start, at(10)).state).toBe('done')
  })

  it('refuses to extrapolate at very low progress', () => {
    const eta = estimateEta(1, start, at(10))
    expect(eta.state).toBe('insufficient')
    expect(eta.remainingSec).toBeNull()
  })

  it('reports insufficient when created_at is missing (legacy task)', () => {
    const eta = estimateEta(50, '', at(10))
    expect(eta.state).toBe('insufficient')
    expect(eta.elapsedSec).toBeNull()
  })

  it('reports insufficient when created_at is in the future (clock skew)', () => {
    const eta = estimateEta(50, '2026-10-30T11:00:00', at(10))
    expect(eta.state).toBe('insufficient')
  })

  it('rejects absurd extrapolations beyond 24 h', () => {
    // 2 % nach 23 h → lineare Hochrechnung wäre ~47 Tage
    const eta = estimateEta(4, '2026-10-29T11:00:00', at(0))
    expect(eta.state).toBe('insufficient')
    expect(eta.remainingSec).toBeNull()
  })
})

describe('formatDuration', () => {
  it('formats minutes, hours and sub-minute values', () => {
    expect(formatDuration(30)).toBe('< 1 min')
    expect(formatDuration(600)).toBe('10 min')
    expect(formatDuration(3600)).toBe('1 h')
    expect(formatDuration(3900)).toBe('1 h 05 min')
  })
})
