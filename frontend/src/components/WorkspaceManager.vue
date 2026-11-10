<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { t } from '@/i18n'
import { appState, getCollapsePrefs, setCollapsePref } from '@/store'
import { useConfig } from '@/composables/useConfig'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()

const collapsed = reactive(getCollapsePrefs())
function toggleConfigPanel(section: string) {
  collapsed[section] = !collapsed[section]
  setCollapsePref(section, collapsed[section])
}

const {
  isRegression,
  wsDisplayName,
  renderWorkspaces,
  activateWorkspace,
  removeWorkspaceEntry,
  browseDirectory,
  addWorkspace,
} = useConfig()

const workspacePath = ref('')
const workspaceName = ref('')

async function onBrowse() {
  const p = await browseDirectory()
  if (p) workspacePath.value = p
}
async function onAddWorkspace() {
  await addWorkspace(workspacePath.value, workspaceName.value)
  workspacePath.value = ''
  workspaceName.value = ''
}

onMounted(async () => {
  await renderWorkspaces()
})
</script>

<template>
  <!-- 工作目录 -->
  <div class="glass-card rounded-2xl mb-6 overflow-hidden transition-all duration-300">
    <button
      v-if="collapsed.workspace"
      type="button"
      class="w-full flex items-center justify-between px-6 py-3 cursor-pointer hover:bg-paper-3 transition text-left"
      :aria-expanded="!collapsed.workspace"
      @click="toggleConfigPanel('workspace')"
    >
      <div class="flex items-center gap-3">
        <svg class="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>
        <span class="text-sm text-muted">
          <span class="text-ink-2 font-medium">{{ t('workspaceTitle') }}</span>
          <span class="text-muted mx-2">·</span>
          <span :class="appState.activeWorkspace ? 'text-success' : 'text-muted'">
            {{ appState.activeWorkspace ? (appState.workspaces.find((w) => w.path === appState.activeWorkspace)?.name || appState.activeWorkspace) : t('workspaceNone') }}
          </span>
        </span>
      </div>
      <svg class="w-4 h-4 text-muted shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
    </button>
    <div v-else class="p-6 pt-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-lg font-semibold text-accent">{{ t('workspaceTitle') }}</h2>
        <div class="flex items-center gap-2">
          <span :class="appState.activeWorkspace ? 'badge-success' : 'text-xs px-2 py-1 rounded-full bg-paper-2 text-muted'">
            {{ appState.activeWorkspace ? t('workspaceActive') : t('workspaceNone') }}
          </span>
          <button
            class="text-xs text-muted hover:text-ink-2 transition px-2 py-1 rounded cursor-pointer"
            :aria-label="t('collapse')"
            :aria-expanded="!collapsed.workspace"
            @click="toggleConfigPanel('workspace')"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
          </button>
        </div>
      </div>
      <div v-if="isRegression" class="mb-3 text-xs text-accent bg-accent/15 rounded-lg px-3 py-2">{{ t('workspaceRegressionHint') }}</div>
      <div v-if="appState.activeWorkspace" class="mb-3 glass-input rounded-lg px-4 py-2.5">
        <p class="text-xs text-muted mb-0.5">{{ t('workspaceCurrentActive') }}</p>
        <p class="text-sm text-success font-medium">{{ appState.workspaces.find((w) => w.path === appState.activeWorkspace)?.name || appState.activeWorkspace }}</p>
        <p class="text-xs text-muted font-mono truncate">{{ appState.activeWorkspace }}</p>
      </div>
      <div class="flex gap-3 mb-4">
        <input v-model="workspacePath" :placeholder="t('workspacePathPlaceholder')" readonly class="flex-1 glass-input rounded-lg px-4 py-2.5 text-sm text-ink placeholder-muted" />
        <input v-model="workspaceName" :placeholder="t('workspaceNamePlaceholder')" class="w-40 glass-input rounded-lg px-4 py-2.5 text-sm text-ink placeholder-muted" />
        <button class="px-4 py-2.5 bg-paper-3 hover:bg-paper-3 rounded-lg text-sm font-medium transition" @click="onBrowse">{{ t('workspaceBrowse') }}</button>
        <button class="px-5 py-2.5 bg-accent text-accent-ink hover:bg-accent/90 rounded-lg text-sm font-medium transition" @click="onAddWorkspace">{{ t('workspaceAdd') }}</button>
      </div>
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-sm font-medium text-muted">{{ t('workspaceListTitle') }}</h3>
        <span class="text-xs text-muted">{{ t('workspaceListHint') }}</span>
      </div>
      <div class="space-y-2">
        <div
          v-for="ws in appState.workspaces"
          :key="ws.path"
          class="flex items-center justify-between glass-input rounded-lg px-4 py-2.5"
        >
          <div class="flex-1 min-w-0">
            <p class="text-sm text-ink truncate">{{ wsDisplayName(ws) }}</p>
            <p class="text-xs text-muted font-mono truncate">{{ ws.path }}</p>
          </div>
          <div class="flex gap-2 ml-3">
            <span v-if="ws.path === appState.activeWorkspace" class="badge-success">{{ t('workspaceActiveBadge') }}</span>
            <button v-else class="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded-lg text-xs font-medium transition" @click="activateWorkspace(ws.path)">
              {{ t('workspaceActivate') }}
            </button>
            <button v-if="!ws.is_default" class="btn-danger text-xs px-3 py-1 font-medium" @click="removeWorkspaceEntry(ws.path)">
              {{ t('workspaceRemove') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

</template>