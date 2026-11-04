<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { t } from '@/i18n'
import { appState } from '@/store'
import { useVoice } from '@/composables/useVoice'
import { useTaskSubmit, collectAudioSubtitleFields } from '@/composables/useTaskSubmit'
import { useDraft } from '@/composables/useDraft'
import WatermarkToggle from '@/components/shared/WatermarkToggle.vue'
import SubtitleConfig from '@/components/shared/SubtitleConfig.vue'
import AspectPicker from '@/components/shared/AspectPicker.vue'
import NeuSwitch from '@/components/shared/NeuSwitch.vue'

const { voiceSelections } = useVoice()
const { submitting, runSubmit } = useTaskSubmit()

const subtitleRef = ref<InstanceType<typeof SubtitleConfig>>()

const form = reactive({
  name: '',
  text: '',
  resolution: '768x1152',
  // v7.1 关键帧模式（I2V-first）：逐段先出关键帧静图再 i2v 动画
  keyframes: false,
  // v7.2 R8 质量闸：生成后逐段免费 VLM 检查 + FAIL 自动重生成一次
  qc: false,
})

const charCount = computed(() => form.text.length)

// Logikcheck Befund 6: Entwurf wie im Kreativformular lokal sichern —
// Aufgabentyp-Wechsel (unmount) und Seiten-Reload verlieren sonst lange Texte.
const draft = useDraft('manuscript')
;(() => {
  const d = draft.load()
  if (!d) return
  if (typeof d.name === 'string') form.name = d.name
  if (typeof d.text === 'string') form.text = d.text
  if (typeof d.resolution === 'string') form.resolution = d.resolution
  if (typeof d.keyframes === 'boolean') form.keyframes = d.keyframes
  if (typeof d.qc === 'boolean') form.qc = d.qc
})()
draft.autoSave(form, (v) => ({
  name: v.name, text: v.text, resolution: v.resolution,
  keyframes: v.keyframes, qc: v.qc,
}))

function parseResolution(val: string) {
  const [w, h] = val.split('x').map(Number)
  return { width: w, height: h }
}

async function submitManuscript() {
  let ev: Record<string, any> = {}
  await runSubmit({
    taskType: 'manuscript',
    buildForm: () => {
      const text = form.text.trim()
      if (!text) throw new Error(t('enterText'))
      const fd = new FormData()
      fd.append('manuscript_text', text)
      fd.append('creative_name', form.name.trim())
      const res = parseResolution(form.resolution)
      fd.append('video_width', String(res.width))
      fd.append('video_height', String(res.height))
      fd.append('generate_keyframes', String(form.keyframes))
      fd.append('qc_enabled', String(form.qc))

      const sc = subtitleRef.value
      collectAudioSubtitleFields(fd, sc, voiceSelections, 'm')

      // v6.0 手动模式：执行模式 + 暂停点
      fd.append('execution_mode', appState.execMode)
      fd.append('pause_points', JSON.stringify(appState.execMode === 'manual' ? appState.pausePoints : []))

      ev = {
        resolution: form.resolution,
        text_len: text.length,
        audio: sc?.audioEnabled ? 'on' : 'off',
        subtitle: sc?.subtitleEnabled ? 'on' : 'off',
      }
      return fd
    },
    extraEvent: ev,
    // Erfolgreich abgeschickt → Entwurf nicht wiederherstellen
    onSuccess: () => draft.clear(),
  })
}
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-4 text-xs text-muted">
      <svg class="w-3.5 h-3.5 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <a href="https://video.lichuanyang.top/guides/prompt-examples-manuscript" target="_blank" rel="noopener" class="hover:text-accent transition-colors">{{ t('exampleLinkManuscript') }}</a>
    </div>

    <div class="glass-card rounded-2xl p-6 mb-4">
      <h2 class="text-lg font-semibold text-accent mb-4">{{ t('manuscriptSettings') }}</h2>

      <div class="mb-4">
        <label class="block text-sm text-muted mb-1.5">{{ t('taskName') }}</label>
        <input v-model="form.name" :placeholder="t('taskNamePlaceholder')" class="w-full glass-input rounded-lg px-4 py-2.5 text-sm text-ink placeholder-muted" />
      </div>

      <div class="mb-4">
        <label class="block text-sm text-muted mb-1.5">{{ t('manuscriptText') }} <span class="text-red-400">*</span></label>
        <textarea v-model="form.text" rows="10" :placeholder="t('manuscriptPlaceholder')" class="w-full glass-input rounded-lg px-4 py-2.5 text-sm resize-y text-ink placeholder-muted font-mono"></textarea>
        <p class="text-xs text-muted mt-1">{{ t('charCount') }}: {{ charCount }}</p>
      </div>

      <div class="mb-5">
        <label class="block text-sm text-muted font-medium mb-2">{{ t('resolution') }}</label>
        <AspectPicker v-model="form.resolution" />
      </div>

      <!-- v7.1 关键帧模式（I2V-first） -->
      <div class="mb-3 p-3 rounded-xl border border-rule/30 bg-paper-2/40 flex items-center justify-between">
        <div class="mr-4">
          <span class="block text-sm text-ink-2 font-medium">{{ t('kfToggleLabel') }}</span>
          <span class="block text-xs text-muted mt-0.5 leading-relaxed">{{ t('kfToggleHint') }}</span>
        </div>
        <NeuSwitch v-model="form.keyframes" />
      </div>

      <!-- v7.2 R8 质量闸（opt-in） -->
      <div class="mb-2 p-3 rounded-xl border border-rule/30 bg-paper-2/40 flex items-center justify-between">
        <div class="mr-4">
          <span class="block text-sm text-ink-2 font-medium">{{ t('qcToggleLabel') }}</span>
          <span class="block text-xs text-muted mt-0.5 leading-relaxed">{{ t('qcToggleHint') }}</span>
        </div>
        <NeuSwitch v-model="form.qc" />
      </div>
    </div>

    <SubtitleConfig ref="subtitleRef" task="m" :with-style="true" />

    <WatermarkToggle />

    <button
      class="w-full py-3.5 bg-accent text-accent-ink hover:bg-accent/90 rounded-xl text-base font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed glow-btn"
      :disabled="submitting"
      @click="submitManuscript"
    >
      {{ submitting ? t('submitting') : t('startGenerate') }}
    </button>
  </div>
</template>
