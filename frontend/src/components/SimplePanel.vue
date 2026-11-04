<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { t, currentLang } from '@/i18n'
import { appState } from '@/store'
import * as api from '@/api'
import { ensureApiKeyConfigured } from '@/composables/useTaskSubmit'
import { useVoice } from '@/composables/useVoice'
import { useToast } from '@/composables/useToast'
import { useDraft } from '@/composables/useDraft'
import { useNavigation } from '@/composables/useNavigation'
import AspectPicker from '@/components/shared/AspectPicker.vue'
import NeuStepper from '@/components/shared/NeuStepper.vue'
import NeuSwitch from '@/components/shared/NeuSwitch.vue'

const { voiceSelections, voiceIndex, voiceName, voiceDescription, openVoicePicker, initVoiceSelector } = useVoice()
const { showToast } = useToast()
const { goProgress } = useNavigation()

const emit = defineEmits<{ (e: 'go-list'): void }>()

// 简易模式使用独立的音色选择 key（与 c/m/a/p 互不干扰）
const VOICE_KEY = 's'

// ── 状态 ──
const idea = ref('')
const sceneCount = ref(3)
const previewData = ref<any>(null)
const previewLoading = ref(false)
const generating = ref(false)
const audioEnabled = ref(true)
const subtitleEnabled = ref(true)
const resolution = ref('768x1152')

const resolutions = [
  { value: '768x1152', label: 'resPortrait' },
  { value: '1280x720', label: 'resLandscape' },
  { value: '1024x1024', label: 'resSquare' },
]

// preview-script 白名单仅 ar/en，默认按 UI 语言降级；实际配音语言由所选音色驱动
const contentLang = computed(() => (currentLang.value === 'ar' ? 'ar' : 'en'))

const currentVoiceId = computed(() => voiceSelections[VOICE_KEY] || 'zh-CN-XiaoxiaoNeural')

onMounted(async () => {
  if (!voiceSelections[VOICE_KEY]) voiceSelections[VOICE_KEY] = 'zh-CN-XiaoxiaoNeural'
  // 音色目录未加载时补齐（App 已初始化时跳过）
  if (!appState.voiceCatalog) {
    await initVoiceSelector()
  }
})

// Logikcheck Befund 8: Ein-Klick-Eingabe lokal sichern — Reload setzt sonst
// alles auf leer zurück (der Reiter liegt nur im Komponentenstatus).
const draft = useDraft('simple')
;(() => {
  const d = draft.load()
  if (!d) return
  if (typeof d.idea === 'string') idea.value = d.idea
  if (typeof d.sceneCount === 'number') sceneCount.value = d.sceneCount
  if (typeof d.audioEnabled === 'boolean') audioEnabled.value = d.audioEnabled
  if (typeof d.subtitleEnabled === 'boolean') subtitleEnabled.value = d.subtitleEnabled
  if (typeof d.resolution === 'string') resolution.value = d.resolution
})()
watch([idea, sceneCount, audioEnabled, subtitleEnabled, resolution], () => {
  draft.save({
    idea: idea.value, sceneCount: sceneCount.value, audioEnabled: audioEnabled.value,
    subtitleEnabled: subtitleEnabled.value, resolution: resolution.value,
  })
})

// Logikcheck Befund 3: geänderte Eingabe macht die bestätigte Vorschau ungültig
// (sie wurde aus dem alten Text erzeugt) — freigeben statt veralten lassen.
watch([idea, sceneCount], () => {
  previewData.value = null
})

async function generatePreview() {
  if (!idea.value.trim()) {
    showToast(t('enterIdea'), 3500)
    return
  }
  previewLoading.value = true
  try {
    const d = await api.creativePreview(idea.value.trim(), contentLang.value, sceneCount.value)
    if (d.ok === false) throw new Error(d.detail || t('failCreate'))
    previewData.value = d
  } catch (e: any) {
    showToast(e?.message || t('failCreate'), 4500)
  } finally {
    previewLoading.value = false
  }
}

function pickVoice() {
  openVoicePicker(VOICE_KEY)
}

