<script setup lang="ts">
import { computed, ref } from 'vue'
import { t } from '@/i18n'
import { appState } from '@/store'
import * as api from '@/api'
import { useTasks } from '@/composables/useTasks'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { statusTextCls, statusLabelKey } from '@/utils/status'
import { TYPE_LABEL_KEY_MAP, buildDraftFromTaskState } from '@/taskManifest'
import type { TaskListItem } from '@/types'
import TaskDashboard from './TaskDashboard.vue'

const { tasks, loading, loadTaskList, viewTask, viewRunningTask, resumeTask, stopTaskById, deleteTaskById, switchMode } = useTasks()
const { confirmAsync } = useConfirm()
const { showToast } = useToast()

// Search, filter, pagination & batch selection (P1-5)
const searchQuery = ref('')
const statusFilter = ref<'all' | 'running' | 'awaiting' | 'completed' | 'failed' | 'pending'>('all')
const typeFilter = ref<string>('all')
const pageSize = 20
const visibleLimit = ref(pageSize)
const selectedIds = ref<string[]>([])
const batchDeleting = ref(false)

function isRunning(task: TaskListItem): boolean {
  return task.status === 'running' || task.status === 'queued'
}
function isCompleted(task: TaskListItem): boolean {
  return task.status === 'completed'
}
function isFailed(task: TaskListItem): boolean {
  return task.status === 'failed'
}

function taskDesc(task: TaskListItem): string {
  return (
    task.idea ||
    task.prompt ||
    task.song_title ||
    (task.manuscript_text || '').substring(0, 80) ||
    (task.script_text || '').substring(0, 80) ||
    (task.poem_text || '').substring(0, 80) ||
    ''
  )
}

const filteredTasks = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return tasks.value.filter((task) => {
    if (typeFilter.value !== 'all' && task.task_type !== typeFilter.value) return false
    if (statusFilter.value === 'running' && !isRunning(task)) return false
    if (statusFilter.value === 'awaiting' && !task.awaiting_user) return false
    if (statusFilter.value === 'completed' && !isCompleted(task)) return false
    if (statusFilter.value === 'failed' && !isFailed(task)) return false
    if (statusFilter.value === 'pending' && (task.status !== 'pending' || task.awaiting_user)) return false
    if (q) {
      const hay = [
        task.task_id,
        task.creative_name,
        task.idea,
        task.prompt,
        task.song_title,
        task.manuscript_text,
        task.script_text,
        task.poem_text,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      if (!hay.includes(q)) return false
    }
    return true
  })
})

const pagedTasks = computed(() => filteredTasks.value.slice(0, visibleLimit.value))
const hasMore = computed(() => filteredTasks.value.length > visibleLimit.value)
const deletableVisibleIds = computed(() => pagedTasks.value.filter((x) => !isRunning(x)).map((x) => x.task_id))

function toggleSelect(id: string) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function toggleSelectAllVisible() {
  const allIds = deletableVisibleIds.value
  const allSelected = allIds.length > 0 && allIds.every((id) => selectedIds.value.includes(id))
  if (allSelected) {
    selectedIds.value = selectedIds.value.filter((id) => !allIds.includes(id))
  } else {
    const merged = new Set([...selectedIds.value, ...allIds])
    selectedIds.value = Array.from(merged)
  }
}

async function batchDeleteSelected() {
  const ids = [...selectedIds.value]
  if (!ids.length) return
  const msg = t('taskBatchDeleteConfirm').replace('{n}', String(ids.length))
  if (!(await confirmAsync(msg))) return
  batchDeleting.value = true
  try {
    for (const id of ids) {
      await api.deleteTask(id)
    }
    selectedIds.value = []
    showToast(t('deletedTask'), 3000, 'success')
    await loadTaskList()
  } catch (e: any) {
    showToast(t('failDelete') + ': ' + (e?.message || ''), 4000, 'error')
  } finally {
    batchDeleting.value = false
  }
}

async function cloneTask(taskId: string) {
  try {
    const state = await api.getTask(taskId)
    const mapped = buildDraftFromTaskState(state)
    if (!mapped) {
      showToast(t('taskCloneUnsupported'), 3000)
      return
    }
    localStorage.setItem('wb_draft_' + mapped.draftKey, JSON.stringify(mapped.payload))
    appState.createTaskType = mapped.createTab
    appState.view = 'create'
    location.hash = '#/create'
    showToast(t('taskCloned'), 3000, 'success')
  } catch (e: any) {
    showToast(t('failLoad') + ': ' + (e?.message || ''), 4000, 'error')
  }
}

