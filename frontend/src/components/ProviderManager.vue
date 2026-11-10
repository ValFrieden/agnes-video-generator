<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { t } from '@/i18n'
import { appState, getCollapsePrefs, setCollapsePref } from '@/store'
import { useConfig } from '@/composables/useConfig'
import { useVoice } from '@/composables/useVoice'
import { useGa } from '@/composables/useGa'
import { useVideoModelCaps } from '@/composables/useVideoModelCaps'
import { useToast } from '@/composables/useToast'
import { useModalA11y } from '@/composables/useModalA11y'
import ProviderIntro from '@/components/shared/ProviderIntro.vue'

const props = defineProps<{ collapsed: boolean }>()
const emit = defineEmits<{ (e: 'toggle'): void }>()

const { trackEvent, isGaOptedOut, setGaOptOut } = useGa()
const { showToast } = useToast()

const gaOptOut = ref(isGaOptedOut())
function toggleGaOptOut() {
  setGaOptOut(gaOptOut.value)
}
const {
  apiKeyStatus,
  keyCount,
  keySource,
  keyList,
  saveMultiKeys,
  loadKeyInfo,
  removeKey,
  saveKeyDomain,
  detectKeyDomains,
  detectingKeys,
  clearApiKey,
  modelSyncStatus,
  modelSaveStatus,
  modelErrorMsg,
  betaHintVisible,
  isBetaModel,
  isPaidModel,
  syncModels,
  saveModels,
  providerName,
  providerApi,
  providerBaseUrl,
  providerApiKey,
  providerTestBusy,
  providerSaveStatus,
  providerErrorMsg,
  loadTextProviders,
  saveTextProvider,
  deleteTextProvider,
  testTextProvider,
  domainSaveStatus,
  domainErrorMsg,
  saveDomain,
  toggleWatermark,
  isRegression,
  wsDisplayName,
  renderWorkspaces,
  activateWorkspace,
  removeWorkspaceEntry,
  modelSyncStatus: _ms,
} = useConfig()

const { initVoiceSelector } = useVoice()
const vmCaps = useVideoModelCaps()

const collapsed = reactive(getCollapsePrefs())
function toggleConfigPanel(section: string) {
  collapsed[section] = !collapsed[section]
  setCollapsePref(section, collapsed[section])
}

const DOMAIN_ENTRIES = [
  { key: 'com', labelKey: 'domainCom', url: 'https://api.agnes-ai.com' },
  { key: 'cn', labelKey: 'domainCn', url: 'https://api.agnes-ai.cn' },
]

const apiKeyInput = ref('')
const hasApiKey = computed(() => apiKeyStatus.value !== 'none')

function modelDisplayLabel(m: string): string {
  return m
}

async function onSaveApiKey() {
  try {
    await saveMultiKeys(apiKeyInput.value)
    apiKeyInput.value = ''
    await loadKeyInfo()
    showToast(t('apiKeySaved'), 3000, 'success')
  } catch (e: any) {
    showToast(t('failSave') + ': ' + (e?.message || ''), 4000, 'error')
  }
}

function domainEntry(root = appState.agnesDomain) {
  return DOMAIN_ENTRIES.find((d) => d.key === root) || DOMAIN_ENTRIES[0]
}
function displayDomain(root?: string) {
  return domainEntry(root).url
}
function keyDomainUrl(domain?: string) {
  if (!domain) return ''
  const e = DOMAIN_ENTRIES.find((d) => d.key === domain)
  return e ? e.url : ''
}
function agnesApiKeyText(): string {
  if (keyCount.value === 0) return t('apiKeyNotConfigured')
  return `${keyCount.value} key(s) (${keySource.value})`
}

function providerDisplayName(p: any): string {
  return p.display_name || p.provider
}
function providerApiLabel(p: any): string {
  return p.api_type === 'openai-completions' ? t('providerApiOpenai') : t('providerApiAnthropic')
}

const manageProviders = computed(() => {
  const list = [...(appState.textProviders || [])]
  const hasAgnes = list.some((p: any) => p.builtin || p.provider === 'agnes')
  if (!hasAgnes) {
    list.unshift({ provider: 'agnes', display_name: 'Agnes', api: 'openai-completions', base_url: '', api_key: '', models: [], builtin: true })
  }
  return list
})

async function onKeyDomainChange(item: any, domain: string) {
  try {
    await saveKeyDomain(item.id, domain)
    await loadKeyInfo()
  } catch (e: any) {
    showToast(t('failSave') + ': ' + (e?.message || ''), 4000, 'error')
  }
}

