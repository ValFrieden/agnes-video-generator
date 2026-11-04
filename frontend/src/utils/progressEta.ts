// 剩余时间估算（Progress ETA）—— 纯函数，便于单测。
//
// 口径：用任务创建时间 `created_at` 到现在作为已耗时，按当前进度线性外推。
// 明确不适用的场景一律返回 `insufficient`，绝不猜：
// - 任务没有 created_at（旧任务）；
// - 进度太低（< 3%）——外推会把 0.5 秒放大成几小时；
// - 已耗时非正数（时钟漂移）。
// 线性外推对「逐场景生成」这类均匀环节足够准；遇到单步长尾（如视频排队）
// 会低估，因此 UI 上方用「≈」标注为估算。
import type { TaskListItem } from '@/types'

export type EtaState = 'estimating' | 'insufficient' | 'done'

export interface EtaEstimate {
  state: EtaState
  /** 已耗时（秒），无法计算时为 null */
  elapsedSec: number | null
  /** 预计剩余（秒），无法计算时为 null */
  remainingSec: number | null
}

const MIN_PCT_FOR_ESTIMATE = 3
const MAX_REASONABLE_SEC = 24 * 3600

/**
 * 估算剩余时间。
 *
 * @param pct 当前进度百分比（0–100）
 * @param createdAt 任务创建时间（`YYYY-MM-DDTHH:MM:SS`，本地时间、无时区）
 * @param now 当前时间（注入以便测试）
 */
export function estimateEta(pct: number, createdAt: string, now: Date = new Date()): EtaEstimate {
  if (pct >= 100) return { state: 'done', elapsedSec: null, remainingSec: null }

  const started = parseLocalStamp(createdAt)
  if (started === null) return { state: 'insufficient', elapsedSec: null, remainingSec: null }

  const elapsedSec = (now.getTime() - started.getTime()) / 1000
  if (!Number.isFinite(elapsedSec) || elapsedSec <= 0) {
    return { state: 'insufficient', elapsedSec: null, remainingSec: null }
  }
  if (pct < MIN_PCT_FOR_ESTIMATE) {
    return { state: 'insufficient', elapsedSec: Math.round(elapsedSec), remainingSec: null }
  }

  const remainingSec = Math.round((elapsedSec * (100 - pct)) / pct)
  if (!Number.isFinite(remainingSec) || remainingSec < 0 || remainingSec > MAX_REASONABLE_SEC) {
    // 超过 24 小时的外推视为无意义（多半是旧任务或长期暂停）
    return { state: 'insufficient', elapsedSec: Math.round(elapsedSec), remainingSec: null }
  }
  return { state: 'estimating', elapsedSec: Math.round(elapsedSec), remainingSec }
}

/** 解析 `YYYY-MM-DDTHH:MM:SS`（本地时间）或纯日期；非法返回 null。 */
export function parseLocalStamp(stamp: string): Date | null {
  if (!stamp) return null
  const m = stamp.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?/)
  if (!m) return null
  const [, y, mo, d, hh, mm, ss] = m
  const date = new Date(
    Number(y),
    Number(mo) - 1,
    Number(d),
    Number(hh ?? 0),
    Number(mm ?? 0),
    Number(ss ?? 0),
  )
  return Number.isNaN(date.getTime()) ? null : date
}

/** 秒 → `1 h 05 min` / `12 min` / `< 1 min`（纯数字单位，不随语言变化）。 */
export function formatDuration(totalSec: number): string {
  if (totalSec < 60) return '< 1 min'
  const minutes = Math.round(totalSec / 60)
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest ? `${hours} h ${String(rest).padStart(2, '0')} min` : `${hours} h`
}

/** 便捷入口：直接从任务条目与进度算。 */
export function etaForTask(
  task: TaskListItem | null | undefined,
  pct: number,
  now: Date = new Date(),
): EtaEstimate {
  return estimateEta(pct, task?.created_at || '', now)
}
