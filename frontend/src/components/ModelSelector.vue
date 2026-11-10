<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { t } from '@/i18n'
import { appState, getCollapsePrefs, setCollapsePref } from '@/store'
import { useConfig } from '@/composables/useConfig'
import { useVideoModelCaps } from '@/composables/useVideoModelCaps'
import { useToast } from '@/composables/useToast'
import { useGa } from '@/composables/useGa'

const emit = defineEmits<{ (e: 'add-provider'): void }>()

const { trackEvent } = useGa()
const { showToast } = useToast()
const vmCaps = useVideoModelCaps()

const collapsed = reactive(getCollapsePrefs())
function toggleConfigPanel(section: string) {
  collapsed[section] = !collapsed[section]
  setCollapsePref(section, collapsed[section])
}

const {
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
  loadModels,
} = useConfig()

// 供应商相关的 computed（原 ConfigPanel 本地定义）
const textProviderOptions = computed(() => {
  const opts: { key: string; label: string }[] = []
  const list = appState.textProviders || []
  const hasAgnes = list.some((p: any) => p.provider === 'agnes')
  if (!hasAgnes) opts.push({ key: 'agnes', label: t('providerBuiltinAgnes') })
  list.forEach((p: any) => {
    opts.push({ key: p.provider, label: (p.display_name || p.provider) })
  })
  return opts
})
const textProviderComposite = computed<string>({
  get() {
    return appState.models.text_provider || 'agnes'
  },
  set(val: string) {
    const cur = appState.models.text_provider || 'agnes'
    if (val === cur) return
    appState.models.text_provider = val === 'agnes' ? '' : val
    appState.textProviderSelected = val
    const models = textModelsForProvider(val)
    if (models.length > 0) appState.models.text = models[0]
  },
})
function textModelsForProvider(provider: string): string[] {
  if (provider === 'agnes') return appState.modelListCache.text || []
  return appState.providerModelCache[provider] || []
}
const textModelOptions = computed(() => textModelsForProvider(textProviderComposite.value))

function modelDisplayLabel(m: string): string {
  return m
}
function vmDurationsLabel(ds: unknown[]): string {
  if (!Array.isArray(ds)) return ''
  return ds.map((d: any) => (typeof d === 'number' ? d + 's' : String(d))).join(' / ')
}
function vmPixelLabel(opts: { value: string }[]): string {
  if (!Array.isArray(opts)) return ''
  return opts.map((o: any) => o.value || o).join(' / ')
}
function vmRatioListText(item: { model: string; caps: Record<string, any> }): string {
  const r = item?.caps?.resolution
  if (!r || r.type !== 'ratio') return ''
  return (r.options || []).map((o: any) => o.label || o.value || o).join(' / ')
}

onMounted(async () => {
  await loadModels()
  await loadTextProviders()
})
</script>

