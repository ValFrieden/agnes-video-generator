<script setup lang="ts">
import { computed } from 'vue'
import { t } from '@/i18n'
import { appState } from '@/store'
import { useProgress } from '@/composables/useProgress'
import { useTasks } from '@/composables/useTasks'
import { useNavigation } from '@/composables/useNavigation'
import LangSwitcher from '@/components/shared/LangSwitcher.vue'

const { progressPct, awaitingCheckpoint, taskFailed, needsResume, resumeTask } = useProgress()
const { stopTaskById, switchMode } = useTasks()
const { goBack, goHome } = useNavigation()

const taskId = computed(() => appState.currentTaskId || appState.progressTaskId || '')
const dirName = computed(() => appState.currentDirName || '')

const typeLabelKey: Record<string, string> = {
  simple: 'typeSimple',
  creative: 'typeCreative',
  manuscript: 'typeManuscript',
  anchor: 'typeAnchor',
  poetry: 'typePoetry',
  image: 'typeImage',
}

const statusInfo = computed(() => {
  if (taskFailed.value) return { key: 'statusFailed', cls: 'badge-danger' }
  if (needsResume.value) return { key: 'statusNeedsResume', cls: 'badge-warning' }
  if (awaitingCheckpoint.value) return { key: 'statusAwaitingUser', cls: 'badge-warning' }
  if (appState.isTaskRunning || progressPct.value > 0 && progressPct.value < 100) {
    return { key: 'statusRunning', cls: 'badge-warning' }
  }
  return { key: 'statusCompleted', cls: 'badge-success' }
})

function onBack() {
  goBack()
}

function onHome() {
  goHome()
}

async function onStop() {
  if (taskId.value) await stopTaskById(taskId.value)
}

async function onResume() {
  if (taskId.value) await resumeTask(taskId.value)
}

async function onSwitchAuto() {
  if (taskId.value) await switchMode(taskId.value, 'auto')
}
</script>

<template>
  <header class="sticky top-0 z-40 bg-paper/90 backdrop-blur-md border-b border-rule/30 neu-raised">
    <div class="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
      <button
        class="flex items-center gap-1.5 text-sm font-medium text-ink-2 hover:text-accent transition rounded-xl px-3 py-1.5 neu-raised hover:neu-sunken"
        @click="onBack"
      >
        <span class="text-base leading-none">←</span>
        <span class="text-xs">{{ t('progressBack') }}</span>
      </button>

      <a
        href="#"
        class="flex items-center gap-1.5 text-sm text-accent hover:text-ink transition rounded-xl px-3 py-1.5 neu-raised hover:neu-sunken"
        @click.prevent="onHome"
      >
        <svg class="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
        <span class="text-xs">{{ t('goHome') }}</span>
      </a>

      <div class="flex items-center gap-2 min-w-0">
        <span class="text-xs px-2.5 py-0.5 rounded-full neu-sunken text-accent font-medium shrink-0">
          {{ t(typeLabelKey[appState.currentTaskType] || '') || appState.currentTaskType }}
        </span>
        <span class="text-sm font-semibold truncate text-ink">{{ t('task_') }}: {{ taskId }}</span>
        <span v-if="dirName" class="text-xs text-muted font-mono truncate hidden md:inline px-2 py-0.5 rounded-full neu-sunken">{{ dirName }}</span>
      </div>

      <div class="ml-auto flex items-center gap-2.5 shrink-0">
        <LangSwitcher compact />
        <span class="text-xs px-2.5 py-1 rounded-full neu-sunken font-medium" :class="statusInfo.cls">
          {{ t(statusInfo.key) }}
        </span>
        <button
          v-if="needsResume"
          class="inline-flex items-center gap-1.5 text-xs px-3.5 py-1.5 neu-raised hover:neu-sunken text-accent font-semibold rounded-xl transition glow-btn"
          @click="onResume"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          {{ t('resumeTaskBtn') }}
        </button>
        <button
          v-if="awaitingCheckpoint"
          class="inline-flex items-center gap-1.5 text-xs px-3.5 py-1.5 neu-raised hover:neu-sunken text-ink-2 rounded-xl transition"
          @click="onSwitchAuto"
        >
          <svg class="w-3.5 h-3.5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          {{ t('switchToAuto') }}
        </button>
        <button
          v-if="appState.isTaskRunning"
          class="btn-danger text-xs px-3.5 py-1.5 rounded-xl neu-raised hover:neu-sunken"
          @click="onStop"
        >
          {{ t('stopTask') }}
        </button>
      </div>
    </div>
  </header>
</template>
