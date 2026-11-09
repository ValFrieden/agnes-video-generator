<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { t } from '@/i18n'
import { appState } from '@/store'
import { useGa } from '@/composables/useGa'
import { useVideoModelCaps, MODE_V25_TO_API, normalizeResolution } from '@/composables/useVideoModelCaps'
import { useConfig } from '@/composables/useConfig'
import { useTaskSubmit } from '@/composables/useTaskSubmit'
import { useDraft } from '@/composables/useDraft'
import WatermarkToggle from '@/components/shared/WatermarkToggle.vue'
import DropzoneCard from '@/components/shared/DropzoneCard.vue'
import InfoTooltip from '@/components/shared/InfoTooltip.vue'
import CameraMovementPicker from '@/components/presets/CameraMovementPicker.vue'

const { trackEvent } = useGa()
const { saveModels } = useConfig()

// 3.1：视频/图片两个提交独立守卫
const videoSubmit = useTaskSubmit()
const imageSubmit = useTaskSubmit()

// 3.4：表单草稿（切走/刷新不丢失，提交成功清除）
const videoDraft = useDraft('simple-video')
const imageDraft = useDraft('simple-image')

// v6.2：视频模型能力（动态选项 + 差异说明）
const vmCaps = useVideoModelCaps()

// Sub-mode: video / image
const subMode = ref<'video' | 'image'>('video')

// Video form
const video = reactive({
  prompt: '',
  mode: 't2v',
  duration: '5',
  resolution: '768x1152', // v2.0：像素分辨率
  ratio: '9:16',          // 2.5 系列：画幅比例（默认竖屏，对齐原 768x1152）
  size: '720P',           // 2.5 系列：清晰度档位
  seed: '',
  negative: '',
  system: '',
  refImage: null as File | null,
  refName: '',
  endImage: null as File | null,
  endName: '',
  cameraMovement: '',
  draftMode: false,
})

// Image form
const image = reactive({
  prompt: '',
  size: '1024x1024',
  negative: '',
  system: '',
  refImage: null as File | null,
  refName: '',
  imageResultVisible: false,
  imageResultSrc: '',
})

const advancedCollapsed = reactive({ video: true, image: true })

// 3.4：恢复草稿（仅 JSON 安全字段）
;(() => {
  const vd = videoDraft.load()
  if (vd) {
    if (typeof vd.prompt === 'string') video.prompt = vd.prompt
    if (typeof vd.mode === 'string') video.mode = vd.mode
    if (typeof vd.duration === 'string') video.duration = vd.duration
    if (typeof vd.resolution === 'string') video.resolution = normalizeResolution(vd.resolution)
    if (typeof vd.ratio === 'string') video.ratio = vd.ratio
    if (typeof vd.size === 'string') video.size = vd.size
    if (typeof vd.seed === 'string') video.seed = vd.seed
    if (typeof vd.negative === 'string') video.negative = vd.negative
    if (typeof vd.system === 'string') video.system = vd.system
  }
  const id = imageDraft.load()
  if (id) {
    if (typeof id.prompt === 'string') image.prompt = id.prompt
    if (typeof id.size === 'string') image.size = id.size
    if (typeof id.negative === 'string') image.negative = id.negative
    if (typeof id.system === 'string') image.system = id.system
  }
})()
videoDraft.autoSave(video, (v) => ({
  prompt: v.prompt, mode: v.mode, duration: v.duration, resolution: v.resolution,
  ratio: v.ratio, size: v.size, seed: v.seed, negative: v.negative, system: v.system,
}))
imageDraft.autoSave(image, (v) => ({
  prompt: v.prompt, size: v.size, negative: v.negative, system: v.system,
}))