const editingProvider = ref<null | string>(null)
const showProviderModal = ref(false)
const modelItems = ref<string[]>([])
const modelInput = ref('')

const isEditCustom = computed(() => editingProvider.value !== null && editingProvider.value !== 'agnes')
const modalTitle = computed(() => {
  if (editingProvider.value === 'agnes') return t('providerEditAgnes')
  if (editingProvider.value === null) return t('providerAddTitle')
  return t('providerEditTitle')
})

function addModelItem(value: string) {
  const v = value.trim()
  if (!v) return
  if (!modelItems.value.includes(v)) modelItems.value.push(v)
  modelInput.value = ''
}
function onAddModel() {
  addModelItem(modelInput.value)
}
function removeModelItem(idx: number) {
  modelItems.value.splice(idx, 1)
}
function resetProviderForm() {
  providerName.value = ''
  providerApi.value = 'openai-completions'
  providerBaseUrl.value = ''
  providerApiKey.value = ''
  modelItems.value = []
  modelInput.value = ''
}
function openAddProvider() {
  editingProvider.value = null
  resetProviderForm()
  showProviderModal.value = true
}
function openEditProvider(p: any) {
  if (p.provider === 'agnes') {
    editingProvider.value = 'agnes'
  } else {
    editingProvider.value = p.provider
    providerName.value = p.display_name || p.provider
    providerApi.value = p.api_type || 'openai-completions'
    providerBaseUrl.value = p.base_url || ''
    providerApiKey.value = p.api_key || ''
    modelItems.value = [...(p.models || [])]
  }
  showProviderModal.value = true
}

async function onFetchProviderModels() {
  providerTestBusy.value = true
  try {
    const res = await testTextProvider({ base_url: providerBaseUrl.value, api_key: providerApiKey.value, api: providerApi.value })
    if (res && res.length) {
      res.forEach((m: string) => addModelItem(m))
    }
  } catch (e: any) {
    showToast(t('failLoad') + ': ' + (e?.message || ''), 4000, 'error')
  } finally {
    providerTestBusy.value = false
  }
}

