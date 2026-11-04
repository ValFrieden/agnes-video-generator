// 项目概览的纯聚合逻辑（与组件解耦，便于单测）。
// 输入是 /api/tasks 返回的轻量任务列表；不读盘、不发请求。
import type { TaskListItem } from '@/types'

export interface TaskStats {
  total: number
  counts: Record<string, number>
  finished: number
  activeNow: number
  successRate: number | null
}

export interface TypeSlice {
  key: string
  value: number
  pct: number
}

export interface ActivityDay {
  key: string
  label: string
  count: number
}

/** 汇总任务状态。未知状态计入 counts 但不影响成功率分母。 */
export function computeTaskStats(tasks: TaskListItem[]): TaskStats {
  const counts: Record<string, number> = { running: 0, queued: 0, pending: 0, completed: 0, failed: 0 }
  for (const task of tasks) {
    const s = task.status || 'pending'
    counts[s] = (counts[s] || 0) + 1
  }
  const finished = counts.completed + counts.failed
  return {
    total: tasks.length,
    counts,
    finished,
    activeNow: counts.running + counts.queued,
    successRate: finished ? Math.round((counts.completed / finished) * 100) : null,
  }
}

/** 按任务类型分组，降序；百分比相对总数。 */
export function computeTypeSlices(tasks: TaskListItem[]): TypeSlice[] {
  const map = new Map<string, number>()
  for (const task of tasks) {
    const key = task.task_type || 'creative'
    map.set(key, (map.get(key) || 0) + 1)
  }
  const total = tasks.length
  return [...map.entries()]
    .map(([key, value]) => ({ key, value, pct: total ? Math.round((value / total) * 100) : 0 }))
    .sort((a, b) => b.value - a.value)
}

function dayKey(d: Date): string {
  // 本地日期（不用 toISOString：那是 UTC，跨时区会把任务算到前一天）
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/**
 * 最近 N 天（含今天）新建任务数。
 *
 * 只统计带合法 `created_at` 前缀的任务；旧任务没有时间戳就不计入，
 * 而不是伪造一个日期把它们算到「今天」。
 */
export function computeActivity(tasks: TaskListItem[], days = 14, now = new Date()): ActivityDay[] {
  const buckets = new Map<string, number>()
  for (const task of tasks) {
    const stamp = (task.created_at || '').slice(0, 10)
    if (!/^\d{4}-\d{2}-\d{2}$/.test(stamp)) continue
    buckets.set(stamp, (buckets.get(stamp) || 0) + 1)
  }
  const out: ActivityDay[] = []
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(now.getDate() - i)
    const key = dayKey(d)
    out.push({ key, label: String(d.getDate()), count: buckets.get(key) || 0 })
  }
  return out
}
