// 完成通知（P2）：任务在后台跑完时给系统通知，用户不必盯着进度条。
//
// 设计约束：
// - 只在用户显式开启后发通知（浏览器要求用户手势触发权限申请）。
// - 不做持久订阅：通知由 ProgressPage 的轮询状态变化驱动，页面卸载即停。
// - 同一次任务同一种结局只通知一次（notified 集合），避免续传/重试刷屏。
import { ref } from 'vue'
import { t } from '@/i18n'

const STORAGE_KEY = 'agnes.notify.completion'

/** 'unsupported' | 'default' | 'granted' | 'denied' */
const permission = ref<string>(
  typeof Notification === 'undefined' ? 'unsupported' : Notification.permission,
)

const enabled = ref<boolean>(localStorage.getItem(STORAGE_KEY) === '1')
const notified = new Set<string>()

function refreshPermission() {
  if (typeof Notification === 'undefined') {
    permission.value = 'unsupported'
    return
  }
  permission.value = Notification.permission
}

async function enable() {
  if (typeof Notification === 'undefined') {
    permission.value = 'unsupported'
    return false
  }
  const result = await Notification.requestPermission()
  permission.value = result
  enabled.value = result === 'granted'
  if (enabled.value) localStorage.setItem(STORAGE_KEY, '1')
  return enabled.value
}

function disable() {
  enabled.value = false
  localStorage.removeItem(STORAGE_KEY)
}

/**
 * 发送完成/失败通知。重复调用同一 key 只发一次。
 *
 * @param taskId 任务 id（用于去重）
 * @param ok true=成功，false=失败
 * @param detail 后端给出的说明（可空）
 */
function notify(taskId: string, ok: boolean, detail = '') {
  if (!enabled.value || permission.value !== 'granted') return
  const key = `${taskId}:${ok ? 'ok' : 'fail'}`
  if (notified.has(key)) return
  notified.add(key)
  try {
    // eslint-disable-next-line no-new
    new Notification(ok ? t('notifyDoneTitle') : t('notifyFailedTitle'), {
      body: detail || taskId,
      tag: key,
    })
  } catch {
    /* 浏览器策略拒绝时静默失败：通知是锦上添花，不能影响任务本身 */
  }
}

export function useCompletionNotify() {
  refreshPermission()
  return { permission, enabled, enable, disable, notify, refreshPermission }
}
