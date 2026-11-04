<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: boolean
    label?: string
    hint?: string
    disabled?: boolean
  }>(),
  {
    label: '',
    hint: '',
    disabled: false,
  },
)

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
}>()

function toggle() {
  if (props.disabled) return
  emit('update:modelValue', !props.modelValue)
}
</script>

<template>
  <div
    class="inline-flex items-center justify-between gap-3 cursor-pointer select-none"
    :class="{ 'opacity-50 cursor-not-allowed': disabled }"
    @click="toggle"
  >
    <div v-if="label || hint">
      <div v-if="label" class="text-sm font-medium text-ink-2">{{ label }}</div>
      <div v-if="hint" class="text-xs text-muted">{{ hint }}</div>
    </div>

    <!-- Tactile Capsule Switch -->
    <div
      class="relative w-12 h-6 rounded-full neu-sunken border border-rule/40 p-0.5 transition-colors shrink-0"
      :class="modelValue ? 'bg-accent/15 border-accent/40' : 'bg-paper-3/40'"
    >
      <div
        class="w-5 h-5 rounded-full neu-raised flex items-center justify-center transition-transform duration-200"
        :class="modelValue ? 'translate-x-6 bg-accent text-accent-ink shadow-sm' : 'translate-x-0 text-muted'"
      >
        <span class="w-1.5 h-1.5 rounded-full" :class="modelValue ? 'bg-accent-ink' : 'bg-muted/60'"></span>
      </div>
    </div>
  </div>
</template>
