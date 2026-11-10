<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { t } from '@/i18n'
import { getLuts } from '@/api'
import type { LutPreset } from '@/types'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: string): void }>()

const luts = ref<LutPreset[]>([])
const loading = ref(false)

const selectedLut = computed(() => luts.value.find((l) => l.id === props.modelValue))

onMounted(async () => {
  loading.value = true
  try {
    const res = await getLuts()
    if (res?.ok && Array.isArray(res.luts)) {
      luts.value = res.luts
    }
  } catch {
    /* fail-open: LUTs remain optional */
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <label class="block text-sm text-muted font-medium mb-1.5" :for="'lut-select-' + $.uid">{{ t('lutLabel') }}</label>
    <select
      :id="'lut-select-' + $.uid"
      :value="modelValue"
      class="w-full glass-input rounded-lg px-3 py-2.5 text-sm text-ink"
      :disabled="loading"
      @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option value="">{{ t('lutNone') }}</option>
      <option v-for="l in luts" :key="l.id" :value="l.id">{{ l.name }}</option>
    </select>
    <p v-if="selectedLut?.description" class="text-xs text-muted mt-1 leading-relaxed">
      {{ selectedLut.description }}
    </p>
  </div>
</template>
