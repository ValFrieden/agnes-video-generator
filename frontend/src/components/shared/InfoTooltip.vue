<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  text: string
  title?: string
}>()

const isHovered = ref(false)
</script>

<template>
  <span
    class="relative inline-flex items-center ml-1 group"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  >
    <button
      type="button"
      class="w-5 h-5 rounded-full flex items-center justify-center text-[11px] text-muted hover:text-ink hover:bg-paper-3 transition border border-rule/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent cursor-pointer"
      :aria-label="title || text"
      :aria-expanded="isHovered"
      @focus="isHovered = true"
      @blur="isHovered = false"
      @click.stop="isHovered = !isHovered"
    >
      ?
    </button>

    <!-- Tooltip Card -->
    <transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-100 ease-out"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isHovered"
        class="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 z-50 w-64 p-3 rounded-xl bg-paper border border-rule shadow-2xl text-xs text-ink-2 leading-relaxed pointer-events-none"
      >
        <div v-if="title" class="font-semibold text-ink mb-1 flex items-center gap-1.5">
          <svg class="w-3.5 h-3.5 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <span>{{ title }}</span>
        </div>
        <p class="whitespace-pre-line text-muted">{{ text }}</p>
        <div class="absolute left-1/2 -translate-x-1/2 top-full w-2 h-2 bg-paper border-r border-b border-rule rotate-45 -mt-1"></div>
      </div>
    </transition>
  </span>
</template>