// ── 按所选视频模型动态派生选项 ──
const currentVideoModel = computed(() => appState.models.video || '')
const isV25 = computed(() => vmCaps.isV25Model(currentVideoModel.value))
const modeOptions = computed(() => vmCaps.modeOptions(currentVideoModel.value))
const durationOptions = computed(() => vmCaps.durationOptions(currentVideoModel.value))
const ratioOptions = computed(() => vmCaps.ratioOptions(currentVideoModel.value))
const sizeOptions = computed(() => vmCaps.sizeOptions(currentVideoModel.value))
const pixelOptions = computed(() => vmCaps.pixelOptions(currentVideoModel.value))

// 参考图/尾帧显隐（按模型 + 模式语义统一）
const needsRefImage = computed(() => {
  const m = video.mode
  return isV25.value ? m === 'reference' || m === 'keyframe' : m !== 't2v'
})
const needsEndFrame = computed(() => {
  const m = video.mode
  return isV25.value ? m === 'keyframe' : m === 'keyframes'
})

// 模型切换 → 修正表单默认值（选项集变化时避免非法值）
watch(currentVideoModel, (model, old) => {
  if (model === old) return
  const ms = modeOptions.value
  if (ms.length && !ms.some((x) => x.id === video.mode)) {
    video.mode = ms[0].id
  }
  const ds = durationOptions.value
  const cur = Number(video.duration)
  if (ds.length && !ds.includes(cur)) {
    video.duration = String(ds[0])
  }
  if (isV25.value) {
    // 2.5 系列：比例与 size 对齐能力
    if (ratioOptions.value.length && !ratioOptions.value.includes(video.ratio)) {
      video.ratio = '9:16'
    }
    if (sizeOptions.value.length && !sizeOptions.value.includes(video.size)) {
      video.size = sizeOptions.value[0]
    }
  }
})

function toggleCollapse(key: 'video' | 'image') {
  advancedCollapsed[key] = !advancedCollapsed[key]
}

function onRefImageChange(e: Event, target: 'video' | 'image') {
  const file = (e.target as HTMLInputElement).files?.[0] || null
  if (target === 'video') {
    video.refImage = file
    video.refName = file ? file.name : ''
  } else {
    image.refImage = file
    image.refName = file ? file.name : ''
  }
}

function onEndImageChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0] || null
  video.endImage = file
  video.endName = file ? file.name : ''
}

function parseResolution(val: string) {
  const [w, h] = val.split('x').map(Number)
  return { width: w, height: h }
}

// 模型选择即保存（与 ConfigPanel 联动同一全局状态）
async function onVideoModelChange(e: Event) {
  const model = (e.target as HTMLSelectElement).value
  if (!model) return
  appState.models.video = model
  trackEvent('config_action', { action: 'select_video_model', video_model: model })
  await saveModels()
}

async function submitSimple() {
  await videoSubmit.runSubmit({
    taskType: 'simple',
    buildForm: () => {
      const prompt = video.prompt.trim()
      if (!prompt) throw new Error(t('enterPrompt'))
      const form = new FormData()
      form.append('prompt', prompt)
      // 2.5 系列模式映射：text→t2v / reference→i2v / keyframe→keyframes
      form.append('mode', isV25.value ? MODE_V25_TO_API[video.mode] || 't2v' : video.mode)
      form.append('duration', video.duration)
      if (isV25.value) {
        // 2.5 系列：比例 → 720P 基准像素 + 清晰度档位
        const [w, h] = vmCaps.ratioToWH(video.ratio, currentVideoModel.value)
        form.append('video_width', String(w))
        form.append('video_height', String(h))
        form.append('video_size', video.size)
      } else {
        const res = parseResolution(video.resolution)
        form.append('video_width', String(res.width))
        form.append('video_height', String(res.height))
      }
      if (video.cameraMovement) form.append('camera_movement', video.cameraMovement)
      form.append('draft_mode', String(video.draftMode))
      if (video.seed) form.append('seed', video.seed)
      // 2.5 系列不支持负面提示词，不提交
      if (!isV25.value && video.negative) form.append('negative_prompt', video.negative)
      if (video.system.trim()) form.append('system_prompt', video.system.trim())
      if (video.refImage) form.append('reference_image', video.refImage)
      if (video.endImage) form.append('end_frame_image', video.endImage)
      return form
    },
    extraEvent: {
      mode: video.mode,
      duration: video.duration,
      resolution: isV25.value ? video.ratio + '/' + video.size : video.resolution,
      video_model: currentVideoModel.value,
    },
    onSuccess: () => videoDraft.clear(),
  })
}