<template>
  <!-- 模型选择 -->
  <div class="glass-card rounded-2xl mb-6 overflow-hidden transition-all duration-300">
    <button
      v-if="collapsed.model"
      type="button"
      class="w-full flex items-center justify-between px-6 py-3 cursor-pointer hover:bg-paper-3 transition text-left"
      :aria-expanded="!collapsed.model"
      @click="toggleConfigPanel('model')"
    >
      <div class="flex items-center gap-3">
        <svg class="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
        <span class="text-sm text-muted">
          <span class="text-ink-2 font-medium">{{ t('modelTitle') }}</span>
          <span class="text-muted mx-2">·</span>
          <span v-if="appState.models.text || appState.models.image || appState.models.video" class="text-muted">
            {{ t('modelTagText') }} {{ appState.models.text }} {{ t('modelTagImage') }} {{ appState.models.image }} {{ t('modelTagVideo') }} {{ appState.models.video }}
          </span>
          <span v-else class="text-muted">-</span>
        </span>
      </div>
      <svg class="w-4 h-4 text-muted shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
    </button>
    <div v-else class="p-6 pt-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-lg font-semibold text-accent">{{ t('modelTitle') }}</h2>
        <div class="flex items-center gap-2">
          <span class="text-xs px-2 py-1 rounded-full bg-paper-2 text-muted">{{ t('modelSyncIdle') }}</span>
          <button
            class="text-xs text-muted hover:text-ink-2 transition px-2 py-1 rounded cursor-pointer"
            :aria-label="t('collapse')"
            :aria-expanded="!collapsed.model"
            @click="toggleConfigPanel('model')"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
          </button>
        </div>
      </div>
      <p class="text-xs text-muted mb-4">{{ t('modelHint') }}</p>
      <div class="space-y-3">
        <div>
          <label class="block text-xs text-muted mb-1">{{ t('modelSupplier') }}</label>
          <div class="flex justify-end mb-1">
            <button
              class="text-xs text-accent hover:text-ink transition whitespace-nowrap"
              @click="emit('add-provider')"
            >{{ t('providerAddBtn') }}</button>
          </div>
          <div class="flex gap-3">
            <select
              v-model="textProviderComposite"
              class="flex-1 glass-input rounded-lg px-3 py-2.5 text-sm text-ink"
              :aria-label="t('modelSupplier')"
            >
              <option v-for="opt in textProviderOptions" :key="opt.key" :value="opt.key">{{ opt.label }}</option>
            </select>
            <button class="px-4 py-2.5 bg-paper-3 hover:bg-paper-3 rounded-lg text-sm font-medium transition whitespace-nowrap" @click="syncModels">
              {{ t('modelSync') }}
            </button>
          </div>
          <p class="text-xs text-muted/70 mt-1">{{ t('providerTextHint') }}</p>
          <label class="block text-xs text-muted mb-1 mt-3">{{ t('modelTextLabel') }}</label>
          <select
            v-model="appState.models.text"
            class="flex-1 glass-input rounded-lg px-3 py-2.5 text-sm text-ink"
            :aria-label="t('modelTextLabel')"
          >
            <option v-if="textModelOptions.length === 0" value="">{{ t('providerNoModels') }}</option>
            <option v-for="m in textModelOptions" :key="m" :value="m">{{ modelDisplayLabel(m) }}</option>
          </select>
          <p v-if="textModelOptions.length === 0" class="text-xs text-muted mt-1.5">{{ t('providerNoModels') }}</p>
          <p v-if="betaHintVisible" class="text-xs text-accent mt-1.5">{{ t('modelBetaHint') }}</p>
          <p v-if="isPaidModel(appState.models.text)" class="text-xs text-warning mt-1.5">{{ t('modelPaidHint') }}</p>
        </div>
        <div>
          <label class="block text-xs text-muted mb-1">{{ t('modelImageLabel') }}</label>
          <select v-model="appState.models.image" class="flex-1 glass-input rounded-lg px-3 py-2.5 text-sm text-ink">
            <option v-for="m in appState.modelListCache.image" :key="m" :value="m">{{ modelDisplayLabel(m) }}</option>
          </select>
          <p v-if="isPaidModel(appState.models.image)" class="text-xs text-warning mt-1.5">{{ t('modelPaidHint') }}</p>
        </div>
        <!-- v6.2：开放视频模型选择 + 三模型差异说明 -->
        <div>
          <label class="block text-xs text-muted mb-1">{{ t('modelVideoLabel') }} (v6.2)</label>
          <select v-model="appState.models.video" class="flex-1 glass-input rounded-lg px-3 py-2.5 text-sm text-ink">
            <option v-for="m in appState.modelListCache.video" :key="m" :value="m">{{ modelDisplayLabel(m) }}{{ vmCaps.isAdapted(m) ? '' : ' [!]' }}</option>
          </select>
          <!-- v7.0 U8：上游有、本地能力表无的模型显式提示（避免「模型可见档位不能用」） -->
          <p v-if="appState.models.video && !vmCaps.isAdapted(appState.models.video)" class="text-xs text-warning mt-1.5">{{ t('vmUnadaptedHint') }}</p>
          <p v-if="vmCaps.isPaidTag(appState.models.video)" class="text-xs text-warning mt-1.5">{{ t('modelPaidHint') }}</p>
          <p v-else-if="vmCaps.priceText(appState.models.video)" class="text-xs text-success mt-1.5">{{ vmCaps.priceText(appState.models.video) }}</p>

          <!-- 三模型差异对比（选模型阶段详细说明） -->
          <div v-if="vmCaps.allCapabilities().length > 0" class="mt-3 rounded-lg bg-paper-3/60 p-3">
            <p class="text-xs font-medium text-ink-2 mb-2">{{ t('vmDiffTitle') }}</p>
            <div class="overflow-x-auto">
              <table class="w-full text-[11px] leading-relaxed">
                <thead>
                  <tr class="text-muted">
                    <th class="text-left font-normal pr-3 py-0.5">{{ t('vmColCapability') }}</th>
                    <th v-for="item in vmCaps.allCapabilities()" :key="item.model" class="text-left font-normal px-2 py-0.5 whitespace-nowrap">
                      <span :class="item.model === appState.models.video ? 'text-accent' : ''">{{ item.caps.label }}</span>
                      <span v-if="item.caps.price === 'paid'" class="text-warning"> {{ t('vmTagPaid') }}</span>
                      <span v-else-if="item.caps.price === 'free'" class="text-success"> {{ t('vmTagFree') }}</span>
                    </th>
                  </tr>
                </thead>
                <tbody class="text-ink-2">
                  <tr>
                    <td class="text-muted pr-3 py-0.5">{{ t('vmColPrice') }}</td>
                    <td v-for="item in vmCaps.allCapabilities()" :key="'p' + item.model" class="px-2 py-0.5" :class="item.caps.price === 'paid' ? 'text-warning' : 'text-success'">
                      {{ vmCaps.priceText(item.model) }}
                    </td>
                  </tr>
                  <tr>
                    <td class="text-muted pr-3 py-0.5">{{ t('vmColMode') }}</td>
                    <td v-for="item in vmCaps.allCapabilities()" :key="'m' + item.model" class="px-2 py-0.5">
                      {{ vmCaps.modeOptions(item.model).map((x) => x.label).join(' · ') }}
                    </td>
                  </tr>
                  <tr>
                    <td class="text-muted pr-3 py-0.5">{{ t('vmColDuration') }}</td>
                    <td v-for="item in vmCaps.allCapabilities()" :key="'d' + item.model" class="px-2 py-0.5">
                      {{ vmDurationsLabel(item.caps.durations) }}
                    </td>
                  </tr>
                  <tr>
                    <td class="text-muted pr-3 py-0.5">{{ t('vmColResolution') }}</td>
                    <td v-for="item in vmCaps.allCapabilities()" :key="'r' + item.model" class="px-2 py-0.5">
                      <template v-if="item.caps.resolution && item.caps.resolution.type === 'pixels'">
                        {{ vmPixelLabel(item.caps.resolution.options) }}
                      </template>
                      <template v-else-if="item.caps.resolution">
                        {{ vmRatioListText(item) }}<span v-if="item.caps.resolution.sizes.length > 1">（{{ item.caps.resolution.sizes.join(' / ') }}）</span>
                      </template>
                    </td>
                  </tr>
                  <tr>
                    <td class="text-muted pr-3 py-0.5">{{ t('vmColNegative') }}</td>
                    <td v-for="item in vmCaps.allCapabilities()" :key="'n' + item.model" class="px-2 py-0.5">
                      {{ item.caps.supports_negative ? t('vmYes') : t('vmNo') }}
                    </td>
                  </tr>
                  <tr>
                    <td class="text-muted pr-3 py-0.5">{{ t('vmColRefVideo') }}</td>
                    <td v-for="item in vmCaps.allCapabilities()" :key="'v' + item.model" class="px-2 py-0.5">
                      {{ item.caps.supports_ref_video ? t('vmYes') : t('vmNo') }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="text-xs text-muted mt-2">{{ vmCaps.descOf(appState.models.video) }}</p>
          </div>
        </div>
      </div>
      <div class="flex gap-3 mt-4">
        <button class="px-5 py-2.5 bg-accent text-accent-ink hover:bg-accent/90 rounded-lg text-sm font-medium transition" @click="saveModels">{{ t('save') }}</button>
        <span v-if="modelSaveStatus === 'ok'" class="self-center text-xs text-success">{{ t('modelSaved') }}</span>
        <span v-if="modelSaveStatus === 'error'" class="self-center text-xs text-danger">{{ modelErrorMsg }}</span>
      </div>
    </div>
  </div>

</template>