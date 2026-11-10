import { describe, it, expect } from 'vitest'
import { t, tf } from '@/i18n'

describe('i18n t()', () => {
  it('returns the key itself for unknown keys', () => {
    expect(t('__nonexistent_key__')).toBe('__nonexistent_key__')
  })
  it('returns a non-empty German string for a known key', () => {
    const v = t('tabCreate')
    expect(typeof v).toBe('string')
    expect(v.length).toBeGreaterThan(0)
    expect(v).not.toBe('tabCreate')
  })
})

describe('i18n tf()', () => {
  it('interpolates named params', () => {
    // knowledgeSyncSuccess exists in de.json with {updated} and {total}
    const v = tf('knowledgeSyncSuccess', { updated: 3, total: 10 })
    expect(v).toContain('3')
    expect(v).toContain('10')
  })
  it('leaves placeholder when param missing', () => {
    const v = tf('knowledgeSyncSuccess', {})
    expect(v).toContain('{updated}')
  })
})