<script setup lang="ts">
import { reactive } from 'vue'
import { t } from '@/i18n'
import { appState } from '@/store'
import { useTaskSubmit } from '@/composables/useTaskSubmit'
import { useDraft } from '@/composables/useDraft'
import type { WorkspaceAsset } from '@/types'
import AspectPicker from '@/components/shared/AspectPicker.vue'
import DropzoneCard from '@/components/shared/DropzoneCard.vue'
import StylePresetChips from '@/components/shared/StylePresetChips.vue'
import PresetPicker from '@/components/presets/PresetPicker.vue'
import CameraMovementPicker from '@/components/presets/CameraMovementPicker.vue'
import LutSelector from '@/components/shared/LutSelector.vue'
import AssetLibraryPicker from '@/components/shared/AssetLibraryPicker.vue'
import NeuStepper from '@/components/shared/NeuStepper.vue'
import NeuSwitch from '@/components/shared/NeuSwitch.vue'
import WatermarkToggle from '@/components/shared/WatermarkToggle.vue'

const { submitting, runSubmit } = useTaskSubmit()

const form = reactive({
  songTitle: '',
  visualStyle: 'Cinematic Music Video, 35mm film grain, dramatic lighting',
  bpm: 120,
  sceneCount: 6,
  resolution: '768x1152',
  generateMusic: false,
  musicPrompt: '',
  musicStyle: '',
  instrumental: false,
  sunoModel: 'V6',
  trimStartSec: 0,
  trimEndSec: 0,
  cameraMovement: '',
  lutId: '',
  audioFile: null as File | null,
  refImage: null as File | null,
  selectedAssetId: '',
})

const draft = useDraft('music-video')
;(() => {
  const d = draft.load()
  if (!d) return
  if (typeof d.songTitle === 'string') form.songTitle = d.songTitle
  if (typeof d.visualStyle === 'string') form.visualStyle = d.visualStyle
  if (typeof d.bpm === 'number') form.bpm = d.bpm
  if (typeof d.sceneCount === 'number') form.sceneCount = d.sceneCount
  if (typeof d.resolution === 'string') form.resolution = d.resolution
  if (typeof d.generateMusic === 'boolean') form.generateMusic = d.generateMusic
  if (typeof d.musicPrompt === 'string') form.musicPrompt = d.musicPrompt
  if (typeof d.musicStyle === 'string') form.musicStyle = d.musicStyle
  if (typeof d.instrumental === 'boolean') form.instrumental = d.instrumental
  if (typeof d.sunoModel === 'string') form.sunoModel = d.sunoModel
  if (typeof d.lutId === 'string') form.lutId = d.lutId
})()
draft.autoSave(form, (v) => ({
  songTitle: v.songTitle,
  visualStyle: v.visualStyle,
  bpm: v.bpm,
  sceneCount: v.sceneCount,
  resolution: v.resolution,
  generateMusic: v.generateMusic,
  musicPrompt: v.musicPrompt,
  musicStyle: v.musicStyle,
  instrumental: v.instrumental,
  sunoModel: v.sunoModel,
  lutId: v.lutId,
}))

function onAudioFileChange(e: Event) {
  form.audioFile = (e.target as HTMLInputElement).files?.[0] || null
}

function onSelectAsset(asset: WorkspaceAsset | null) {
  form.selectedAssetId = asset ? asset.id : ''
  if (asset?.prompt && !form.visualStyle.includes(asset.prompt)) {
    form.visualStyle = `${asset.prompt}, ${form.visualStyle}`
  }
}

async function submitMv() {
  await runSubmit({
    taskType: 'music_video',
    buildForm: () => {
      if (!form.audioFile && !form.generateMusic && !form.musicPrompt.trim() && !form.songTitle.trim()) {
        throw new Error(t('mvInputRequired'))
      }
      const fd = new FormData()
      fd.append('song_title', form.songTitle.trim())
      fd.append('visual_style', form.visualStyle.trim() || 'Cinematic Music Video')
      fd.append('bpm', String(form.bpm))
      fd.append('scene_count', String(form.sceneCount))
      const [w, h] = form.resolution.split('x').map(Number)
      fd.append('video_width', String(w || 768))
      fd.append('video_height', String(h || 1152))
      fd.append('generate_music', String(form.generateMusic))
      fd.append('music_prompt', form.musicPrompt.trim())
      fd.append('music_style', form.musicStyle.trim())
      fd.append('instrumental', String(form.instrumental))
      fd.append('suno_model', form.sunoModel)
      fd.append('trim_start_sec', String(form.trimStartSec || 0))
      fd.append('trim_end_sec', String(form.trimEndSec || 0))
      if (form.cameraMovement) fd.append('camera_movement', form.cameraMovement)
      if (form.lutId) fd.append('lut_id', form.lutId)
      if (form.audioFile) fd.append('audio_file', form.audioFile)
      if (form.refImage) fd.append('reference_image', form.refImage)
      else if (form.selectedAssetId) fd.append('reference_asset_id', form.selectedAssetId)
      fd.append('execution_mode', appState.execMode)
      fd.append('pause_points', JSON.stringify(appState.execMode === 'manual' ? appState.pausePoints : []))
      return fd
    },
    extraEvent: { bpm: form.bpm, scene_count: form.sceneCount, suno: form.generateMusic },
    onSuccess: () => draft.clear(),
  })
}
</script>

