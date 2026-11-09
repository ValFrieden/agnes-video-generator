<script setup lang="ts">
import { computed } from 'vue'
import { t } from '@/i18n'
import { useTasks } from '@/composables/useTasks'
import { useConfirm } from '@/composables/useConfirm'
import { statusTextCls, statusLabelKey } from '@/utils/status'
import type { TaskListItem } from '@/types'
import TaskDashboard from './TaskDashboard.vue'

const { tasks, loading, loadTaskList, viewTask, viewRunningTask, resumeTask, stopTaskById, deleteTaskById, switchMode } = useTasks()
const { confirmAsync } = useConfirm()

async function toggleMode(task: TaskListItem) {
  const target = task.current_mode === 'manual' ? 'auto' : 'manual'
  if (!(await confirmAsync(target === 'auto' ? t('switchToAutoConfirm') : t('switchToManualConfirm')))) return
  const d = await switchMode(task.task_id, target as 'auto' | 'manual')
  if (d && task.awaiting_user && target === 'auto') {
    // 手动→自动：切换即继续（后端已 resume），刷新列表
    loadList()
  }
}

function loadList() {
  // useTasks 内部轮询 5s；此处立即刷新一次（1.7：收敛裸 fetch 到 useTasks，
  // 复用 in-flight 守卫与错误处理）
  void loadTaskList()
}

const typeLabelKey: Record<string, string> = {
  simple: 'typeSimple',
  creative: 'typeCreative',
  manuscript: 'typeManuscript',
  anchor: 'typeAnchor',
  poetry: 'typePoetry',
  image: 'typeImage',
}

function taskDesc(task: TaskListItem): string {
  return (
    task.idea ||
    task.prompt ||
    (task.manuscript_text || '').substring(0, 80) ||
    (task.script_text || '').substring(0, 80) ||
    (task.poem_text || '').substring(0, 80) ||
    ''
  )
}

function taskExtra(task: TaskListItem): string {
  if (task.scene_count) return ` · ${task.scene_count}${t('sceneUnit')}`
  if (task.paragraph_count) return ` · ${task.paragraph_count}${t('paraUnit')}`
  return ''
}

function isRunning(task: TaskListItem): boolean {
  return task.status === 'running' || task.status === 'queued'
}

function isCompleted(task: TaskListItem): boolean {
  return task.status === 'completed'
}

function isFailed(task: TaskListItem): boolean {
  return task.status === 'failed'
}

function mainBtnLabel(task: TaskListItem): string {
  if (isCompleted(task)) return t('btnView')
  if (isRunning(task)) return t('btnViewProgress')
  if (isFailed(task)) return t('btnView')
  // Logikcheck Befund 2: wartende Prüfpunkt-Aufgaben prüfen statt fortsetzen
  if (task.awaiting_user) return t('btnReviewCheckpoint')
  // Logikcheck Befund 1: Bild-Aufträge sind synchron — kein Resume möglich
  if (task.task_type === 'image') return t('btnView')
  return t('btnResume')
}

function onMainBtn(task: TaskListItem) {
  if (isCompleted(task)) viewTask(task.task_id)
  else if (isRunning(task)) viewRunningTask(task.task_id)
  else if (isFailed(task)) viewTask(task.task_id)
  else if (task.awaiting_user) {
    // Logikcheck Befund 2: zur Prüfung/Freigabe öffnen — der generische Resume
    // würde den manuellen Prüfpunkt still überspringen (Backend blockt mit 409).
    viewTask(task.task_id)
  }
  else if (task.task_type === 'image') viewTask(task.task_id)
  else resumeTask(task.task_id)
}
</script>

