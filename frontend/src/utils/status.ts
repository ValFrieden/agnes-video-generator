// 任务状态的徽标样式与文案 key —— 单一来源。
// 此前 TaskListPanel 与 GalleryPanel 各自维护一份 Map，颜色漂移过一次
// （见 GalleryPanel Logikcheck Befund 10）；集中在此杜绝再次分叉。
// 颜色使用语义 token（text-success / text-danger …），亮暗主题自动适配。

export type TaskStatus = 'completed' | 'failed' | 'running' | 'pending' | 'queued'

const STATUS_TEXT_CLS: Record<TaskStatus, string> = {
  completed: 'text-success',
  failed: 'text-danger',
  running: 'text-warning',
  pending: 'text-muted',
  queued: 'text-accent',
}

const STATUS_LABEL_KEY: Record<TaskStatus, string> = {
  completed: 'statusCompleted',
  failed: 'statusFailed',
  running: 'statusRunning',
  pending: 'statusPending',
  queued: 'statusQueued',
}

/** 状态文字颜色类；未知状态回退为 text-muted。 */
export function statusTextCls(status: string): string {
  return STATUS_TEXT_CLS[status as TaskStatus] || 'text-muted'
}

/** 状态文案的 i18n key；未知状态回退为 statusPending。 */
export function statusLabelKey(status: string): string {
  return STATUS_LABEL_KEY[status as TaskStatus] || 'statusPending'
}