async function toggleMode(task: TaskListItem) {
  const target = task.current_mode === 'manual' ? 'auto' : 'manual'
  if (!(await confirmAsync(target === 'auto' ? t('switchToAutoConfirm') : t('switchToManualConfirm')))) return
  const d = await switchMode(task.task_id, target as 'auto' | 'manual')
  if (d && task.awaiting_user && target === 'auto') {
    void loadTaskList()
  }
}

function taskExtra(task: TaskListItem): string {
  if (task.scene_count) return ` · ${task.scene_count}${t('sceneUnit')}`
  if (task.paragraph_count) return ` · ${task.paragraph_count}${t('paraUnit')}`
  return ''
}

function mainBtnLabel(task: TaskListItem): string {
  if (isCompleted(task)) return t('btnView')
  if (isRunning(task)) return t('btnViewProgress')
  if (isFailed(task)) return t('btnView')
  if (task.awaiting_user) return t('btnReviewCheckpoint')
  if (task.task_type === 'image') return t('btnView')
  return t('btnResume')
}

function onMainBtn(task: TaskListItem) {
  if (isCompleted(task)) viewTask(task.task_id)
  else if (isRunning(task)) viewRunningTask(task.task_id)
  else if (isFailed(task)) viewTask(task.task_id)
  else if (task.awaiting_user) viewTask(task.task_id)
  else if (task.task_type === 'image') viewTask(task.task_id)
  else resumeTask(task.task_id)
}
</script>

