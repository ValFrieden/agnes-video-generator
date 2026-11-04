<script setup lang="ts">
import { ref, computed } from 'vue'
import { t } from '@/i18n'
import { appState } from '@/store'
import { useGa } from '@/composables/useGa'
import SimpleForm from './forms/SimpleForm.vue'
import CreativeForm from './forms/CreativeForm.vue'
import ScenarioStudioPanel from './ScenarioStudioPanel.vue'
import ManuscriptForm from './forms/ManuscriptForm.vue'
import AnchorForm from './forms/AnchorForm.vue'
import PoetryForm from './forms/PoetryForm.vue'

const { trackEvent } = useGa()

const taskTypes = [
  { key: 'creative', label: 'ttCreative', desc: 'AI Story · Keyframes · Audio' },
  { key: 'simple', label: 'ttSimple', desc: 'Fast T2V / I2V Prompt' },
  { key: 'manuscript', label: 'ttManuscript', desc: 'Article or Prepared Text' },
  { key: 'anchor', label: 'ttAnchor', desc: 'Digital Anchor with Audio' },
  { key: 'poetry', label: 'ttPoetry', desc: 'Poem to Video Clip' },
]

// v6.0/6.1 手动模式：暂停点选项（按任务类型）
const pausePointOptions: Record<string, { key: string; label: string }[]> = {
  creative: [
    { key: 'image_analysis', label: 'cpImageAnalysis' },
    { key: 'story', label: 'cpStory' },
    { key: 'script', label: 'cpScript' },
    { key: 'character_ref', label: 'cpCharacterRef' },
    { key: 'end_frame_prompts', label: 'cpEndFramePrompts' },
    { key: 'end_frame_gen', label: 'cpEndFrameGen' },
    { key: 'videos', label: 'cpVideos' },
    { key: 'audio', label: 'cpAudio' },
    { key: 'subtitle', label: 'cpSubtitle' },
    { key: 'final', label: 'cpFinal' },
  ],
  manuscript: [
    { key: 'scenes', label: 'cpScenes' },
    { key: 'keyframes', label: 'cpKeyframes' },
    { key: 'videos', label: 'cpVideos' },
    { key: 'audio', label: 'cpAudio' },
    { key: 'subtitle', label: 'cpSubtitle' },
    { key: 'final', label: 'cpFinal' },
  ],
  poetry: [
    { key: 'scenes', label: 'cpScenes' },
    { key: 'keyframes', label: 'cpKeyframes' },
    { key: 'videos', label: 'cpVideos' },
    { key: 'audio', label: 'cpAudio' },
    { key: 'subtitle', label: 'cpSubtitle' },
    { key: 'final', label: 'cpFinal' },
  ],
  anchor: [
    { key: 'scenes', label: 'cpScenes' },
    { key: 'references', label: 'cpReferences' },
    { key: 'videos', label: 'cpVideos' },
    { key: 'audio', label: 'cpAudio' },
    { key: 'subtitle', label: 'cpSubtitle' },
    { key: 'final', label: 'cpFinal' },
  ],
}

// 手动模式支持的任务类型（simple/simple_image 不支持暂停，PRD §4.3）
const manualSupported = computed(() => !['simple', 'image'].includes(appState.createTaskType))

// 当前任务类型可选的暂停点
const currentPausePoints = computed(() => pausePointOptions[appState.createTaskType] || [])

// 默认暂停点（PRD §4.8 预填，用户可增删）
const defaultPausePoints: Record<string, string[]> = {
  creative: ['story', 'script', 'character_ref', 'videos', 'subtitle'],
  manuscript: ['scenes', 'keyframes', 'videos', 'subtitle'],
  poetry: ['scenes', 'keyframes', 'videos', 'subtitle'],
  anchor: ['scenes', 'videos'],
}

function switchTaskType(type: string) {
  trackEvent('ui_action', { action: 'switch_task_type', type })
  appState.createTaskType = type
  appState.pausePoints = [...(defaultPausePoints[type] || [])]
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
    appState.pausePoints = [...(defaultPausePoints[appState.createTaskType] || [])]
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- 1. Task Type Selector (Top Studio Row) -->
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

      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <button
          v-for="tt in taskTypes"
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
                <!-- Creative -->
                <svg v-if="tt.key === 'creative'" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M4 6h8a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2z" />
                </svg>
                <!-- Simple -->
                <svg v-else-if="tt.key === 'simple'" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <!-- Manuscript -->
                <svg v-else-if="tt.key === 'manuscript'" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <!-- Anchor -->
                <svg v-else-if="tt.key === 'anchor'" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                <!-- Poetry -->
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
              {{ t(tt.label) }}
            </div>
          </div>
          <div class="text-[11px] text-muted leading-tight mt-1">
            {{ tt.desc }}
          </div>
        </button>
      </div>
    </div>

    <!-- 2. Execution Pipeline Toolbar (Compact & Progressive) -->
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

      <!-- Manual Pause Point Badges -->
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
            <span>{{ t(p.label) }}</span>
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
  </div>
</template>
