<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { t, currentLang } from '@/i18n'
import { appState } from '@/store'
import { useVoice } from '@/composables/useVoice'
import { useTaskSubmit, collectAudioSubtitleFields } from '@/composables/useTaskSubmit'
import { useDraft } from '@/composables/useDraft'
import { normalizeResolution } from '@/composables/useVideoModelCaps'
import WatermarkToggle from '@/components/shared/WatermarkToggle.vue'
import SubtitleConfig from '@/components/shared/SubtitleConfig.vue'
import PresetPicker from '@/components/presets/PresetPicker.vue'
import CameraMovementPicker from '@/components/presets/CameraMovementPicker.vue'
import AspectPicker from '@/components/shared/AspectPicker.vue'
import DropzoneCard from '@/components/shared/DropzoneCard.vue'
import StylePresetChips from '@/components/shared/StylePresetChips.vue'
import InfoTooltip from '@/components/shared/InfoTooltip.vue'
import NeuStepper from '@/components/shared/NeuStepper.vue'
import NeuSwitch from '@/components/shared/NeuSwitch.vue'
import LutSelector from '@/components/shared/LutSelector.vue'
import AssetLibraryPicker from '@/components/shared/AssetLibraryPicker.vue'
import type { WorkspaceAsset } from '@/types'

const { voiceSelections } = useVoice()
const { submitting, runSubmit } = useTaskSubmit()

const subtitleRef = ref<InstanceType<typeof SubtitleConfig>>()

const form = reactive({
  name: '',
  idea: '',
  durationSource: 'manual' as 'manual' | 'prompt',
  sceneCount: 3,
  uniform: true,
  uniformDuration: 5,
  independentDurations: [] as number[],
  style: '',
  cameraMovement: '',
  draftMode: false,
  lutId: '',
  selectedAssetId: '',
  chaining: 'keyframes',
  resolution: '768x1152',
  refImage: null as File | null,
  refName: '',
  useEndFrames: false,
  genEndFromRef: true,
  endFrames: [] as File[],
  // v5.0 优化 5：用户上传分镜场景图（按场景 index 对齐）
  sceneRefs: [] as File[],
})

const attachedScenario = ref<{
  title: string
  story: string
  scenes: { title: string; prompt: string; voiceover: string; duration: number }[]
  locks: string[]
} | null>(null)

function parseResolution(val: string) {
  const [w, h] = val.split('x').map(Number)
  return { width: w, height: h }
}

// 3.4：创意表单草稿（JSON 安全字段，File 不保存）
const draft = useDraft('creative')
;(() => {
  const d = draft.load()
  if (!d) return
  if (typeof d.name === 'string') form.name = d.name
  if (typeof d.idea === 'string') form.idea = d.idea
  if (d.durationSource === 'manual' || d.durationSource === 'prompt') form.durationSource = d.durationSource
  if (typeof d.sceneCount === 'number') form.sceneCount = d.sceneCount
  if (typeof d.uniform === 'boolean') form.uniform = d.uniform
  if (typeof d.uniformDuration === 'number') form.uniformDuration = d.uniformDuration
  if (Array.isArray(d.independentDurations)) form.independentDurations = d.independentDurations
  if (typeof d.style === 'string') form.style = d.style
  if (typeof d.cameraMovement === 'string') form.cameraMovement = d.cameraMovement
  if (typeof d.draftMode === 'boolean') form.draftMode = d.draftMode
  if (typeof d.lutId === 'string') form.lutId = d.lutId
  if (typeof d.chaining === 'string') form.chaining = d.chaining
  if (typeof d.resolution === 'string') form.resolution = normalizeResolution(d.resolution)
})()
draft.autoSave(form, (v) => ({
  name: v.name, idea: v.idea, durationSource: v.durationSource, sceneCount: v.sceneCount,
  uniform: v.uniform, uniformDuration: v.uniformDuration,
  independentDurations: v.independentDurations, style: v.style,
  cameraMovement: v.cameraMovement, draftMode: v.draftMode, lutId: v.lutId,
  chaining: v.chaining, resolution: v.resolution,
}))