function slugifyProvider(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

async function onSaveProvider() {
  try {
    if (editingProvider.value === 'agnes') {
      await saveDomain()
    } else {
      await saveTextProvider({
        provider: editingProvider.value || slugifyProvider(providerName.value),
        display_name: providerName.value,
        api: providerApi.value,
        base_url: providerBaseUrl.value,
        api_key: providerApiKey.value,
        models_json: JSON.stringify(modelItems.value),
      })
    }
    showProviderModal.value = false
    await loadTextProviders()
    showToast(t('providerSaved'), 3000, 'success')
  } catch (e: any) {
    showToast(t('failSave') + ': ' + (e?.message || ''), 4000, 'error')
  }
}

async function onDeleteProvider(id: string) {
  if (!confirm(t('deleteProviderConfirm'))) return
  try {
    await deleteTextProvider(id)
    await loadTextProviders()
    showToast(t('deletedTask'), 3000, 'success')
  } catch (e: any) {
    showToast(t('failDelete') + ': ' + (e?.message || ''), 4000, 'error')
  }
}

const { containerRef: providerModalRef } = useModalA11y(showProviderModal, () => (showProviderModal.value = false))

onMounted(async () => {
  await loadKeyInfo()
  await loadTextProviders()
})

defineExpose({ openAddProvider })
</script>

<template>
  <!-- 供应商管理 -->
  <div class="glass-card rounded-2xl mb-6 overflow-hidden transition-all duration-300">
    <button
      v-if="props.collapsed"
      type="button"
      class="w-full flex items-center justify-between px-6 py-3 cursor-pointer hover:bg-paper-3 transition text-left"
      :aria-expanded="!props.collapsed"
      @click="emit('toggle')"
    >
      <div class="flex items-center gap-3">
        <svg class="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
        <span class="text-sm text-muted">
          <span class="text-ink-2 font-medium">{{ t('providerManageTitle') }}</span>
          <span class="text-muted mx-2">·</span>
          <span class="text-muted tabular-nums">{{ manageProviders.length }}</span>
        </span>
      </div>
      <svg class="w-4 h-4 text-muted shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
    </button>
    <div v-else class="p-6 pt-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-lg font-semibold text-accent">{{ t('providerManageTitle') }}</h2>
        <div class="flex items-center gap-3">
          <button class="text-xs text-accent hover:text-ink transition whitespace-nowrap cursor-pointer" @click="openAddProvider()">
            {{ t('providerAddBtn') }}
          </button>
          <button
            class="text-xs text-muted hover:text-ink-2 transition px-2 py-1 rounded cursor-pointer"
            :aria-label="t('collapse')"
            :aria-expanded="!props.collapsed"
            @click="emit('toggle')"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
          </button>
        </div>
      </div>
      <p class="text-xs text-muted mb-4">{{ t('providerManageHint') }}</p>

      <ProviderIntro />

      <!-- 供应商列表：agnes（内置）+ 自定义 -->
      <div class="space-y-2">
        <div
          v-for="p in manageProviders"
          :key="p.provider"
          class="flex items-center justify-between glass-input rounded-lg px-4 py-2.5"
        >
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <p class="text-sm text-ink font-medium truncate">{{ providerDisplayName(p) }}</p>
              <span v-if="p.builtin" class="badge-success">{{ t('providerBuiltin') }}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded bg-paper-3 text-muted">{{ providerApiLabel(p) }}</span>
              <span
                v-if="p.provider === (appState.models.text_provider || 'agnes')"
                class="badge-info"
              >{{ t('providerInUse') }}</span>
            </div>
            <p class="text-xs text-muted font-mono truncate mt-0.5">
              {{ p.provider === 'agnes' ? displayDomain() : (p.base_url || '-') }}
            </p>
            <p class="text-xs text-muted font-mono truncate">
              <template v-if="p.provider === 'agnes'">{{ agnesApiKeyText() }}</template>
              <template v-else>{{ t('providerApiKeyLabel') }}: {{ p.api_key || '-' }}</template>
            </p>
          </div>
          <div class="flex items-center gap-2 ml-3">
            <button
              class="px-3 py-1 bg-blue-600/80 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition"
              @click="openEditProvider(p)"
            >{{ t('providerEditLabel') }}</button>
            <button
              v-if="!p.builtin"
              class="btn-danger text-xs px-3 py-1 font-medium"
              @click="onDeleteProvider(p.provider)"
            >{{ t('delete') }}</button>
            <span v-else class="text-muted/50" :title="t('providerBuiltinHint')">•</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 新增 / 编辑供应商弹窗 -->
  <teleport to="body">
    <div
      v-if="showProviderModal"
      ref="providerModalRef"
      class="fixed inset-0 z-[60] flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      :aria-label="modalTitle"
    >
      <div class="absolute inset-0 bg-black/40" @click="showProviderModal = false"></div>
      <div class="relative bg-paper rounded-2xl p-6 max-w-lg w-full mx-4 shadow-2xl border border-rule max-h-[85vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-semibold text-ink">{{ modalTitle }}</h3>
          <button
            class="text-muted hover:text-ink-2 transition p-1"
            :aria-label="t('cancel')"
            @click="showProviderModal = false"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <template v-if="editingProvider === 'agnes'">
          <div class="flex items-center gap-2 mb-5">
            <span class="text-sm font-semibold text-ink-2">Agnes</span>
            <span class="badge-success">{{ t('providerBuiltin') }}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-paper-3 text-muted">{{ t('providerEditReadonly') }}</span>
          </div>

          <!-- 域名 -->
          <div class="mb-6">
            <p class="text-sm font-medium text-ink-2 mb-1">{{ t('domainTitle') }}</p>
            <p class="text-xs text-muted mb-3">{{ t('domainHint') }}</p>
            <div class="space-y-2">
              <label v-for="d in DOMAIN_ENTRIES" :key="d.key" class="flex items-center gap-3 glass-input rounded-lg px-4 py-3 cursor-pointer hover:border-blue-500/40 transition">
                <input v-model="appState.agnesDomain" type="radio" name="agnes-domain-modal" :value="d.key" class="accent-blue-500 w-4 h-4 cursor-pointer" />
                <div>
                  <span class="text-sm text-ink-2 font-medium">{{ d.url }}</span>
                  <span class="text-xs text-muted ml-2">{{ t(d.labelKey) }}</span>
                </div>
              </label>
            </div>
            <div class="flex items-center gap-3 mt-3">
              <button class="px-4 py-2 bg-accent text-accent-ink hover:bg-accent/90 rounded-lg text-sm font-medium transition" @click="saveDomain">{{ t('save') }}</button>
              <span v-if="domainSaveStatus === 'ok'" class="text-xs text-success">{{ t('domainSaved') }}</span>
              <span v-if="domainSaveStatus === 'error'" class="text-xs text-danger">{{ domainErrorMsg }}</span>
            </div>
          </div>

          <!-- API Key -->
          <div>
            <p class="text-sm font-medium text-ink-2 mb-1">{{ t('apiKeyTitle') }}</p>
            <div class="flex gap-3 items-start">
              <textarea
                v-model="apiKeyInput"
                rows="2"
                :placeholder="hasApiKey ? t('apiKeyAppendPlaceholder') : t('apiKeyPlaceholder')"
                class="flex-1 glass-input rounded-lg px-4 py-2.5 text-sm text-ink placeholder-muted resize-y"
              ></textarea>
              <button class="px-5 py-2.5 bg-accent text-accent-ink hover:bg-accent/90 rounded-lg text-sm font-medium transition whitespace-nowrap" @click="onSaveApiKey">{{ hasApiKey ? t('addKey') : t('save') }}</button>
              <button v-if="apiKeyStatus !== 'none'" class="btn-danger text-sm px-5 py-2.5 font-medium whitespace-nowrap" @click="clearApiKey">{{ t('clear') }}</button>
            </div>
            <div v-if="keyCount > 0" class="mt-2 flex items-center gap-2 flex-wrap">
              <span class="badge-success">{{ t('keyCountLabel') }}: {{ keyCount }} <span class="opacity-70">({{ keySource }})</span></span>
              <span v-if="keyCount > 1" class="badge-info" :title="t('multiKeyHint')">{{ t('multiKeyActive') }}</span>
            </div>
            <div v-if="keyList.length > 0" class="mt-3 space-y-1.5">
              <div v-for="(item, idx) in keyList" :key="item.id + idx" class="flex items-center gap-2 rounded-lg px-3 py-1.5 bg-paper-3/70 text-xs flex-wrap">
                <code class="flex-1 font-mono text-ink-2 truncate min-w-[8rem]">{{ item.mask }}</code>
                <span :class="item.source === 'env' ? 'badge-warning uppercase' : 'px-1.5 py-0.5 rounded text-[10px] uppercase bg-paper-3 text-muted'">{{ item.source === 'env' ? t('keySrcEnv') : t('keySrcConfig') }}</span>
                <span v-if="item.domain && keyDomainUrl(item.domain)" class="font-mono" :class="item.domain === 'cn' ? 'badge-success' : 'badge-info'">{{ keyDomainUrl(item.domain) }}</span>
                <span v-else-if="item.source === 'env'" class="px-1.5 py-0.5 rounded text-[10px] font-mono text-muted bg-paper-3" :title="t('keySrcEnvHint')">{{ t('keyDomainEnvFollow') }}（{{ displayDomain() }}）</span>
                <span v-else class="badge-warning" :title="t('keyDomainNotSetHint')">{{ t('keyDomainNotSet') }}</span>
                <label v-if="item.persistable" :for="'key-domain-select-' + item.id" class="sr-only">{{ t('keyDomainSelectTitle') }}</label>
                <select :id="'key-domain-select-' + item.id" v-if="item.persistable" :value="item.domain || ''" class="glass-input rounded px-1.5 py-0.5 text-[10px] text-ink cursor-pointer" :title="t('keyDomainSelectTitle')" :aria-label="t('keyDomainSelectTitle')" @change="onKeyDomainChange(item, ($event.target as HTMLSelectElement).value)">
                  <option value="">{{ t('keyDomainAuto') }}（{{ displayDomain() }}）</option>
                  <option v-for="d in DOMAIN_ENTRIES" :key="d.key" :value="d.key">{{ d.url }}</option>
                </select>
                <button v-if="item.source !== 'env'" class="text-danger hover:opacity-80 transition flex items-center justify-center p-0.5" :title="t('removeKeyBtn')" @click="removeKey(item.id)">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
                <span v-else class="text-muted/50" :title="t('keySrcEnvHint')">•</span>
              </div>
              <div class="flex items-center gap-2 pt-1">
                <button class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-xs font-medium transition" :disabled="detectingKeys" @click="detectKeyDomains()">{{ detectingKeys ? t('detectKeysRunning') : t('detectKeysBtn') }}</button>
                <span class="text-xs text-muted">{{ t('detectKeysHint') }}</span>
              </div>
            </div>
            <div class="flex flex-wrap items-center gap-x-5 gap-y-1.5 mt-3 text-xs">
              <a href="https://platform.agnes-ai.com" target="_blank" rel="noopener" class="text-accent hover:text-ink transition-colors">{{ t('apiKeyGetLink') }}</a>
              <a href="https://video.lichuanyang.top/guides/api-key" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('apiKeyGuideLink') }}</a>
              <a href="https://video.lichuanyang.top/demo" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('apiKeyDemoLink') }}</a>
            </div>
          </div>

          <div class="flex justify-end mt-5">
            <button class="px-4 py-2 rounded-lg text-sm text-ink-2 bg-paper-3 hover:bg-paper-2 border border-rule transition" @click="showProviderModal = false">{{ t('close') }}</button>
          </div>
        </template>

        <template v-else>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-muted mb-1">{{ t('providerNameLabel') }}</label>
              <input v-model="providerName" :placeholder="t('providerNamePlaceholder')" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink placeholder-muted" />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">{{ t('providerApiLabel') }}</label>
              <select v-model="providerApi" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink">
                <option value="openai-completions">{{ t('providerApiOpenai') }}</option>
                <option value="anthropic-messages">{{ t('providerApiAnthropic') }}</option>
              </select>
            </div>
            <div class="sm:col-span-2">
              <label class="block text-xs text-muted mb-1">{{ t('providerBaseUrlLabel') }}</label>
              <input v-model="providerBaseUrl" :placeholder="t('providerBaseUrlPlaceholder')" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink placeholder-muted" />
            </div>
            <div>
              <label class="block text-xs text-muted mb-1">{{ t('providerApiKeyLabel') }}</label>
              <input v-model="providerApiKey" type="password" :placeholder="isEditCustom ? t('providerApiKeyEditPlaceholder') : t('providerApiKeyPlaceholder')" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink placeholder-muted" />
              <p v-if="isEditCustom" class="text-[10px] text-muted mt-0.5">{{ t('providerApiKeyEditHint') }}</p>
            </div>
            <div class="flex items-end">
              <button
                class="px-4 py-2.5 bg-green-600 hover:bg-green-500 text-white disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition whitespace-nowrap"
                :disabled="providerTestBusy"
                @click="onFetchProviderModels"
              >{{ providerTestBusy ? t('providerFetching') : t('providerFetchModels') }}</button>
            </div>
          </div>

          <div class="mt-3">
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-xs text-muted">{{ t('modelListLabel') }}</label>
              <span v-if="modelItems.length === 0" class="text-xs text-muted">{{ t('providerNoModels') }}</span>
            </div>
            <div v-if="modelItems.length > 0" class="space-y-1.5 mb-2">
              <div v-for="(m, idx) in modelItems" :key="m + idx" class="flex items-center gap-2 glass-input rounded-lg px-3 py-1.5">
                <span class="flex-1 min-w-0 font-mono text-xs text-ink truncate">{{ m }}</span>
                <button class="text-danger hover:opacity-80 transition p-1" :aria-label="t('delete')" @click="removeModelItem(idx)">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </div>
            <div class="flex gap-2">
              <input v-model="modelInput" class="flex-1 glass-input rounded-lg px-3 py-2 text-sm text-ink placeholder-muted font-mono" :placeholder="t('modelInputPlaceholder')" @keyup.enter.prevent="onAddModel()" />
              <button class="px-3 py-2 bg-blue-600/80 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition whitespace-nowrap" @click="onAddModel()">{{ t('modelAdd') }}</button>
            </div>
            <p class="text-[10px] text-muted mt-1">{{ t('modelInputHint') }}</p>
          </div>

          <div class="flex items-center gap-3 justify-end mt-6">
            <span v-if="providerSaveStatus === 'ok'" class="self-center text-xs text-success">{{ t('providerSaved') }}</span>
            <span v-if="providerSaveStatus === 'error'" class="self-center text-xs text-danger">{{ providerErrorMsg }}</span>
            <button class="px-4 py-2 rounded-lg text-sm text-ink-2 bg-paper-3 hover:bg-paper-2 border border-rule transition" @click="showProviderModal = false">{{ t('cancel') }}</button>
            <button class="px-5 py-2.5 bg-accent text-accent-ink hover:bg-accent/90 rounded-lg text-sm font-medium transition" @click="onSaveProvider">{{ t('save') }}</button>
          </div>
        </template>
      </div>
    </div>
  </teleport>
</template>