async function generate() {
  if (!idea.value.trim()) {
    showToast(t('enterIdea'), 3500)
    return
  }
  // Logikcheck Befund 10：缺 API Key 时提前拦截（与 useTaskSubmit 行为一致）
  if (!(await ensureApiKeyConfigured())) {
    showToast(t('apiKeyMissingHint'), 4500)
    return
  }
  generating.value = true
  try {
    const fd = new FormData()
    fd.append('idea', idea.value.trim())
    fd.append('scene_count', String(sceneCount.value))
    fd.append('scene_durations_json', JSON.stringify(Array(sceneCount.value).fill(5)))
    fd.append('audio_enabled', String(audioEnabled.value))
    fd.append('audio_voice', currentVoiceId.value)
    // audio_lang 用页面语言：创意旁白由 LLM 按页面语言生成，音色兼容性按此校验
    fd.append('audio_lang', currentLang.value)
    fd.append('subtitle_enabled', String(subtitleEnabled.value))
    const [w, h] = resolution.value.split('x').map(Number)
    fd.append('video_width', String(w))
    fd.append('video_height', String(h))
    fd.append('execution_mode', 'auto')
    // Logikcheck Befund 3: bestätigte Vorschau mitgeben — das Backend säiert sie
    // als fertige Schritt-Artefakte ein, das Video nutzt genau die gezeigten
    // Szenen statt sie neu (und anders) zu generieren.
    if (previewData.value?.story && Array.isArray(previewData.value?.scenes)) {
      fd.append('preview_json', JSON.stringify({
        story: previewData.value.story,
        scenes: previewData.value.scenes,
        narration: previewData.value.narration || '',
      }))
    }

    const d = await api.submitCreative(fd)
    if (!d.ok) throw new Error(d.detail || t('failCreate'))
    draft.clear()
    showToast(t('simpleGenerated'), 5000, 'success')
    goProgress(d.task_id, 'simple')
    emit('go-list')
  } catch (e: any) {
    showToast(t('failCreate') + ': ' + (e?.message || ''), 4500)
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <div>
    <div class="glass-card rounded-2xl p-6 mb-4">
      <h2 class="text-lg font-semibold text-accent mb-4">{{ t('simpleTitle') }}</h2>

      <!-- 步骤 1：主题输入 -->
      <div class="mb-4">
        <label class="block text-sm text-muted mb-1.5">{{ t('simpleIdea') }} <span class="text-red-400">*</span></label>
        <textarea
          v-model="idea"
          rows="3"
          :placeholder="t('simpleIdeaPlaceholder')"
          class="w-full glass-input rounded-lg px-4 py-2.5 text-sm resize-y text-ink placeholder-muted"
        ></textarea>
      </div>
      <div class="mb-4">
        <label class="block text-xs text-muted font-medium mb-1.5">{{ t('sceneCount') }}</label>
        <NeuStepper v-model="sceneCount" :min="1" :max="30" />
      </div>
    </div>

    <div class="glass-card rounded-2xl p-6 mb-4">
      <!-- 步骤 2：生成预览 & 设置 -->
      <button
        class="w-full py-3 bg-accent text-accent-ink hover:bg-accent/90 rounded-xl text-base font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed glow-btn mb-4"
        :disabled="previewLoading"
        @click="generatePreview"
      >
        {{ previewLoading ? t('simplePreviewing') : t('simplePreview') }}
      </button>

      <template v-if="previewData && previewData.scenes">
        <h3 class="text-sm font-medium text-accent mb-3">{{ t('simpleScenes') }}</h3>
        <div class="space-y-4 mb-6">
          <div v-for="(s, i) in previewData.scenes" :key="i" class="p-4 rounded-xl bg-paper-2/30 border border-rule/50">
            <div class="text-sm font-semibold text-ink mb-1">{{ t('scene_') }}{{ i + 1 }} · {{ s.title }}</div>
            <div class="text-xs text-muted mb-2"><span class="text-ink-2 font-medium">{{ t('simpleScenePrompt') }}:</span> {{ s.prompt }}</div>
            <div class="text-xs text-muted"><span class="text-ink-2 font-medium">{{ t('simpleSceneVoiceover') }}:</span> {{ s.voiceover }}</div>
          </div>
        </div>
      </template>

      <!-- 设置面板 -->
      <h3 class="text-sm font-medium text-accent mb-3">{{ t('simpleSetting') }}</h3>
      <div class="mb-4">
        <label class="block text-sm text-muted font-medium mb-2">{{ t('resolution') }}</label>
        <AspectPicker v-model="resolution" />
      </div>

      <div class="mb-4">
        <label class="block text-sm text-muted mb-1.5">{{ t('voiceRole') }}</label>
        <button
          class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink text-left hover:border-accent/40 transition flex items-center justify-between"
          @click="pickVoice"
        >
          <span>{{ voiceName(VOICE_KEY) || voiceDescription(VOICE_KEY) || currentVoiceId }}</span>
          <span class="text-xs text-muted">🔄 {{ t('chooseVoice') || 'Выбрать' }}</span>
        </button>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-2">
        <div class="p-3 rounded-xl border border-rule/30 bg-paper-2/40 flex items-center justify-between">
          <span class="text-xs text-ink-2 font-medium">{{ t('enableNarration') }}</span>
          <NeuSwitch v-model="audioEnabled" />
        </div>
        <div class="p-3 rounded-xl border border-rule/30 bg-paper-2/40 flex items-center justify-between">
          <span class="text-xs text-ink-2 font-medium">{{ t('enableSubtitle') }}</span>
          <NeuSwitch v-model="subtitleEnabled" />
        </div>
      </div>
    </div>

    <!-- 步骤 3：一键生成 -->
    <button
      class="w-full py-3.5 bg-accent text-accent-ink hover:bg-accent/90 rounded-xl text-base font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed glow-btn"
      :disabled="generating"
      @click="generate"
    >
      {{ generating ? t('simpleGenerating') : t('simpleGenerate') }}
    </button>
  </div>
</template>