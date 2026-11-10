<script setup lang="ts">
import { ref, computed } from 'vue'
import { t } from '@/i18n'
import { extractScenes } from '@/api'
import { useToast } from '@/composables/useToast'
import type { GalleryItem } from '@/types'

const props = defineProps<{
  videos: GalleryItem[]
}>()

const { showToast } = useToast()

const open = ref(false)
const videoPath = ref('')
const threshold = ref(0.15)
const maxScenes = ref(20)
const busy = ref(false)
const result = ref<{ scene_count: number; output_dir: string; scenes: any[] } | null>(null)

const completedVideos = computed(() =>
  props.videos.filter((v) => v.kind === 'video' && v.status === 'completed' && v.dir_name),
)

function pickGalleryVideo(e: Event) {
  const dir = (e.target as HTMLSelectElement).value
  if (dir) videoPath.value = `${dir}/final_video.mp4`
}

async function runExtract() {
  const path = videoPath.value.trim()
  if (!path) {
    showToast(t('extractPathRequired'), 2500, 'error')
    return
  }
  busy.value = true
  result.value = null
  try {
    const res = await extractScenes({
      video_path: path,
      threshold: Number(threshold.value) || 0.15,
      max_scenes: Number(maxScenes.value) || 20,
    })
    if (res?.ok) {
      result.value = {
        scene_count: res.scene_count,
        output_dir: res.output_dir,
        scenes: res.scenes || [],
      }
      showToast(t('extractSuccess').replace('{n}', String(res.scene_count)), 3000, 'success')
    }
  } catch (e: any) {
    showToast(e?.message || t('failCreate'), 4000, 'error')
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="glass-card rounded-2xl p-4 mt-6 border border-rule">
    <button
      type="button"
      class="w-full flex items-center justify-between text-left"
      :aria-expanded="open"
      @click="open = !open"
    >
      <div>
        <h3 class="text-sm font-semibold text-ink">{{ t('extractTitle') }}</h3>
        <p class="text-xs text-muted">{{ t('extractSubtitle') }}</p>
      </div>
      <span class="text-xs text-muted">{{ open ? '▲' : '▼' }}</span>
    </button>

    <div v-if="open" class="mt-4 pt-4 border-t border-rule/50 space-y-3">
      <div v-if="completedVideos.length" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs text-muted mb-1">{{ t('extractPickVideo') }}</label>
          <select class="w-full glass-input rounded-lg px-3 py-2 text-xs text-ink" @change="pickGalleryVideo">
            <option value="">{{ t('extractChooseOption') }}</option>
            <option v-for="v in completedVideos" :key="v.task_id" :value="v.dir_name">
              {{ v.title || v.task_id }} ({{ v.dir_name }})
            </option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-muted mb-1">{{ t('extractVideoPath') }}</label>
          <input
            v-model="videoPath"
            class="w-full glass-input rounded-lg px-3 py-2 text-xs text-ink font-mono placeholder-muted"
            placeholder="20261110_.../final_video.mp4"
          />
        </div>
      </div>
      <div v-else>
        <label class="block text-xs text-muted mb-1">{{ t('extractVideoPath') }}</label>
        <input
          v-model="videoPath"
          class="w-full glass-input rounded-lg px-3 py-2 text-xs text-ink font-mono placeholder-muted"
          placeholder="20261110_.../final_video.mp4"
        />
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 items-end">
        <div>
          <label class="block text-xs text-muted mb-1">{{ t('extractThreshold') }}</label>
          <input v-model.number="threshold" type="number" min="0.05" max="0.9" step="0.05" class="w-full glass-input rounded-lg px-3 py-1.5 text-xs text-ink" />
        </div>
        <div>
          <label class="block text-xs text-muted mb-1">{{ t('extractMaxScenes') }}</label>
          <input v-model.number="maxScenes" type="number" min="1" max="50" class="w-full glass-input rounded-lg px-3 py-1.5 text-xs text-ink" />
        </div>
        <button
          type="button"
          class="px-4 py-2 rounded-lg text-xs font-semibold glow-btn disabled:opacity-50"
          :disabled="busy"
          @click="runExtract"
        >
          {{ busy ? t('loading') : t('extractBtn') }}
        </button>
      </div>

      <div v-if="result" class="p-3 rounded-xl bg-paper border border-rule space-y-1 text-xs">
        <p class="font-semibold text-success">{{ t('extractSuccess').replace('{n}', String(result.scene_count)) }}</p>
        <p class="text-muted font-mono break-all">{{ result.output_dir }}</p>
      </div>
    </div>
  </section>
</template>