// Full ScenarioStudio transfer: title, logline, style, shots, camera movements, continuity locks
function onApplyScenario(e: CustomEvent) {
  const p = e.detail
  if (!p) return
  if (p.title) form.name = p.title
  if (p.logline) form.idea = p.logline
  if (p.style) form.style = p.style

  const locks: string[] = Array.isArray(p.character?.continuity_locks)
    ? p.character.continuity_locks.map((l: any) => `${l.key}: ${l.phrase}`).filter(Boolean)
    : []

  if (Array.isArray(p.shots) && p.shots.length > 0) {
    form.durationSource = 'manual'
    form.sceneCount = p.shots.length
    form.uniform = false
    form.independentDurations = p.shots.map((s: any) =>
      Math.max(2, Math.min(30, Math.round((s.end_time_s || 5) - (s.start_time_s || 0)) || 5)),
    )
    const charLine = p.character
      ? `${p.character.name || ''} (${p.character.role || ''}): ${p.character.appearance || ''} ${p.character.wardrobe || ''}`.trim()
      : ''
    const storyText = [p.logline || p.title || '', charLine, locks.length ? `Locks: ${locks.join('; ')}` : '']
      .filter(Boolean)
      .join('\n\n')
    const mappedScenes = p.shots.map((s: any, idx: number) => ({
      title: `${s.beat_type || 'Scene'} #${s.scene_number || idx + 1}`,
      prompt: s.video_prompt || `${s.shot_size || ''}, ${s.camera_movement || ''}. ${s.action_description || ''} ${s.lighting_and_color || ''}`.trim(),
      voiceover: s.narration || s.action_description || '',
      duration: form.independentDurations[idx] || 5,
    }))
    attachedScenario.value = {
      title: p.title || '',
      story: storyText || p.logline || '',
      scenes: mappedScenes,
      locks,
    }
  }
}

function onSelectAsset(asset: WorkspaceAsset | null) {
  form.selectedAssetId = asset ? asset.id : ''
  if (asset) {
    const extra = [asset.prompt, asset.continuity_locks].filter(Boolean).join('. ')
    if (extra && !form.idea.includes(extra)) {
      form.idea = form.idea.trim() ? `${form.idea.trim()}\n\n[${asset.name}: ${extra}]` : `[${asset.name}: ${extra}]`
    }
  }
}

onMounted(() => {
  window.addEventListener('apply-scenario-to-creative', onApplyScenario as EventListener)
})

onUnmounted(() => {
  window.removeEventListener('apply-scenario-to-creative', onApplyScenario as EventListener)
})

function onRefImageChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0] || null
  form.refImage = file
  form.refName = file ? file.name : ''
}

function toggleEndFrames() {
  if (!form.useEndFrames) {
    form.genEndFromRef = false
  }
}

function toggleEndFrameMode() {
  if (form.genEndFromRef) {
    form.useEndFrames = false
  }
}

function addEndFrameInput() {
  form.endFrames.push(new File([], ''))
}

function onEndFrameChange(e: Event, idx: number) {
  const file = (e.target as HTMLInputElement).files?.[0] || null
  if (file) form.endFrames[idx] = file
}

function onSceneRefChange(e: Event, idx: number) {
  const file = (e.target as HTMLInputElement).files?.[0] || null
  if (file) form.sceneRefs[idx] = file
}

