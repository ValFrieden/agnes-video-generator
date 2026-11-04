<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
}>()

interface QuickStyle {
  label: string
  prompt: string
}

const quickStyles: QuickStyle[] = [
  {
    label: 'Cinematic 35mm',
    prompt: 'Cinematic 35mm film, dramatic natural lighting, hyperrealistic, high detailed, shallow depth of field, 8k',
  },
  {
    label: 'Makoto Shinkai',
    prompt: 'Makoto Shinkai anime aesthetic, beautiful volumetric sky, vibrant colors, detailed emotional atmosphere, studio ghibli lighting',
  },
  {
    label: '3D Animation',
    prompt: 'Cute 3D animation style, Pixar and Disney render, subsurface scattering, soft studio lighting, ultra detailed',
  },
  {
    label: 'Cyberpunk',
    prompt: 'Cyberpunk dystopian city, glowing neon lights, rain reflections, volumetric fog, cinematic mood, 8k',
  },
  {
    label: 'Oil Painting',
    prompt: 'Impressionist classic oil painting, rich textured canvas brush strokes, artistic lighting, fine art masterpiece',
  },
  {
    label: 'Dark Fantasy',
    prompt: 'Dark fantasy gothic aesthetic, atmospheric moody fog, epic cinematic composition, intricate details',
  },
]

function selectStyle(prompt: string) {
  emit('update:modelValue', prompt)
}

function isSelected(prompt: string): boolean {
  return props.modelValue === prompt
}
</script>

<template>
  <div class="flex items-center gap-2 overflow-x-auto pb-1.5 scrollbar-thin">
    <button
      v-for="s in quickStyles"
      :key="s.label"
      type="button"
      class="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium border shrink-0 transition-colors cursor-pointer"
      :class="
        isSelected(s.prompt)
          ? 'bg-accent text-accent-ink border-accent'
          : 'bg-paper-2 border-rule/70 text-ink-2 hover:bg-paper-3 hover:text-ink hover:border-rule'
      "
      @click="selectStyle(s.prompt)"
    >
      <span>{{ s.label }}</span>
    </button>
  </div>
</template>
