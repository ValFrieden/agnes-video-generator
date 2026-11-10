<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { t } from '@/i18n'
import { useTheme } from '@/composables/useTheme'
import { useToast } from '@/composables/useToast'
import { useConfig } from '@/composables/useConfig'
import { useVoice } from '@/composables/useVoice'
import { useTasks } from '@/composables/useTasks'
import { useProgress } from '@/composables/useProgress'
import { useNavigation } from '@/composables/useNavigation'
import { useGallery } from '@/composables/useGallery'
import { appState } from '@/store'
import SettingsModal from '@/components/SettingsModal.vue'
import CreatePanel from '@/components/CreatePanel.vue'
import SimplePanel from '@/components/SimplePanel.vue'
import TaskListPanel from '@/components/TaskListPanel.vue'
import GalleryPanel from '@/components/GalleryPanel.vue'
import KnowledgePanel from '@/components/KnowledgePanel.vue'
import ProgressPage from '@/components/ProgressPage.vue'
import VoicePickerModal from '@/components/VoicePickerModal.vue'
import Toast from '@/components/Toast.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import LangSwitcher from '@/components/shared/LangSwitcher.vue'

const { themeIcon, themeLabel, cycleTheme } = useTheme()
const { visible: toastVisible, message: toastMessage, type: toastType } = useToast()
const { loadModels, renderWorkspaces } = useConfig()
const { initVoiceSelector } = useVoice()
const { loadTaskList, startTaskListTimer, stopTaskListTimer } = useTasks()
const { parseHash } = useNavigation()
const { loadGallery, startGalleryTimer, stopGalleryTimer } = useGallery()

const showSettings = ref(false)

function switchMainTab(tab: 'create' | 'list' | 'simple' | 'gallery' | 'knowledge') {
  appState.view = tab
  location.hash =
    tab === 'list'
      ? '#/list'
      : tab === 'simple'
      ? '#/simple'
      : tab === 'gallery'
      ? '#/gallery'
      : tab === 'knowledge'
      ? '#/knowledge'
      : '#/create'
  if (tab === 'list') {
    loadTaskList()
    startTaskListTimer()
    stopGalleryTimer()
  } else if (tab === 'gallery') {
    loadGallery()
    startGalleryTimer()
    stopTaskListTimer()
  } else {
    stopTaskListTimer()
    stopGalleryTimer()
  }
}

function applyHashRoute() {
  const parsed = parseHash()
  if (parsed.view === appState.view) {
    if (parsed.view === 'progress' && parsed.taskId && parsed.taskId !== appState.progressTaskId) {
      appState.progressTaskId = parsed.taskId
      appState.currentTaskId = parsed.taskId
    }
    return
  }
  if (parsed.view === 'progress' && parsed.taskId) {
    appState.view = 'progress'
    appState.progressTaskId = parsed.taskId
    appState.currentTaskId = parsed.taskId
    return
  }
  appState.view = parsed.view
  appState.progressTaskId = null
  if (parsed.view === 'gallery') {
    loadGallery()
    startGalleryTimer()
    stopTaskListTimer()
  } else if (parsed.view === 'list') {
    loadTaskList()
    startTaskListTimer()
    stopGalleryTimer()
  } else {
    stopTaskListTimer()
    stopGalleryTimer()
  }
}

const isConfigLoaded = ref(false)

onMounted(async () => {
  const parsed = parseHash()
  if (parsed.view === 'progress' && parsed.taskId) {
    appState.view = 'progress'
    appState.progressTaskId = parsed.taskId
    appState.currentTaskId = parsed.taskId
  } else {
    appState.view = parsed.view
    if (parsed.view === 'gallery') {
      loadGallery()
      startGalleryTimer()
    } else if (parsed.view === 'list') {
      loadTaskList()
      startTaskListTimer()
    }
  }

  try {
    const cfg = await fetch('/api/config').then((r) => r.json())
    if (cfg.api_key) {
      appState.apiKeySource = cfg.source
    }
    if (cfg.app_version) {
      appState.appVersion = cfg.app_version
    }
    await renderWorkspaces()
    if (cfg.watermark !== undefined) {
      appState.watermarkEnabled = !!cfg.watermark.enabled
    }
    if (cfg.agnes_domain) {
      appState.agnesDomain = cfg.agnes_domain
    }
    await loadModels()
    isConfigLoaded.value = true
  } catch (e) {
    console.error('init config load error:', e)
  }

  try {
    await initVoiceSelector()
  } catch (e) {
    console.error('init voice selector error:', e)
  }

  if (appState.view === 'create') {
    autoReconnectRunningTask()
  }

  window.addEventListener('hashchange', applyHashRoute)
})

onUnmounted(() => {
  window.removeEventListener('hashchange', applyHashRoute)
})