async function submitCreative() {
  let ev: Record<string, any> = {}
  await runSubmit({
    taskType: 'creative',
    buildForm: () => {
      const idea = form.idea.trim()
      if (!idea) throw new Error(t('enterIdea'))
      const fd = new FormData()
      fd.append('idea', idea)
      fd.append('creative_name', form.name.trim())
      fd.append('style', form.style)
      if (form.cameraMovement) fd.append('camera_movement', form.cameraMovement)
      fd.append('draft_mode', String(form.draftMode))
      if (form.lutId) fd.append('lut_id', form.lutId)
      if (form.selectedAssetId) fd.append('reference_asset_id', form.selectedAssetId)
      fd.append('chaining_mode', form.chaining)
      if (attachedScenario.value && attachedScenario.value.scenes.length === form.sceneCount) {
        fd.append(
          'preview_json',
          JSON.stringify({
            story: attachedScenario.value.story,
            scenes: attachedScenario.value.scenes,
            narration: attachedScenario.value.scenes.map((s) => s.voiceover).filter(Boolean).join('\n'),
          }),
        )
      }

      fd.append('duration_source', form.durationSource)
      if (form.durationSource === 'manual') {
        fd.append('scene_count', String(form.sceneCount))
        fd.append('uniform_duration', String(form.uniform))
        if (form.uniform) {
          fd.append('scene_durations_json', JSON.stringify(Array(form.sceneCount).fill(form.uniformDuration)))
        } else {
          const vals = form.independentDurations.slice(0, form.sceneCount)
          fd.append('scene_durations_json', JSON.stringify(vals))
        }
      } else {
        fd.append('scene_count', '0')
        fd.append('uniform_duration', 'true')
        fd.append('scene_durations_json', JSON.stringify([]))
      }

      const res = parseResolution(form.resolution)
      fd.append('video_width', String(res.width))
      fd.append('video_height', String(res.height))
      fd.append('use_custom_end_frames', String(form.useEndFrames))
      fd.append('generate_end_frames_from_ref', String(form.genEndFromRef))

      if (form.refImage) fd.append('reference_image', form.refImage)
      if (form.useEndFrames) {
        form.endFrames.forEach((f) => {
          if (f && f.size > 0) fd.append('end_frame_images', f)
        })
      }
      // v5.0 优化 5：用户上传分镜场景图（多文件，后端按上传顺序对应场景 index）
      if (form.sceneRefs.length > 0) {
        form.sceneRefs.forEach((f) => {
          if (f && f.size > 0) fd.append('scene_reference_images', f)
        })
      }

      // Audio & Subtitle
      const sc = subtitleRef.value
      collectAudioSubtitleFields(fd, sc, voiceSelections, 'c', currentLang.value)

      // v6.0 手动模式：执行模式 + 暂停点
      fd.append('execution_mode', appState.execMode)
      fd.append('pause_points', JSON.stringify(appState.execMode === 'manual' ? appState.pausePoints : []))

      ev = {
        style: form.style,
        chaining_mode: form.chaining,
        duration_source: form.durationSource,
        resolution: form.resolution,
        audio: sc?.audioEnabled ? 'on' : 'off',
        subtitle: sc?.subtitleEnabled ? 'on' : 'off',
      }
      return fd
    },
    extraEvent: ev,
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
      <a href="https://video.lichuanyang.top/guides/prompt-examples-creative" target="_blank" rel="noopener" class="hover:text-accent transition-colors">{{ t('exampleLinkCreative') }}</a>
    </div>

    <div class="glass-card rounded-2xl p-6 mb-4">
      <h2 class="text-lg font-semibold text-accent mb-4">{{ t('creativeSettings') }}</h2>

      <!-- Attached Scenario Banner (from Scenario Studio) -->
      <div
        v-if="attachedScenario"
        class="mb-4 p-3.5 rounded-xl border border-accent/40 bg-accent/10 flex flex-wrap items-start justify-between gap-2"
      >
        <div class="space-y-1 min-w-0 flex-1">
          <p class="text-xs font-semibold text-accent">
            {{ t('scAttachedBanner').replace('{n}', String(attachedScenario.scenes.length)) }}
          </p>
          <div v-if="attachedScenario.locks.length" class="flex flex-wrap gap-1">
            <span
              v-for="lk in attachedScenario.locks"
              :key="lk"
              class="text-[11px] px-2 py-0.5 rounded-full bg-paper border border-rule text-ink-2 font-mono"
            >
              {{ lk }}
            </span>
          </div>
        </div>
        <button
          type="button"
          class="text-xs text-muted hover:text-ink px-2 py-1 rounded border border-rule bg-paper"
          @click="attachedScenario = null"
        >
          {{ t('clear') }}
        </button>
      </div>

      <div class="mb-4">
        <label class="block text-sm text-muted mb-1.5" for="cr-name">{{ t('taskName') }}</label>
        <input id="cr-name" v-model="form.name" :placeholder="t('taskNamePlaceholder')" class="w-full glass-input rounded-lg px-4 py-2.5 text-sm text-ink placeholder-muted" />
      </div>

      <div class="mb-4">
        <label class="block text-sm text-muted mb-1.5" for="cr-idea">{{ t('ideaLabel') }} (idea) <span class="text-red-400">*</span></label>
        <textarea id="cr-idea" v-model="form.idea" rows="4" :placeholder="t('ideaPlaceholder')" class="w-full glass-input rounded-lg px-4 py-2.5 text-sm resize-y text-ink placeholder-muted"></textarea>
      </div>

      <!-- Scene Config -->
      <div class="mb-4 p-4 rounded-xl bg-paper-2/30 border border-rule/50">
        <h3 class="text-sm font-medium text-accent mb-3">{{ t('sceneConfig') }}</h3>
        <div class="mb-4">
          <label class="block text-sm text-muted mb-2">{{ t('durationSource') }}</label>
          <div class="flex gap-2">
            <label class="flex-1 flex items-center gap-2 px-3 py-2.5 rounded-lg bg-paper-2/50 border border-rule cursor-pointer hover:border-blue-500/30 transition">
              <input v-model="form.durationSource" type="radio" value="manual" class="text-accent" />
              <span class="text-sm text-ink-2">{{ t('sourceManual') }}</span>
            </label>
            <label class="flex-1 flex items-center gap-2 px-3 py-2.5 rounded-lg bg-paper-2/50 border border-rule cursor-pointer hover:border-blue-500/30 transition">
              <input v-model="form.durationSource" type="radio" value="prompt" class="text-accent" />
              <span class="text-sm text-ink-2">{{ t('sourcePrompt') }}</span>
            </label>
          </div>
          <p class="text-xs text-muted mt-1.5">{{ form.durationSource === 'manual' ? t('sourceManualHint') : t('sourcePromptHint') }}</p>
        </div>

        <div v-if="form.durationSource === 'manual'">
          <div class="mb-4">
            <label class="block text-xs text-muted font-medium mb-1.5">{{ t('sceneCount') }}</label>
            <NeuStepper v-model="form.sceneCount" :min="1" :max="30" />
          </div>
          <div class="mb-3">
            <label class="block text-xs text-muted font-medium mb-2">{{ t('durationMode') }}</label>
            <div class="flex gap-2 mb-3">
              <label class="flex items-center gap-2 text-sm text-muted cursor-pointer">
                <input v-model="form.uniform" type="radio" :value="true" class="text-accent" />
                <span>{{ t('uniformDuration') }}</span>
              </label>
              <label class="flex items-center gap-2 text-sm text-muted cursor-pointer">
                <input v-model="form.uniform" type="radio" :value="false" class="text-accent" />
                <span>{{ t('independentDuration') }}</span>
              </label>
            </div>
            <div v-if="form.uniform">
              <NeuStepper v-model="form.uniformDuration" :min="2" :max="30" :unit="t('seconds') || 's'" />
            </div>
            <div v-else class="space-y-2">
              <div v-for="i in form.sceneCount" :key="i" class="flex items-center gap-3 mb-1.5">
                <span class="text-xs text-muted w-14">{{ t('scene_') }} {{ i }}</span>
                <NeuStepper v-model="form.independentDurations[i - 1]" :min="2" :max="30" :unit="t('seconds') || 's'" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mb-4">
        <div class="flex items-center justify-between mb-1.5">
          <label class="block text-sm text-muted font-medium" for="cr-style">{{ t('visualStyle') }}</label>
          <InfoTooltip :text="t('tipVisualStyle')" />
        </div>
        <StylePresetChips v-model="form.style" class="mb-2" />
        <div class="flex items-center gap-2">
          <input id="cr-style" v-model="form.style" :placeholder="t('visualStyle')" class="flex-1 glass-input rounded-lg px-4 py-2.5 text-sm text-ink placeholder-muted" />
          <PresetPicker v-model="form.style" />
        </div>
      </div>

      <!-- 20 Cinematic Camera Movements (SYNTX AI) -->
      <div class="mb-4">
        <div class="flex items-center justify-between mb-1.5">
          <label class="block text-sm text-muted font-medium">{{ t('cameraMovementLabel') }}</label>
          <InfoTooltip :text="t('tipCameraMovement')" />
        </div>
        <CameraMovementPicker v-model="form.cameraMovement" />
      </div>
    </div>

    <!-- Advanced Config -->
    <div class="glass-card rounded-2xl p-6 mb-4">
      <h2 class="text-lg font-semibold text-accent mb-4">{{ t('advancedSettings') }}</h2>

      <!-- Draft Mode Toggle (pauses after storyboard/keyframes before video render) -->
      <div class="mb-5 p-3.5 rounded-xl bg-accent/10 border border-accent/25 flex items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-semibold text-accent">{{ t('draftModeTitle') }}</span>
            <span class="badge-info">{{ t('draftModeBadge') }}</span>
          </div>
          <p class="text-[11px] text-muted mt-1 leading-relaxed">{{ t('draftModeDesc') }}</p>
        </div>
        <NeuSwitch v-model="form.draftMode" :label="t('draftModeTitle')" />
      </div>

      <!-- Visual Aspect Ratio -->
      <div class="mb-5">
        <div class="flex items-center justify-between mb-2">
          <label class="block text-sm text-muted font-medium">{{ t('resolution') }}</label>
          <InfoTooltip :text="t('tipAspectRatio')" />
        </div>
        <AspectPicker v-model="form.resolution" />
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-sm text-muted font-medium" for="cr-chaining">{{ t('chainingMode') }}</label>
            <InfoTooltip :text="t('tipChainingMode')" />
          </div>
          <select id="cr-chaining" v-model="form.chaining" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink">
            <option value="keyframes">{{ t('modeKeyframes') }}</option>
            <option value="ti2vid">{{ t('modeTi2vid') }}</option>
            <option value="none">{{ t('modeNone') }}</option>
          </select>
        </div>
        <LutSelector v-model="form.lutId" />
      </div>

      <div class="mb-5">
        <AssetLibraryPicker :selected-id="form.selectedAssetId" @select="onSelectAsset" />
      </div>

      <!-- Reference Image with DropzoneCard -->
      <div class="mb-5">
        <div class="flex items-center justify-between mb-2">
          <label class="block text-sm text-muted font-medium">{{ t('referenceImage') }}</label>
          <InfoTooltip :text="t('tipReferenceImage')" />
        </div>
        <DropzoneCard
          v-model="form.refImage"
          :title="t('referenceImage')"
          :hint="t('refDescription')"
          badge="Reference Anchor"
          @change="(f) => form.refName = f ? f.name : ''"
        />
      </div>

      <!-- End Frames -->
      <div class="mb-4">
        <div class="flex items-center justify-between mb-3">
          <label class="text-sm text-muted">{{ t('customEndFrames') }}</label>
          <div class="flex gap-3">
            <label class="flex items-center gap-2 text-sm text-muted cursor-pointer">
              <input v-model="form.useEndFrames" type="checkbox" class="rounded bg-paper-2 border-rule" @change="toggleEndFrames" />
              <span>{{ t('enableCustomEndFrames') }}</span>
            </label>
            <label class="flex items-center gap-2 text-sm text-muted cursor-pointer">
              <input v-model="form.genEndFromRef" type="checkbox" class="rounded bg-paper-2 border-rule" @change="toggleEndFrameMode" />
              <span>{{ t('genEndFramesFromRef') }}</span>
            </label>
          </div>
        </div>
        <div v-if="form.useEndFrames" class="space-y-2">
          <p class="text-xs text-muted mb-2">{{ t('endFrameDesc') }}</p>
          <div class="space-y-2">
            <div v-for="i in form.sceneCount" :key="i" class="flex items-center gap-3 mb-2">
              <span class="text-xs text-muted w-16">{{ t('scene_') }} {{ i }}</span>
              <input type="file" accept="image/*" class="end-frame-file flex-1 text-sm text-muted file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:bg-paper-3 file:text-ink-2 hover:file:bg-paper-3" @change="onEndFrameChange($event, i - 1)" />
            </div>
          </div>
        </div>
      </div>

      <!-- Scene Reference Images (v5.0 优化 5) -->
      <div class="mb-4">
        <label class="block text-sm text-muted mb-1.5">{{ t('sceneReferenceImages') }}</label>
        <p class="text-xs text-muted mb-2">{{ t('sceneRefDesc') }}</p>
        <div class="space-y-2">
          <div v-for="i in form.sceneCount" :key="i" class="flex items-center gap-3 mb-2">
            <span class="text-xs text-muted w-16">{{ t('scene_') }} {{ i }}</span>
            <input type="file" accept="image/*" class="scene-ref-file flex-1 text-sm text-muted file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:bg-paper-3 file:text-ink-2 hover:file:bg-paper-3" @change="onSceneRefChange($event, i - 1)" />
          </div>
        </div>
      </div>
    </div>

    <!-- Audio & Subtitle -->
    <SubtitleConfig ref="subtitleRef" task="c" :with-style="true" />

    <WatermarkToggle />

    <button
      class="w-full py-3.5 bg-accent text-accent-ink hover:bg-accent/90 rounded-xl text-base font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed glow-btn"
      :disabled="submitting"
      :aria-busy="submitting"
      @click="submitCreative"
    >
      {{ submitting ? t('submitting') : t('startGenerate') }}
    </button>
  </div>
</template>
