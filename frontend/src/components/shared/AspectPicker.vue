<script setup lang="ts">
import { computed } from 'vue'
import { t } from '@/i18n'

interface Option {
  value: string
  label?: string
  sublabel?: string
  ratio?: '9:16' | '16:9' | '1:1' | '4:3' | '3:4' | string
}

const props = withDefaults(
  defineProps<{
    modelValue: string
    options?: Option[]
  }>(),
  {
    options: () => [
      { value: '768x1152', ratio: '9:16', label: 'resPortrait', sublabel: 'Shorts · Reels · TikTok' },
      { value: '1280x720', ratio: '16:9', label: 'resLandscape', sublabel: 'YouTube · Cinema' },
      { value: '1024x1024', ratio: '1:1', label: 'resSquare', sublabel: 'Instagram · Post' },
    ],
  },
)

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
}>()

function select(val: string) {
  emit('update:modelValue', val)
}

function getRatioClass(ratio?: string): string {
  if (ratio === '9:16' || ratio?.includes('9:16')) return 'w-4 h-7'
  if (ratio === '16:9' || ratio?.includes('16:9')) return 'w-7 h-4'
  if (ratio === '4:3' || ratio?.includes('4:3')) return 'w-6 h-4.5'
  if (ratio === '3:4' || ratio?.includes('3:4')) return 'w-4.5 h-6'
  return 'w-5 h-5' // 1:1
}
</script>

<template>
  <div class="grid grid-cols-3 gap-2 sm:gap-3">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      class="group relative flex flex-col items-center justify-center p-3 rounded-2xl text-center transition-all duration-200 cursor-pointer"
      :class="
        modelValue === opt.value
          ? 'neu-sunken border border-accent/40 text-accent ring-1 ring-accent/30'
          : 'neu-raised border border-rule/30 text-ink-2 hover:border-rule'
      "
      @click="select(opt.value)"
    >
      <!-- Silhouette Box -->
      <div class="h-8 flex items-center justify-center mb-1.5">
        <div
          class="rounded-sm border-2 transition-all shadow-sm"
          :class="[
            getRatioClass(opt.ratio || opt.value),
            modelValue === opt.value
              ? 'border-accent bg-accent/20'
              : 'border-muted/50 bg-paper-3/40 group-hover:border-muted',
          ]"
        ></div>
      </div>

      <!-- Title / Label -->
      <span class="text-xs font-semibold tracking-wide" :class="modelValue === opt.value ? 'text-accent' : 'text-ink'">
        {{ opt.ratio || (opt.label ? t(opt.label) : opt.value) }}
      </span>

      <!-- Subtitle -->
      <span class="text-[10px] text-muted truncate max-w-full mt-0.5">
        {{ opt.sublabel || (opt.label ? t(opt.label) : opt.value) }}
      </span>

      <!-- Active Check Badge -->
      <div
        v-if="modelValue === opt.value"
        class="absolute top-2 right-2 w-2 h-2 rounded-full bg-accent shadow-sm"
      ></div>
    </button>
  </div>
</template>