<template>
  <div>
    <div class="glass-card rounded-2xl p-6 mb-4 space-y-4">
      <h2 class="text-lg font-semibold text-accent">{{ t('mvSettings') }}</h2>

      <div>
        <label class="block text-sm text-muted mb-1.5" for="mv-title">{{ t('mvSongTitle') }}</label>
        <input
          id="mv-title"
          v-model="form.songTitle"
          class="w-full glass-input rounded-lg px-4 py-2.5 text-sm text-ink placeholder-muted"
          :placeholder="t('mvSongTitlePlaceholder')"
        />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs text-muted font-medium mb-1.5">{{ t('mvBpm') }}</label>
          <NeuStepper v-model="form.bpm" :min="40" :max="240" unit="BPM" />
        </div>
        <div>
          <label class="block text-xs text-muted font-medium mb-1.5">{{ t('sceneCount') }}</label>
          <NeuStepper v-model="form.sceneCount" :min="2" :max="30" />
        </div>
      </div>

      <!-- Audio Upload or Suno Generation -->
      <div class="p-4 rounded-xl bg-paper border border-rule space-y-3">
        <div class="flex items-center justify-between gap-3">
          <div>
            <span class="block text-sm font-medium text-ink">{{ t('mvAudioSection') }}</span>
            <span class="block text-xs text-muted">{{ t('mvAudioHint') }}</span>
          </div>
          <NeuSwitch v-model="form.generateMusic" :label="t('mvGenerateSuno')" />
        </div>

        <div v-if="!form.generateMusic">
          <label class="block text-xs text-muted mb-1.5" for="mv-audio-file">{{ t('mvUploadAudio') }}</label>
          <input
            id="mv-audio-file"
            type="file"
            accept=".mp3,.wav,.m4a,.ogg,.flac,.aac,audio/*"
            class="w-full text-xs text-muted file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border file:border-rule file:text-xs file:bg-paper-2 file:text-ink-2"
            @change="onAudioFileChange"
          />
          <p v-if="form.audioFile" class="text-xs text-success mt-1">{{ form.audioFile.name }}</p>
        </div>

        <div v-else class="space-y-3 pt-2 border-t border-rule/50">
          <div>
            <label class="block text-xs text-muted mb-1" for="mv-music-prompt">{{ t('mvMusicPrompt') }}</label>
            <textarea
              id="mv-music-prompt"
              v-model="form.musicPrompt"
              rows="2"
              class="w-full glass-input rounded-lg px-3 py-2 text-sm text-ink placeholder-muted"
              :placeholder="t('mvMusicPromptPlaceholder')"
            ></textarea>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label class="block text-xs text-muted mb-1" for="mv-suno-model">{{ t('mvSunoModel') }}</label>
              <select id="mv-suno-model" v-model="form.sunoModel" class="w-full glass-input rounded-lg px-3 py-2 text-xs text-ink">
                <option value="V6">Suno V6</option>
                <option value="V6_WILD">Suno V6 Wild</option>
                <option value="V6_MINI">Suno V6 Mini</option>
                <option value="V5">Suno V5</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-muted mb-1" for="mv-music-style">{{ t('mvMusicStyle') }}</label>
              <input
                id="mv-music-style"
                v-model="form.musicStyle"
                class="w-full glass-input rounded-lg px-3 py-2 text-xs text-ink placeholder-muted"
                placeholder="Synthwave, Indie Rock..."
              />
            </div>
            <div class="flex items-end pb-1">
              <NeuSwitch v-model="form.instrumental" :label="t('mvInstrumental')" />
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 pt-2 border-t border-rule/50">
          <div>
            <label class="block text-xs text-muted mb-1" for="mv-trim-start">{{ t('mvTrimStart') }}</label>
            <input id="mv-trim-start" v-model.number="form.trimStartSec" type="number" min="0" step="0.5" class="w-full glass-input rounded-lg px-3 py-1.5 text-xs text-ink" />
          </div>
          <div>
            <label class="block text-xs text-muted mb-1" for="mv-trim-end">{{ t('mvTrimEnd') }}</label>
            <input id="mv-trim-end" v-model.number="form.trimEndSec" type="number" min="0" step="0.5" class="w-full glass-input rounded-lg px-3 py-1.5 text-xs text-ink" />
          </div>
        </div>
      </div>

      <!-- Visual Style & Camera -->
      <div>
        <label class="block text-sm text-muted font-medium mb-1.5" for="mv-style">{{ t('visualStyle') }}</label>
        <StylePresetChips v-model="form.visualStyle" class="mb-2" />
        <div class="flex items-center gap-2">
          <input id="mv-style" v-model="form.visualStyle" class="flex-1 glass-input rounded-lg px-4 py-2.5 text-sm text-ink placeholder-muted" />
          <PresetPicker v-model="form.visualStyle" />
        </div>
      </div>

      <div>
        <label class="block text-sm text-muted font-medium mb-1.5">{{ t('cameraMovementLabel') }}</label>
        <CameraMovementPicker v-model="form.cameraMovement" />
      </div>
    </div>

    <div class="glass-card rounded-2xl p-6 mb-4 space-y-4">
      <h2 class="text-lg font-semibold text-accent">{{ t('advancedSettings') }}</h2>

      <div>
        <label class="block text-sm text-muted font-medium mb-2">{{ t('resolution') }}</label>
        <AspectPicker v-model="form.resolution" />
      </div>

      <LutSelector v-model="form.lutId" />

      <AssetLibraryPicker :selected-id="form.selectedAssetId" @select="onSelectAsset" />

      <div>
        <label class="block text-sm text-muted font-medium mb-1.5">{{ t('referenceImage') }}</label>
        <DropzoneCard
          v-model="form.refImage"
          :title="t('referenceImage')"
          :hint="t('refDescription')"
          badge="MV Ref"
        />
      </div>
    </div>

    <WatermarkToggle />

    <button
      type="button"
      class="w-full py-3.5 rounded-xl text-base font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed glow-btn"
      :disabled="submitting"
      @click="submitMv"
    >
      {{ submitting ? t('submitting') : t('startGenerate') }}
    </button>
  </div>
</template>