async function autoReconnectRunningTask() {
  const h = location.hash || ''
  // Wenn der Nutzer explizit #/create aufgerufen hat, nicht zwangsweise entführen
  if (h === '#/create') return
  try {
    const d = await fetch('/api/tasks').then((r) => r.json())
    const running = (d.tasks || []).find((t: any) => t.status === 'running' || t.status === 'queued')
    if (running) {
      appState.currentTaskType = running.task_type || 'creative'
      appState.currentDirName = running.dir_name || running.task_id
      appState.progressTaskId = running.task_id
      appState.progressOrigin = 'create'
      appState.view = 'progress'
      location.hash = '#/progress/' + encodeURIComponent(running.task_id)
    }
  } catch {
    /* ignore */
  }
}
</script>

<template>
  <ProgressPage v-if="appState.view === 'progress'" />

  <div v-else class="min-h-screen flex flex-col bg-paper text-ink">
    <!-- Top Navigation Bar -->
    <header class="sticky top-0 z-40 border-b border-rule/50 bg-paper/85 backdrop-blur-md">
      <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        <!-- Logo / Title -->
        <div class="flex items-center gap-3 shrink-0">
          <div class="w-9 h-9 rounded-xl bg-paper-2 border border-rule flex items-center justify-center text-accent">
            <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <rect x="2" y="4" width="20" height="16" rx="2.5" stroke-width="1.8" />
              <path d="M7 4v16M17 4v16M2 8h20M2 16h20" stroke-width="1.8" stroke-linecap="round" />
            </svg>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h1 class="font-bold text-base sm:text-lg tracking-tight text-ink">Agnes Studio</h1>
              <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-accent/15 text-accent border border-accent/25">AI Video</span>
            </div>
            <p class="text-[11px] text-muted hidden sm:block -mt-0.5">{{ t('subtitle') }}</p>
          </div>
        </div>

        <!-- Center Main Tabs (Clean Studio Segmented Track) -->
        <nav class="hidden md:flex items-center gap-1 p-1 rounded-xl bg-paper-2 border border-rule text-xs font-medium">
          <button
            class="px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
            :class="appState.view === 'create' ? 'bg-paper-3 text-ink font-semibold border border-rule' : 'text-muted hover:text-ink'"
            @click="switchMainTab('create')"
          >
            <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M4 6h8a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2z" />
            </svg>
            <span>{{ t('tabCreate') }}</span>
          </button>
          <button
            class="px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
            :class="appState.view === 'simple' ? 'bg-paper-3 text-ink font-semibold border border-rule' : 'text-muted hover:text-ink'"
            @click="switchMainTab('simple')"
          >
            <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>{{ t('tabSimple') }}</span>
          </button>
          <button
            class="px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
            :class="appState.view === 'list' ? 'bg-paper-3 text-ink font-semibold border border-rule' : 'text-muted hover:text-ink'"
            @click="switchMainTab('list')"
          >
            <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
            <span>{{ t('tabList') }}</span>
          </button>
          <button
            class="px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
            :class="appState.view === 'gallery' ? 'bg-paper-3 text-ink font-semibold border border-rule' : 'text-muted hover:text-ink'"
            @click="switchMainTab('gallery')"
          >
            <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>{{ t('tabGallery') }}</span>
          </button>
          <button
            class="px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
            :class="appState.view === 'knowledge' ? 'bg-paper-3 text-ink font-semibold border border-rule' : 'text-muted hover:text-ink'"
            @click="switchMainTab('knowledge')"
          >
            <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span>{{ t('tabKnowledge') }}</span>
          </button>
        </nav>

        <!-- Right Action Tools -->
        <div class="flex items-center gap-2 shrink-0">
          <!-- API Status Pill -->
          <button
            class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition cursor-pointer"
            :class="
              appState.apiKeySource
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20'
            "
            :title="appState.apiKeySource ? t('apiKeyConfigured') : t('apiKeyNotConfigured')"
            @click="showSettings = true"
          >
            <span class="w-2 h-2 rounded-full" :class="appState.apiKeySource ? 'bg-emerald-500' : 'bg-amber-500'"></span>
            <span class="hidden lg:inline">{{ appState.apiKeySource ? t('apiKeyConfigured') : t('apiKeyNotConfigured') }}</span>
          </button>

          <!-- Settings Button -->
          <button
            class="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-ink-2 hover:text-ink hover:bg-paper-2 rounded-lg border border-rule/50 transition cursor-pointer"
            :title="t('advancedSettings')"
            @click="showSettings = true"
          >
            <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span class="hidden sm:inline">{{ t('advancedSettings') }}</span>
          </button>

          <!-- Theme -->
          <button
            class="flex items-center gap-1 px-2.5 py-1.5 text-xs text-ink-2 hover:text-ink hover:bg-paper-2 rounded-lg border border-rule/50 transition cursor-pointer"
            :title="themeLabel"
            :aria-label="themeLabel"
            @click="cycleTheme"
          >
            <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" :d="themeIcon"></path>
            </svg>
          </button>

          <!-- Language Switcher -->
          <LangSwitcher />
        </div>
      </div>

      <!-- Mobile Sub-navigation Tabs -->
      <div class="flex md:hidden overflow-x-auto px-4 py-2 gap-1.5 border-t border-rule/40 bg-paper-2">
        <button
          v-for="item in [
            { key: 'create', label: t('tabCreate') },
            { key: 'simple', label: t('tabSimple') },
            { key: 'list', label: t('tabList') },
            { key: 'gallery', label: t('tabGallery') },
            { key: 'knowledge', label: t('tabKnowledge') },
          ]"
          :key="item.key"
          class="px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition"
          :class="appState.view === item.key ? 'bg-paper-3 text-ink font-semibold border border-rule' : 'text-muted hover:text-ink'"
          @click="switchMainTab(item.key as any)"
        >
          <span>{{ item.label }}</span>
        </button>
      </div>
    </header>

    <!-- Main Workspace Container -->
    <main class="flex-1 max-w-6xl w-full mx-auto px-4 py-6">
      <!-- Quick Resource Bar -->
      <div class="flex items-center justify-between flex-wrap gap-2 mb-6 px-1 text-xs text-muted">
        <div class="flex items-center gap-2">
          <span class="inline-block w-1.5 h-1.5 rounded-full bg-accent"></span>
          <span>{{ t('subtitle') }}</span>
        </div>
        <div class="flex items-center gap-3">
          <a href="https://video.lichuanyang.top/demo" target="_blank" rel="noopener" class="hover:text-ink transition">Demo</a>
          <span class="text-rule">·</span>
          <a href="https://video.lichuanyang.top/guides/prompt-tips" target="_blank" rel="noopener" class="hover:text-ink transition">Guides</a>
          <span class="text-rule">·</span>
          <a href="https://video.lichuanyang.top/faq" target="_blank" rel="noopener" class="hover:text-ink transition">FAQ</a>
          <span class="text-rule">·</span>
          <a href="https://github.com/lcy362/agnes-video-generator" target="_blank" rel="noopener" class="hover:text-ink transition">GitHub</a>
        </div>
      </div>

      <!-- View Panels -->
      <div v-show="appState.view === 'create'">
        <CreatePanel @open-settings="showSettings = true" />
      </div>

      <div v-show="appState.view === 'simple'">
        <SimplePanel @go-list="switchMainTab('list')" />
      </div>

      <div v-show="appState.view === 'list'">
        <TaskListPanel />
      </div>

      <div v-show="appState.view === 'gallery'">
        <GalleryPanel />
      </div>

      <div v-show="appState.view === 'knowledge'">
        <KnowledgePanel />
      </div>
    </main>

    <!-- Clean Footer -->
    <footer class="border-t border-rule/40 bg-paper-2/40 py-6 mt-12 text-center text-xs text-muted">
      <div class="max-w-4xl mx-auto px-4">
        <div class="flex justify-center flex-wrap gap-x-5 gap-y-2 mb-3">
          <a href="https://video.lichuanyang.top" target="_blank" rel="noopener" class="hover:text-ink transition">{{ t('projectHome') }}</a>
          <a href="https://video.lichuanyang.top/demo" target="_blank" rel="noopener" class="text-accent hover:underline transition">{{ t('onlineDemo') }}</a>
          <a href="https://video.lichuanyang.top/guides/prompt-tips" target="_blank" rel="noopener" class="hover:text-ink transition">{{ t('usageGuide') }}</a>
          <a href="https://video.lichuanyang.top/faq" target="_blank" rel="noopener" class="hover:text-ink transition">{{ t('faqTitle') }}</a>
          <a href="https://video.lichuanyang.top/api-docs" target="_blank" rel="noopener" class="hover:text-ink transition">{{ t('apiDocs') }}</a>
          <a href="https://github.com/lcy362/agnes-video-generator" target="_blank" rel="noopener" class="hover:text-ink transition">GitHub ⭐</a>
        </div>
        <p v-if="appState.appVersion" class="text-[11px] text-muted/60">
          {{ t('footerVersion') }} v{{ appState.appVersion }} · Agnes Video Generator
        </p>
      </div>
    </footer>
  </div>

  <!-- Settings Modal (House ConfigPanel) -->
  <SettingsModal v-model:visible="showSettings" />

  <!-- Voice Picker Modal -->
  <VoicePickerModal />

  <!-- Toast / Confirm -->
  <Toast :visible="toastVisible" :message="toastMessage" :type="toastType" />
  <ConfirmModal />
</template>
