<script setup lang="ts">
import { computed } from 'vue'
import { t } from '@/i18n'
import { useProgress } from '@/composables/useProgress'

const props = defineProps<{ horizontal?: boolean }>()
const emit = defineEmits<{ (e: 'locate', stepKey: string): void }>()

const { steps, stepStates, awaitingCheckpoint } = useProgress()

// checkpoint -> 最近似的 step key（用于暂停时在时间线中高亮对应环节）
const CHECKPOINT_TO_STEP: Record<string, string> = {
  image_analysis: 'image_analysis',
  story: 'story',
  script: 'script',
  character_ref: 'character_ref',
  end_frame_prompts: 'end_frame_prompts',
  end_frame_gen: 'end_frame_gen',
  scenes: 'script',
  references: 'character_ref',
  videos: 'video_gen',
  audio: 'audio',
  subtitle: 'subtitle',
  final: 'concatenate',
}

const checkpointLabelKey: Record<string, string> = {
  image_analysis: 'cpImageAnalysis',
  story: 'cpStory',
  script: 'cpScript',
  character_ref: 'cpCharacterRef',
  end_frame_prompts: 'cpEndFramePrompts',
  end_frame_gen: 'cpEndFrameGen',
  scenes: 'cpScenes',
  references: 'cpReferences',
  videos: 'cpVideos',
  audio: 'cpAudio',
  subtitle: 'cpSubtitle',
  final: 'cpFinal',
}

type Item = { key: string; label: string; state: 'done' | 'running' | 'awaiting' | 'pending' }

const items = computed<Item[]>(() => {
  const cp = awaitingCheckpoint.value
  const highlightStep = cp ? CHECKPOINT_TO_STEP[cp] : ''
  const hasHighlight = cp && highlightStep && steps.value.some((s) => s.key === highlightStep)

  const list: Item[] = steps.value.map((s) => {
    let state: Item['state'] = stepStates.value[s.key] || 'pending'
    if (cp && hasHighlight && s.key === highlightStep) state = 'awaiting'
    return { key: s.key, label: t(s.labelKey), state }
  })

  // 暂停点无对应 step 时，在末尾追加独立条目
  if (cp && !hasHighlight) {
    list.push({ key: cp, label: t(checkpointLabelKey[cp] || cp), state: 'awaiting' })
  }
  return list
})

function onLocate(item: Item) {
  if (item.state !== 'pending') emit('locate', item.key)
}

function clsFor(state: Item['state']): string {
  if (state === 'done') return 'text-success'
  if (state === 'running') return 'text-accent'
  if (state === 'awaiting') return 'text-warning'
  return 'text-muted'
}
</script>

<template>
  <div v-if="!props.horizontal" class="neu-card rounded-2xl p-4 border border-rule/30">
    <div class="text-xs font-semibold text-muted mb-3">{{ t('ppStages') }}</div>
    <div class="space-y-1">
      <button
        v-for="item in items"
        :key="item.key"
        class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left text-sm transition"
        :class="[
          item.state === 'awaiting' ? 'neu-sunken border-amber-500/40 text-warning font-medium' : '',
          item.state === 'running' ? 'neu-raised text-accent font-medium border border-accent/20' : '',
          item.state !== 'awaiting' && item.state !== 'running' ? 'hover:neu-sunken text-ink-2' : '',
        ]"
        @click="onLocate(item)"
      >
        <span class="w-4 h-4 flex items-center justify-center shrink-0" :class="clsFor(item.state)">
          <svg v-if="item.state === 'done'" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
          <span v-else-if="item.state === 'running'" class="w-2 h-2 rounded-full bg-accent animate-pulse"></span>
          <span v-else-if="item.state === 'awaiting'" class="w-2 h-2 rounded-full bg-warning"></span>
          <span v-else class="w-1.5 h-1.5 rounded-full bg-rule"></span>
        </span>
        <span class="truncate" :class="item.state === 'awaiting' ? 'text-warning font-medium' : ''">{{ item.label }}</span>
        <span v-if="item.state === 'awaiting'" class="ml-auto text-[10px] text-warning shrink-0 px-2 py-0.5 rounded-full neu-sunken">{{ t('ppWaiting') }}</span>
      </button>
    </div>
  </div>

  <!-- 移动端：横向滚动胶囊 -->
  <div v-else class="flex gap-2 overflow-x-auto pb-2 -mx-1 px-1">
    <button
      v-for="item in items"
      :key="item.key"
      class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs whitespace-nowrap transition neu-raised hover:neu-sunken"
      :class="[
        item.state === 'awaiting' ? 'neu-sunken border-amber-500/40 text-warning font-medium' : 'text-ink-2',
        item.state === 'running' ? 'text-accent font-medium' : '',
        item.state === 'done' ? 'text-success' : '',
      ]"
      @click="onLocate(item)"
    >
      <span class="w-3.5 h-3.5 flex items-center justify-center shrink-0">
        <svg v-if="item.state === 'done'" class="w-3 h-3 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
        <span v-else-if="item.state === 'running'" class="w-1.5 h-1.5 rounded-full bg-accent animate-pulse"></span>
        <span v-else-if="item.state === 'awaiting'" class="w-1.5 h-1.5 rounded-full bg-warning"></span>
        <span v-else class="w-1.5 h-1.5 rounded-full bg-rule"></span>
      </span>
      <span>{{ item.label }}</span>
    </button>
  </div>
</template>
