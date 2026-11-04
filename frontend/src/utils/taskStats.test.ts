import { describe, expect, it } from 'vitest'
import { computeActivity, computeTaskStats, computeTypeSlices } from './taskStats'
import type { TaskListItem } from '@/types'

function task(overrides: Partial<TaskListItem>): TaskListItem {
  return { task_id: 't', ...overrides } as TaskListItem
}

describe('computeTaskStats', () => {
  it('counts statuses and derives success rate from finished tasks only', () => {
    const stats = computeTaskStats([
      task({ status: 'completed' }),
      task({ status: 'completed' }),
      task({ status: 'completed' }),
      task({ status: 'failed' }),
      task({ status: 'running' }),
      task({ status: 'queued' }),
      task({ status: 'pending' }),
    ])
    expect(stats.total).toBe(7)
    expect(stats.counts.completed).toBe(3)
    expect(stats.counts.failed).toBe(1)
    expect(stats.finished).toBe(4)
    // 3 完成 / 4 已结束 = 75%；running/pending 不进分母
    expect(stats.successRate).toBe(75)
    expect(stats.activeNow).toBe(2)
  })

  it('returns null success rate when nothing has finished yet', () => {
    const stats = computeTaskStats([task({ status: 'running' })])
    expect(stats.successRate).toBeNull()
    expect(stats.activeNow).toBe(1)
  })

  it('treats a missing status as pending', () => {
    const stats = computeTaskStats([task({})])
    expect(stats.counts.pending).toBe(1)
  })

  it('handles an empty list', () => {
    const stats = computeTaskStats([])
    expect(stats.total).toBe(0)
    expect(stats.successRate).toBeNull()
  })
})

describe('computeTypeSlices', () => {
  it('groups by task type, sorted desc with percentage of total', () => {
    const slices = computeTypeSlices([
      task({ task_type: 'creative' }),
      task({ task_type: 'creative' }),
      task({ task_type: 'creative' }),
      task({ task_type: 'poetry' }),
      task({ task_type: 'manuscript' }),
      task({ task_type: 'manuscript' }),
      task({ task_type: 'manuscript' }),
      task({ task_type: 'manuscript' }),
    ])
    expect(slices[0].key).toBe('manuscript')
    expect(slices[0].value).toBe(4)
    expect(slices[0].pct).toBe(50)
    expect(slices.find((s) => s.key === 'creative')?.pct).toBe(38)
  })

  it('falls back to creative when task_type is missing', () => {
    const slices = computeTypeSlices([task({})])
    expect(slices[0].key).toBe('creative')
  })
})

describe('computeActivity', () => {
  const now = new Date(2026, 9, 30) // 2026-10-30 lokal

  it('returns one bucket per day including today, oldest first', () => {
    const days = computeActivity([], 14, now)
    expect(days).toHaveLength(14)
    expect(days[13].key).toBe('2026-10-30')
    expect(days[0].key).toBe('2026-10-17')
  })

  it('counts tasks into their created day', () => {
    const days = computeActivity(
      [
        task({ created_at: '2026-10-30T09:00:00' }),
        task({ created_at: '2026-10-30T18:30:00' }),
        task({ created_at: '2026-10-28T12:00:00' }),
      ],
      14,
      now,
    )
    expect(days[13].count).toBe(2)
    expect(days[11].count).toBe(1)
    expect(days[12].count).toBe(0)
  })

  it('ignores tasks without a valid timestamp instead of faking a date', () => {
    const days = computeActivity(
      [task({ created_at: '' }), task({ created_at: 'not-a-date' })],
      14,
      now,
    )
    expect(days.reduce((sum, d) => sum + d.count, 0)).toBe(0)
  })

  it('ignores tasks older than the window', () => {
    const days = computeActivity([task({ created_at: '2026-01-01T00:00:00' })], 14, now)
    expect(days.reduce((sum, d) => sum + d.count, 0)).toBe(0)
  })
})
