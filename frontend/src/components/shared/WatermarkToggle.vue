<script setup lang="ts">
import { computed } from 'vue'
import { t } from '@/i18n'
import { appState } from '@/store'
import { useConfig } from '@/composables/useConfig'
import NeuSwitch from './NeuSwitch.vue'

const { toggleWatermark } = useConfig()

const isEnabled = computed({
  get: () => appState.watermarkEnabled,
  set: (val: boolean) => toggleWatermark(val),
})
</script>

<template>
  <div class="flex items-center justify-between px-2 py-3 mb-4 rounded-xl border border-rule/40 bg-paper-2/30">
    <div class="mr-4">
      <span class="text-xs font-medium text-ink-2">{{ t('watermarkTitle') }}</span>
      <p class="text-[11px] text-muted leading-relaxed mt-0.5">{{ t('watermarkPromo') }}</p>
    </div>
    <NeuSwitch v-model="isEnabled" />
  </div>
</template>
