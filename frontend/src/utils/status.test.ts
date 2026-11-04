import { describe, it, expect } from 'vitest'
import { statusTextCls, statusLabelKey } from './status'

describe('status utils', () => {
  it('maps known statuses to semantic color classes', () => {
    expect(statusTextCls('completed')).toBe('text-success')
    expect(statusTextCls('failed')).toBe('text-danger')
    expect(statusTextCls('running')).toBe('text-warning')
    expect(statusTextCls('pending')).toBe('text-muted')
    expect(statusTextCls('queued')).toBe('text-accent')
  })

  it('falls back to muted/pending for unknown statuses', () => {
    expect(statusTextCls('weird')).toBe('text-muted')
    expect(statusTextCls('')).toBe('text-muted')
    expect(statusLabelKey('weird')).toBe('statusPending')
    expect(statusLabelKey('')).toBe('statusPending')
  })

  it('returns a status* i18n key for every known status', () => {
    for (const s of ['completed', 'failed', 'running', 'pending', 'queued']) {
      expect(statusLabelKey(s)).toMatch(/^status/)
    }
  })
})