<template>
  <div class="space-y-3">
    <!-- P2 项目概览：聚合已加载的任务列表，无额外请求 -->
    <TaskDashboard />
    <!-- P1 a11y：首次加载明确提示，不让空白页冒充「keine Aufgaben」 -->
    <p v-if="loading && !tasks.length" class="text-muted text-sm px-1" role="status" aria-live="polite">
      {{ t('loading') }}
    </p>
    <!-- Leerzustand erst nach abgeschlossenem Laden zeigen (sonst Blitz beim Start) -->
    <div v-if="!loading && !tasks.length" class="neu-card rounded-2xl p-8 text-center border border-rule/30">
      <p class="text-muted text-sm mb-4">{{ t('noTasks') }}</p>
      <a href="#/create" class="inline-block text-sm px-5 py-2.5 neu-raised hover:neu-sunken text-accent font-medium rounded-xl transition">
        {{ t('tabCreate') }}
      </a>
    </div>
    <div
      v-for="task in tasks"
      :key="task.task_id"
      class="neu-raised rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 transition-all hover:translate-y-[-1px] border border-rule/20 mb-3"
    >
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1.5">
          <span class="text-xs px-2.5 py-0.5 rounded-full neu-sunken text-accent font-medium">
            {{ t(typeLabelKey[task.task_type || ''] || '') || task.task_type }}
          </span>
          <p class="text-sm font-semibold truncate text-ink">{{ task.creative_name || task.task_id }}</p>
          <!-- v6.0 模式徽标 -->
          <span v-if="task.awaiting_user" class="badge-warning text-xs px-2 py-0.5 rounded-full neu-raised">
            {{ t('awaitingUser') }}
          </span>
          <span v-else-if="task.current_mode === 'manual'" class="badge-info text-xs px-2 py-0.5 rounded-full neu-raised">
            {{ t('execManual') }}
          </span>
        </div>
        <p class="text-xs text-muted mt-0.5">{{ task.task_id }}{{ taskExtra(task) }}</p>
        <p v-if="taskDesc(task)" class="text-xs text-muted mt-1 truncate max-w-sm">{{ taskDesc(task) }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-2 md:gap-2.5 md:ml-4 shrink-0">
        <span class="text-xs px-2.5 py-1 rounded-full neu-sunken font-medium" :class="statusTextCls(task.status || '')">
          {{ t(statusLabelKey(task.status || '')) }}
        </span>
        <!-- v6.0 运行时切换（已完成/失败任务不显示） -->
        <button
          v-if="task.current_mode && !isCompleted(task) && task.status !== 'failed' && task.task_type !== 'simple' && task.task_type !== 'image'"
          class="text-xs px-3 py-1.5 rounded-xl transition neu-raised hover:neu-sunken text-ink-2"
          :title="t(task.current_mode === 'manual' ? 'switchToAuto' : 'switchToManual')"
          @click="toggleMode(task)"
        >
          {{ task.current_mode === 'manual' ? t('switchToAuto') : t('switchToManual') }}
        </button>
        <!-- Für fehlgeschlagene Aufgaben: Fortsetzen als sekundäre Aktion; für pausierte: Ansehen -->
        <button
          v-if="isFailed(task) && task.task_type !== 'image'"
          class="text-xs px-3 py-1.5 neu-raised hover:neu-sunken rounded-xl transition text-ink-2"
          @click="resumeTask(task.task_id)"
        >
          {{ t('btnResume') }}
        </button>
        <button
          v-else-if="!isCompleted(task) && !isRunning(task) && !task.awaiting_user && task.task_type !== 'image'"
          class="text-xs px-3 py-1.5 neu-raised hover:neu-sunken rounded-xl transition text-ink-2"
          @click="viewTask(task.task_id)"
        >
          {{ t('btnView') }}
        </button>
        <button class="text-xs px-3.5 py-1.5 neu-raised hover:neu-sunken text-accent font-semibold rounded-xl transition glow-btn" @click="onMainBtn(task)">
          {{ mainBtnLabel(task) }}
        </button>
        <button
          v-if="isRunning(task)"
          class="btn-danger text-xs px-3 py-1.5 rounded-xl neu-raised hover:neu-sunken"
          @click="stopTaskById(task.task_id)"
        >
          {{ t('btnStop') }}
        </button>
        <button
          v-if="!isRunning(task)"
          class="btn-danger-soft text-xs px-3 py-1.5 rounded-xl neu-raised hover:neu-sunken"
          @click="deleteTaskById(task.task_id)"
        >
          {{ t('deleteTask') }}
        </button>
      </div>
    </div>
  </div>
</template>
