<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { t } from '@/i18n'
import { useArtifacts } from '@/composables/useArtifacts'
import { copyText } from '@/utils/clipboard'
import type { Artifact } from '@/types'

const props = defineProps<{ art: Artifact; large?: boolean }>()

const {
  isRunning,
  artifactLabel,
  artifactIcon,
  artifactFileUrl,
  formatSize,
  toggleArtifactPreview,
  openImageModal,
  confirmDeleteArtifact,
} = useArtifacts()

const previewExpanded = ref(false)
const previewText = ref('')
const previewLoading = ref(false)

// 文本 / JSON / 字幕类产物：默认自动展开预览
async function loadPreview() {
  previewExpanded.value = true
  previewLoading.value = true
  previewText.value = ''
  try {
    const resp = await fetch(artifactFileUrl(props.art))
    let text = await resp.text()
    if (text.length > 2000) text = text.substring(0, 2000) + '\n...'
    previewText.value = text
  } catch (err: any) {
    previewText.value = 'Error: ' + err.message
  } finally {
    previewLoading.value = false
  }
}

async function onPreviewClick(e: Event) {
  const el = e.currentTarget as HTMLElement
  if (previewExpanded.value) {
    previewExpanded.value = false
    previewText.value = ''
  } else {
    await loadPreview()
  }
  void el
}

onMounted(() => {
  const cat = props.art.category
  if (cat !== 'image' && cat !== 'video' && cat !== 'audio') {
    loadPreview()
  }
})

async function onCopyPath() {
  const p = (props.art as any).abs_path || (props.art as any).path || ''
  if (!p) return
  await copyText(p)
}
</script>

<template>
  <div class="artifact-card flex items-start gap-3.5 p-3.5 neu-raised rounded-2xl border border-rule/30 mb-2.5">
    <div class="mt-0.5 shrink-0 text-accent">
      <svg v-if="art.category === 'video'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
      <svg v-else-if="art.category === 'image'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
      <svg v-else-if="art.category === 'audio'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"/></svg>
      <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
    </div>
    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2 mb-1">
        <span class="text-xs text-ink-2 truncate">{{ artifactLabel(art) }}</span>
        <span class="text-xs text-muted shrink-0">{{ formatSize(art.size) }}</span>
      </div>

      <!-- 图片预览 -->
      <img
        v-if="art.category === 'image'"
        :src="artifactFileUrl(art)"
        class="rounded-lg cursor-pointer border border-rule/50"
        :class="large ? 'w-full max-h-[400px]' : 'max-h-36'"
        loading="lazy"
        @click="openImageModal(artifactFileUrl(art))"
      />
      <!-- 视频预览 -->
      <video
        v-else-if="art.category === 'video'"
        :src="artifactFileUrl(art)"
        controls
        playsinline
        preload="metadata"
        class="w-full rounded-lg border border-rule/50 bg-black"
        :style="large ? 'max-height: 460px' : 'max-height: 260px'"
      ></video>
      <!-- 音频预览 -->
      <audio v-else-if="art.category === 'audio'" :src="artifactFileUrl(art)" controls class="w-full" preload="metadata"></audio>
      <!-- 文本 / JSON 预览 -->
      <pre
        v-else
        class="text-xs text-muted overflow-auto bg-paper/70 p-2 rounded-lg border border-rule/40 cursor-pointer whitespace-pre-wrap"
        :class="large ? 'max-h-64' : 'max-h-24'"
        @click="onPreviewClick"
      >{{ previewExpanded ? (previewLoading ? t('loading') + '...' : previewText) : t('clickToPreview') }}</pre>

      <!-- 路径复制 -->
      <div
        v-if="(art as any).abs_path || (art as any).path"
        class="mt-1.5 text-[10px] text-muted font-mono truncate cursor-pointer hover:text-ink-2 transition"
        :title="t('copy')"
        @click="onCopyPath"
      >{{ (art as any).abs_path || (art as any).path }}</div>
    </div>

    <!-- 删除 -->
    <button
      v-if="art.deletable && !isRunning"
      class="text-xs p-1.5 neu-raised hover:neu-sunken text-danger rounded-xl transition shrink-0 flex items-center justify-center cursor-pointer"
      :title="t('delete')"
      @click="confirmDeleteArtifact(art)"
    >
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
</template>
