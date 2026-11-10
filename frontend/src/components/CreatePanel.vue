<script setup lang="ts">
import { computed } from 'vue'
import { t } from '@/i18n'
import { appState } from '@/store'
import { useGa } from '@/composables/useGa'
import { CREATE_TASK_TYPES, TASK_MANIFEST } from '@/taskManifest'
import type { TaskType } from '@/types'
import SimpleForm from './forms/SimpleForm.vue'
import CreativeForm from './forms/CreativeForm.vue'
import ScenarioStudioPanel from './ScenarioStudioPanel.vue'
import ManuscriptForm from './forms/ManuscriptForm.vue'
import AnchorForm from './forms/AnchorForm.vue'
import PoetryForm from './forms/PoetryForm.vue'
import MusicVideoForm from './forms/MusicVideoForm.vue'

const emit = defineEmits<{
  (e: 'open-settings'): void
}>()

const { trackEvent } = useGa()

const activeEntry = computed(() => TASK_MANIFEST[appState.createTaskType as TaskType] || TASK_MANIFEST.creative)
const manualSupported = computed(() => activeEntry.value.supportsManual)
const currentPausePoints = computed(() => activeEntry.value.pausePoints)

function switchTaskType(type: string) {
  trackEvent('ui_action', { action: 'switch_task_type', type })
  appState.createTaskType = type
  const entry = TASK_MANIFEST[type as TaskType]
  appState.pausePoints = [...(entry?.defaultPausePoints || [])]
}

function togglePausePoint(key: string) {
  const i = appState.pausePoints.indexOf(key)
  if (i >= 0) appState.pausePoints.splice(i, 1)
  else appState.pausePoints.push(key)
}

function selectExecMode(mode: 'auto' | 'manual') {
  if (mode === 'manual' && !manualSupported.value) return
  appState.execMode = mode
  if (mode === 'manual' && appState.pausePoints.length === 0) {
    appState.pausePoints = [...(activeEntry.value.defaultPausePoints || [])]
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- First-Run Onboarding Banner when API key is missing -->
    <div
      v-if="!appState.apiKeySource"
      class="glass-card rounded-2xl p-4 border-accent/40 bg-accent/5 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
      role="region"
      :aria-label="t('onboardingTitle')"
    >
      <div class="space-y-0.5">
        <p class="text-sm font-semibold text-ink">{{ t('onboardingTitle') }}</p>
        <p class="text-xs text-muted leading-relaxed">{{ t('onboardingDesc') }}</p>
      </div>
      <button
        type="button"
        class="px-4 py-2 rounded-lg text-xs font-semibold glow-btn shrink-0 self-start sm:self-center"
        @click="emit('open-settings')"
      >
        {{ t('onboardingAction') }}
      </button>
    </div>

    <!-- 1. Task Type Selector (Driven by TASK_MANIFEST) -->
    <div>
      <div class="flex items-center justify-between mb-3 px-1">
        <label class="text-xs font-medium text-muted">
          {{ t('tabCreate') }}
        </label>
        <div class="flex items-center gap-2 text-xs text-muted">
          <a href="https://video.lichuanyang.top/guides/prompt-tips" target="_blank" rel="noopener" class="hover:text-accent transition">{{ t('formTipTips') }}</a>
          <span class="text-rule">·</span>
          <a href="https://video.lichuanyang.top/api-docs" target="_blank" rel="noopener" class="hover:text-accent transition">{{ t('formTipModels') }}</a>
        </div>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <button
          v-for="tt in CREATE_TASK_TYPES"
          :key="tt.key"
          type="button"
          class="relative p-3.5 rounded-xl text-left transition-colors duration-150 cursor-pointer flex flex-col justify-between"
          :class="
            appState.createTaskType === tt.key
              ? 'bg-paper-2 border border-accent text-ink'
              : 'bg-paper-2/60 border border-rule text-ink-2 hover:border-rule/80'
          "
          @click="switchTaskType(tt.key)"
        >
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-accent">
                <svg v-if="tt.key === 'creative'" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M4 6h8a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2z" />
                </svg>
                <svg v-else-if="tt.key === 'simple'" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <svg v-else-if="tt.key === 'manuscript'" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <svg v-else-if="tt.key === 'anchor'" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                <svg v-else-if="tt.key === 'music_video'" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                </svg>
                <svg v-else class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </span>
              <span
                v-if="appState.createTaskType === tt.key"
                class="w-2 h-2 rounded-full bg-accent"
              ></span>
            </div>
            <div class="font-semibold text-sm leading-tight text-ink">
              {{ t(tt.createLabelKey || tt.labelKey) }}
            </div>
          </div>
          <div class="text-[11px] text-muted leading-tight mt-1">
            {{ t(tt.createDescKey || tt.labelKey) }}
          </div>
        </button>
      </div>
    </div>

    <!-- 2. Execution Pipeline Toolbar -->
    <div v-if="manualSupported" class="glass-card rounded-xl p-4 border border-rule">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <span class="text-xs font-medium text-ink">{{ t('execMode') }}:</span>
          <div class="inline-flex p-1 rounded-lg bg-paper border border-rule text-xs font-medium">
            <button
              type="button"
              class="px-3.5 py-1.5 rounded-md transition"
              :class="appState.execMode === 'auto' ? 'bg-paper-3 text-ink font-semibold border border-rule' : 'text-muted hover:text-ink'"
              @click="selectExecMode('auto')"
            >
              {{ t('execAuto').replace(/^[^\p{L}\p{N}]+/u, '') }}
            </button>
            <button
              type="button"
              class="px-3.5 py-1.5 rounded-md transition"
              :class="appState.execMode === 'manual' ? 'bg-paper-3 text-ink font-semibold border border-rule' : 'text-muted hover:text-ink'"
              @click="selectExecMode('manual')"
            >
              {{ t('execManual').replace(/^[^\p{L}\p{N}]+/u, '') }}
            </button>
          </div>
        </div>
        <span class="text-xs text-muted max-w-md">
          {{ t('execModeHint') }}
        </span>
      </div>

      <div v-if="appState.execMode === 'manual'" class="mt-3 pt-3 border-t border-rule/40">
        <div class="text-xs text-muted mb-2 font-medium">
          {{ t('pausePoints') }}:
        </div>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="p in currentPausePoints"
            :key="p.key"
            type="button"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 cursor-pointer"
            :class="
              appState.pausePoints.includes(p.key)
                ? 'bg-paper-3 border border-accent/50 text-accent font-semibold'
                : 'bg-paper-2 border border-rule text-muted hover:text-ink-2'
            "
            @click="togglePausePoint(p.key)"
          >
            <span class="w-1.5 h-1.5 rounded-full" :class="appState.pausePoints.includes(p.key) ? 'bg-accent' : 'bg-transparent border border-muted'"></span>
            <span>{{ t(p.labelKey) }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 3. Form Content -->
    <SimpleForm v-if="appState.createTaskType === 'simple'" />
    <template v-else-if="appState.createTaskType === 'creative'">
      <CreativeForm />
      <ScenarioStudioPanel />
    </template>
    <ManuscriptForm v-else-if="appState.createTaskType === 'manuscript'" />
    <AnchorForm v-else-if="appState.createTaskType === 'anchor'" />
    <PoetryForm v-else-if="appState.createTaskType === 'poetry'" />
    <MusicVideoForm v-else-if="appState.createTaskType === 'music_video'" />
  </div>
</template>