<template>
  <div class="space-y-3">
    <TaskDashboard />

    <!-- Search, Filter & Batch Toolbar -->
    <div v-if="tasks.length" class="glass-card rounded-2xl p-3.5 flex flex-wrap items-center gap-2.5">
      <input
        v-model="searchQuery"
        type="search"
        :placeholder="t('taskSearchPlaceholder')"
        :aria-label="t('taskSearchPlaceholder')"
        class="flex-1 min-w-[180px] glass-input rounded-lg px-3 py-1.5 text-xs text-ink placeholder-muted"
      />
      <select
        v-model="statusFilter"
        :aria-label="t('filterStatusAll')"
        class="glass-input rounded-lg px-2.5 py-1.5 text-xs text-ink"
      >
        <option value="all">{{ t('filterStatusAll') }}</option>
        <option value="running">{{ t('statusRunning') }}</option>
        <option value="awaiting">{{ t('awaitingUser') }}</option>
        <option value="completed">{{ t('statusCompleted') }}</option>
        <option value="failed">{{ t('statusFailed') }}</option>
        <option value="pending">{{ t('statusPending') }}</option>
      </select>
      <select
        v-model="typeFilter"
        :aria-label="t('filterAll')"
        class="glass-input rounded-lg px-2.5 py-1.5 text-xs text-ink"
      >
        <option value="all">{{ t('filterAll') }}</option>
        <option v-for="(labelKey, key) in TYPE_LABEL_KEY_MAP" :key="key" :value="key">
          {{ t(labelKey) }}
        </option>
      </select>

      <div v-if="deletableVisibleIds.length" class="flex items-center gap-2 ml-auto">
        <button
          type="button"
          class="text-xs px-2.5 py-1.5 rounded-lg border border-rule bg-paper text-ink-2 hover:text-ink transition"
          @click="toggleSelectAllVisible"
        >
          {{ t('taskSelectAll') }}
        </button>
        <button
          v-if="selectedIds.length"
          type="button"
          class="btn-danger text-xs px-3 py-1.5 disabled:opacity-50"
          :disabled="batchDeleting"
          @click="batchDeleteSelected"
        >
          {{ t('taskBatchDelete').replace('{n}', String(selectedIds.length)) }}
        </button>
      </div>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading && !tasks.length" class="space-y-3" role="status" aria-live="polite" :aria-label="t('loading')">
      <div v-for="i in 3" :key="i" class="glass-card rounded-2xl p-4 animate-pulse space-y-2">
        <div class="h-4 bg-paper-3 rounded w-1/3"></div>
        <div class="h-3 bg-paper-3 rounded w-2/3"></div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!loading && !tasks.length" class="neu-card rounded-2xl p-8 text-center border border-rule/30">
      <div class="flex justify-center mb-4 text-muted/40">
        <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M4 6h8a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2z" />
        </svg>
      </div>
      <p class="text-muted text-sm mb-4">{{ t('noTasks') }}</p>
      <a href="#/create" class="inline-block text-sm px-5 py-2.5 neu-raised hover:neu-sunken text-accent font-medium rounded-xl transition">
        {{ t('tabCreate') }}
      </a>
    </div>

    <!-- Filtered Empty State -->
    <div v-else-if="!filteredTasks.length" class="glass-card rounded-2xl p-6 text-center space-y-2">
      <p class="text-sm text-muted">{{ t('taskFilterEmpty') }}</p>
      <button
        type="button"
        class="text-xs px-3 py-1.5 rounded-lg border border-rule bg-paper text-ink-2 hover:text-ink"
        @click="searchQuery = ''; statusFilter = 'all'; typeFilter = 'all'"
      >
        {{ t('clear') }}
      </button>
    </div>

    <!-- Task Cards -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <div
        v-for="task in pagedTasks"
        :key="task.task_id"
        class="neu-raised rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 transition-all hover:translate-y-[-1px] border border-rule/20 mb-3"
      >
      <div class="flex items-start gap-3 flex-1 min-w-0">
        <input
          v-if="!isRunning(task)"
          type="checkbox"
          :checked="selectedIds.includes(task.task_id)"
          :aria-label="task.creative_name || task.task_id"
          class="mt-1 rounded border-rule bg-paper cursor-pointer"
          @change="toggleSelect(task.task_id)"
        />
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1.5 flex-wrap">
            <span class="text-xs px-2.5 py-0.5 rounded-full neu-sunken text-accent font-medium">
              {{ t(TYPE_LABEL_KEY_MAP[task.task_type || ''] || '') || task.task_type }}
            </span>
            <p class="text-sm font-semibold truncate text-ink">{{ task.creative_name || task.task_id }}</p>
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
      </div>

      <div class="flex flex-wrap items-center gap-2 md:gap-2.5 md:ml-4 shrink-0">
        <span class="text-xs px-2.5 py-1 rounded-full neu-sunken font-medium" :class="statusTextCls(task.status || '')">
          {{ t(statusLabelKey(task.status || '')) }}
        </span>
        <button
          v-if="task.task_type !== 'image'"
          class="text-xs px-2.5 py-1.5 rounded-xl transition neu-raised hover:neu-sunken text-ink-2"
          :title="t('taskCloneBtn')"
          @click="cloneTask(task.task_id)"
        >
          {{ t('taskCloneBtn') }}
        </button>
        <button
          v-if="task.current_mode && !isCompleted(task) && task.status !== 'failed' && task.task_type !== 'simple' && task.task_type !== 'image'"
          class="text-xs px-3 py-1.5 rounded-xl transition neu-raised hover:neu-sunken text-ink-2"
          :title="t(task.current_mode === 'manual' ? 'switchToAuto' : 'switchToManual')"
          @click="toggleMode(task)"
        >
          {{ task.current_mode === 'manual' ? t('switchToAuto') : t('switchToManual') }}
        </button>
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
        <button class="text-xs px-3.5 py-1.5 font-semibold rounded-xl transition glow-btn" @click="onMainBtn(task)">
          {{ mainBtnLabel(task) }}
        </button>
        <button
          v-if="isRunning(task)"
          class="btn-danger text-xs px-3 py-1.5 rounded-xl"
          @click="stopTaskById(task.task_id)"
        >
          {{ t('btnStop') }}
        </button>
        <button
          v-if="!isRunning(task)"
          class="btn-danger-soft text-xs px-3 py-1.5 rounded-xl"
          @click="deleteTaskById(task.task_id)"
        >
          {{ t('deleteTask') }}
        </button>
      </div>
    </div>
    </div>

    <!-- Pagination -->
    <div v-if="hasMore" class="flex items-center justify-center pt-2">
      <button
        type="button"
        class="px-5 py-2 rounded-xl text-xs font-medium bg-paper-2 border border-rule text-ink-2 hover:text-ink hover:border-accent/50 transition"
        @click="visibleLimit += pageSize; if (visibleLimit > tasks.length && !loading) loadTaskList({ limit: 50, offset: tasks.length, append: true })"
      >
        {{ t('taskLoadMore').replace('{shown}', String(pagedTasks.length)).replace('{total}', String(filteredTasks.length)) }}
      </button>
    </div>
  </div>
</template>