async function submitImage() {
  await imageSubmit.runSubmit({
    taskType: 'simple_image',
    eventTaskType: 'image',
    buildForm: () => {
      const prompt = image.prompt.trim()
      if (!prompt) throw new Error(t('enterImagePrompt'))
      const form = new FormData()
      form.append('prompt', prompt)
      form.append('size', image.size)
      if (image.negative) form.append('negative_prompt', image.negative)
      if (image.system.trim()) form.append('system_prompt', image.system.trim())
      if (image.refImage) form.append('reference_image', image.refImage)
      return form
    },
    extraEvent: { size: image.size },
    successMessage: t('imgComplete'),
    onSubmit: (d) => {
      image.imageResultSrc = '/api/image/' + d.task_id
      image.imageResultVisible = true
    },
    onSuccess: () => imageDraft.clear(),
  })
}
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-4 text-xs text-muted">
      <svg class="w-3.5 h-3.5 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <a href="https://video.lichuanyang.top/guides/prompt-examples-simple" target="_blank" rel="noopener" class="hover:text-accent transition-colors">{{ t('exampleLinkSimple') }}</a>
    </div>

    <!-- Sub-mode selector (Clean Studio Segmented Control) -->
    <div class="glass-card rounded-xl p-1 mb-4 flex items-center justify-center gap-1.5">
      <button
        type="button"
        class="flex-1 py-2 px-4 rounded-lg text-sm font-semibold transition flex items-center justify-center gap-2 cursor-pointer"
        :class="subMode === 'video' ? 'bg-paper-3 text-ink border border-rule' : 'text-muted hover:text-ink'"
        @click="subMode = 'video'"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M4 6h8a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2z" />
        </svg>
        <span>{{ t('subModeVideo').replace(/^[^\w\s\u4e00-\u9fa5]+/, '').trim() }}</span>
      </button>
      <button
        type="button"
        class="flex-1 py-2 px-4 rounded-lg text-sm font-semibold transition flex items-center justify-center gap-2 cursor-pointer"
        :class="subMode === 'image' ? 'bg-paper-3 text-ink border border-rule' : 'text-muted hover:text-ink'"
        @click="subMode = 'image'"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span>{{ t('subModeImage').replace(/^[^\w\s\u4e00-\u9fa5]+/, '').trim() }}</span>
      </button>
    </div>

    <!-- Video sub-form -->
    <div v-if="subMode === 'video'">
      <div class="glass-card rounded-2xl p-6 mb-4">
        <h2 class="text-lg font-semibold text-accent mb-4">{{ t('simpleSettings') }}</h2>

        <!-- v6.2：视频模型选择（选模型阶段差异说明） -->
        <div class="mb-4 rounded-xl bg-paper-3/50 p-3">
          <label class="block text-sm text-muted mb-1.5">{{ t('vmModelSelect') }}</label>
          <select :value="appState.models.video" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink" @change="onVideoModelChange">
            <option v-for="m in appState.modelListCache.video" :key="m" :value="m">{{ m }}{{ vmCaps.isAdapted(m) ? '' : ' [!]' }}</option>
          </select>
          <!-- v7.0 U8：当前版本未适配的模型显式提示（不再静默按 v2.0 协议提交） -->
          <p v-if="!vmCaps.isAdapted(currentVideoModel)" class="text-xs text-amber-400 mt-1.5">{{ t('vmUnadaptedHint') }}</p>
          <!-- 当前模型能力说明 -->
          <div class="mt-2.5 space-y-1 text-xs">
            <p class="text-sm text-ink-2 font-medium">{{ vmCaps.capsOf(currentVideoModel).label || currentVideoModel }}</p>
            <p v-if="vmCaps.priceText(currentVideoModel)" class="text-green-400">{{ vmCaps.priceText(currentVideoModel) }}</p>
            <p class="text-muted">{{ vmCaps.descOf(currentVideoModel) }}</p>
            <p v-if="isV25" class="text-muted">{{ t('vm720pHint') }}</p>
            <div class="flex flex-wrap gap-x-4 gap-y-0.5 pt-1">
              <span class="text-muted">{{ t('vmModelModesLabel') }}: <span class="text-ink-2">{{ vmCaps.modeOptions(currentVideoModel).map((x) => x.label).join(' · ') }}</span></span>
              <span class="text-muted">{{ t('vmModelDurationsLabel') }}: <span class="text-ink-2">{{ vmCaps.durationOptions(currentVideoModel).map((x) => x + 's').join(' / ') }}</span></span>
              <span class="text-muted">{{ t('vmModelResLabel') }}: <span class="text-ink-2">
                <template v-if="isV25">{{ vmCaps.ratioOptions(currentVideoModel).map((r) => vmCaps.ratioWHText(r, currentVideoModel)).join(' / ') }}<template v-if="vmCaps.sizeOptions(currentVideoModel).length > 1">（{{ vmCaps.sizeOptions(currentVideoModel).join(' / ') }}）</template></template>
                <template v-else>{{ vmCaps.pixelOptions(currentVideoModel).map((x) => x.value).join(' / ') }}</template>
              </span></span>
              <span class="text-muted">{{ t('vmModelNegativeLabel') }}: <span class="text-ink-2">{{ vmCaps.supportsNegative(currentVideoModel) ? t('vmYes') : t('vmNo') }}</span></span>
              <span v-if="vmCaps.maxRefImages(currentVideoModel)" class="text-muted">{{ t('vmModelRefImagesLabel') }}: <span class="text-ink-2">≤ {{ vmCaps.maxRefImages(currentVideoModel) }}</span></span>
              <span class="text-muted">{{ t('vmModelRefVideoLabel') }}: <span class="text-ink-2">{{ vmCaps.supportsRefVideo(currentVideoModel) ? t('vmYes') : t('vmNo') }}</span></span>
            </div>
            <p v-if="!vmCaps.supportsNegative(currentVideoModel)" class="text-amber-400 pt-0.5">{{ t('vmModelNegativeUnsupported') }}</p>
          </div>
        </div>

        <div class="mb-4">
          <label class="block text-sm text-muted mb-1.5">{{ t('promptLabel') }} (prompt) <span class="text-red-400">*</span></label>
          <textarea v-model="video.prompt" rows="3" :placeholder="t('promptPlaceholder')" class="w-full glass-input rounded-lg px-4 py-2.5 text-sm resize-y text-ink placeholder-muted"></textarea>
        </div>

        <!-- 20 Cinematic Camera Movements (SYNTX AI) -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-sm text-muted font-medium">Кинематографическое движение камеры (SYNTX)</label>
            <InfoTooltip text="20 операторских пресетов (Dolly In, Orbital Pan, Snorricam, Vertigo, Crane): задает физику и кинематографическую траекторию камеры." />
          </div>
          <CameraMovementPicker v-model="video.cameraMovement" />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label class="block text-sm text-muted mb-1.5">{{ t('genMode') }}</label>
            <select v-model="video.mode" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink">
              <option v-for="opt in modeOptions" :key="opt.id" :value="opt.id">{{ opt.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm text-muted mb-1.5">{{ t('duration') }}</label>
            <select v-model="video.duration" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink">
              <option v-for="d in durationOptions" :key="d" :value="String(d)">{{ d }}s</option>
            </select>
          </div>
          <!-- 分辨率：v2.0 像素档位；2.5 系列 比例 + 清晰度 -->
          <div v-if="!isV25">
            <label class="block text-sm text-muted mb-1.5">{{ t('resolution') }}</label>
            <select v-model="video.resolution" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink">
              <option v-for="opt in pixelOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <template v-else>
            <div>
              <label class="block text-sm text-muted mb-1.5">{{ t('vmRatioLabel') }} <span class="text-muted/70">({{ t('vmRatioHint') }})</span></label>
              <select v-model="video.ratio" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink">
                <option v-for="r in ratioOptions" :key="r" :value="r">{{ vmCaps.ratioWHText(r, currentVideoModel) }}</option>
              </select>
            </div>
            <div v-if="sizeOptions.length > 1">
              <label class="block text-sm text-muted mb-1.5">{{ t('vmSizeLabel') }}</label>
              <select v-model="video.size" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink">
                <option v-for="s in sizeOptions" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
          </template>
        </div>

        <!-- v7.0 U3：2.5 系列竖屏（9:16）上游画面旋转缺陷提示（零风险：先提示不自动修） -->
        <p v-if="isV25 && video.ratio === '9:16'" class="text-xs text-amber-400 mb-4">{{ t('vmPortraitRotateHint') }}</p>

        <!-- Reference Image with Dropzone -->
        <div v-if="needsRefImage" class="mb-4">
          <label class="block text-sm text-muted font-medium mb-1.5">{{ t('refImageSimple') }}</label>
          <DropzoneCard
            v-model="video.refImage"
            :title="t('refImageSimple')"
            :badge="t('badgeStartFrame') || 'Start / Ref'"
            @change="(f) => video.refName = f ? f.name : ''"
          />
          <p v-if="vmCaps.maxRefImages(currentVideoModel)" class="text-xs text-muted mt-1">{{ t('vmRefImagesHint') }} ≤ {{ vmCaps.maxRefImages(currentVideoModel) }}</p>
        </div>

        <!-- End Frame with Dropzone -->
        <div v-if="needsEndFrame" class="mb-4">
          <label class="block text-sm text-muted font-medium mb-1.5">{{ t('endFrameImage') }}</label>
          <DropzoneCard
            v-model="video.endImage"
            :title="t('endFrameImage')"
            :badge="t('badgeEndFrame') || 'End Frame'"
            @change="(f) => video.endName = f ? f.name : ''"
          />
        </div>

        <!-- Advanced -->
        <div class="border-t border-rule/40 pt-4 mt-4">
          <div class="collapse-header flex items-center justify-between" @click="toggleCollapse('video')">
            <span class="text-sm text-muted">{{ t('advancedSettings') }}</span>
            <span class="text-muted text-xs">{{ advancedCollapsed.video ? '▶' : '▼' }}</span>
          </div>
          <div v-show="!advancedCollapsed.video" class="mt-3">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm text-muted mb-1.5">Seed ({{ t('optional') }})</label>
                <input v-model="video.seed" type="number" :placeholder="t('seedPlaceholder')" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink" />
              </div>
              <div v-if="vmCaps.supportsNegative(currentVideoModel)">
                <label class="block text-sm text-muted mb-1.5">Negative Prompt ({{ t('optional') }})</label>
                <input v-model="video.negative" :placeholder="t('negativePlaceholder')" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink" />
              </div>
              <div v-else class="md:col-span-2">
                <label class="block text-sm text-muted mb-1.5">Negative Prompt</label>
                <input disabled :placeholder="t('vmNegativeDisabledPlaceholder')" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink opacity-50 cursor-not-allowed" />
              </div>
            </div>
            <div class="mt-4">
              <label class="block text-sm text-muted mb-1.5">{{ t('systemPrompt') }} ({{ t('optional') }})</label>
              <textarea v-model="video.system" rows="2" :placeholder="t('systemPromptPlaceholder')" class="w-full glass-input rounded-lg px-4 py-2.5 text-sm resize-y text-ink placeholder-muted"></textarea>
            </div>
          </div>
        </div>
      </div>

      <WatermarkToggle />

      <button
        class="w-full py-3.5 bg-accent text-accent-ink hover:bg-accent/90 rounded-xl text-base font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed glow-btn"
        :disabled="videoSubmit.submitting.value"
        @click="submitSimple"
      >
        {{ videoSubmit.submitting.value ? t('submitting') : t('startGenerate') }}
      </button>
    </div>

    <!-- Image sub-form -->
    <div v-else>
      <div class="glass-card rounded-2xl p-6 mb-4">
        <h2 class="text-lg font-semibold text-accent mb-4">{{ t('imageSettings') }}</h2>

        <div class="mb-4">
          <label class="block text-sm text-muted mb-1.5">{{ t('imagePrompt') }} (prompt) <span class="text-red-400">*</span></label>
          <textarea v-model="image.prompt" rows="3" :placeholder="t('imagePromptPlaceholder')" class="w-full glass-input rounded-lg px-4 py-2.5 text-sm resize-y text-ink placeholder-muted"></textarea>
        </div>

        <div class="mb-4">
          <label class="block text-sm text-muted mb-1.5">{{ t('imageSize') }}</label>
          <select v-model="image.size" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink">
            <option value="1024x1024">{{ t('resSquare') }} (1024x1024)</option>
            <option value="768x1152">{{ t('resPortrait') }} (768x1152)</option>
            <option value="1280x720">{{ t('resLandscape') }} (1280x720)</option>
            <option value="768x1344">{{ t('resPortraitHD') }} (HD)</option>
            <option value="1344x768">{{ t('resLandscapeHD') }} (HD)</option>
            <option value="1024x1792">{{ t('resPortraitTall') }}</option>
            <option value="1792x1024">{{ t('resLandscapeWide') }}</option>
          </select>
        </div>

        <div class="mb-4">
          <label class="block text-sm text-muted font-medium mb-1.5">{{ t('refImageSimple') }}</label>
          <DropzoneCard
            v-model="image.refImage"
            :title="t('refImageSimple')"
            :hint="t('refImageHint')"
            :badge="t('badgeRefGen') || 'Reference'"
            @change="(f) => image.refName = f ? f.name : ''"
          />
        </div>

        <div class="border-t border-rule/40 pt-4 mt-4">
          <div class="collapse-header flex items-center justify-between" @click="toggleCollapse('image')">
            <span class="text-sm text-muted">{{ t('advancedSettings') }}</span>
            <span class="text-muted text-xs">{{ advancedCollapsed.image ? '▶' : '▼' }}</span>
          </div>
          <div v-show="!advancedCollapsed.image" class="mt-3">
            <div>
              <label class="block text-sm text-muted mb-1.5">Negative Prompt ({{ t('optional') }})</label>
              <input v-model="image.negative" :placeholder="t('negativePlaceholder')" class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink" />
            </div>
            <div class="mt-4">
              <label class="block text-sm text-muted mb-1.5">{{ t('systemPrompt') }} ({{ t('optional') }})</label>
              <textarea v-model="image.system" rows="2" :placeholder="t('systemPromptPlaceholder')" class="w-full glass-input rounded-lg px-4 py-2.5 text-sm resize-y text-ink placeholder-muted"></textarea>
            </div>
          </div>
        </div>
      </div>

      <button
        class="w-full py-3.5 bg-accent text-accent-ink hover:bg-accent/90 rounded-xl text-base font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed glow-btn"
        :disabled="imageSubmit.submitting.value"
        @click="submitImage"
      >
        {{ imageSubmit.submitting.value ? t('submitting') : t('imgGenerate') }}
      </button>

      <div v-if="image.imageResultVisible" class="mt-4 p-4 glass-card rounded-lg">
        <p class="text-green-400 text-sm font-medium mb-2">{{ t('imgComplete') }}</p>
        <img :src="image.imageResultSrc" class="w-full rounded-lg max-h-96 object-contain" />
      </div>
    </div>
  </div>
</template>
