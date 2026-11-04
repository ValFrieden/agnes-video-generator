<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: number
    min?: number
    max?: number
    step?: number
    unit?: string
  }>(),
  {
    min: 1,
    max: 100,
    step: 1,
    unit: '',
  },
)

const emit = defineEmits<{
  (e: 'update:modelValue', val: number): void
}>()

function dec() {
  const next = Math.max(props.min, (props.modelValue || props.min) - props.step)
  emit('update:modelValue', next)
}

function inc() {
  const next = Math.min(props.max, (props.modelValue || props.min) + props.step)
  emit('update:modelValue', next)
}

function onInput(e: Event) {
  const val = Number((e.target as HTMLInputElement).value)
  if (!isNaN(val)) {
    emit('update:modelValue', Math.max(props.min, Math.min(props.max, val)))
  }
}
</script>

<template>
  <div class="inline-flex items-center gap-1.5 p-1 rounded-2xl neu-sunken border border-rule/40 select-none">
    <!-- Decrement Button (-) -->
    <button
      type="button"
      class="w-8 h-8 rounded-xl neu-raised flex items-center justify-center text-sm font-bold text-ink-2 hover:text-ink transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
      :disabled="modelValue <= min"
      @click="dec"
    >
      −
    </button>

    <!-- Value Display / Manual Input -->
    <div class="flex items-center justify-center px-2 min-w-[3.5rem] text-center">
      <input
        type="number"
        :value="modelValue"
        :min="min"
        :max="max"
        class="w-12 bg-transparent text-center text-sm font-semibold text-ink focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
        @change="onInput"
      />
      <span v-if="unit" class="text-xs text-muted ml-0.5">{{ unit }}</span>
    </div>

    <!-- Increment Button (+) -->
    <button
      type="button"
      class="w-8 h-8 rounded-xl neu-raised flex items-center justify-center text-sm font-bold text-ink-2 hover:text-ink transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
      :disabled="modelValue >= max"
      @click="inc"
    >
      +
    </button>
  </div>
</template>
