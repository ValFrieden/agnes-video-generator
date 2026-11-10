<script setup lang="ts">
import { ref } from 'vue'
import { t } from '@/i18n'
import { useGa } from '@/composables/useGa'

const props = defineProps<{ collapsed: boolean }>()
const emit = defineEmits<{ (e: 'toggle'): void }>()

const { isGaOptedOut, setGaOptOut } = useGa()
const gaOptOut = ref(isGaOptedOut())
function toggleGaOptOut() {
  setGaOptOut(gaOptOut.value)
}
</script>

<template>
  <!-- 隐私设置（3.4：GA4 配置开关） -->
  <div class="glass-card rounded-2xl mb-6 overflow-hidden transition-all duration-300">
    <button
      v-if="props.collapsed"
      type="button"
      class="w-full flex items-center justify-between px-6 py-3 cursor-pointer hover:bg-paper-3 transition text-left"
      :aria-expanded="!props.collapsed"
      @click="emit('toggle')"
    >
      <div class="flex items-center gap-3">
        <svg class="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
        <span class="text-sm text-muted">
          <span class="text-ink-2 font-medium">{{ t('privacyTitle') }}</span>
          <span class="text-muted mx-2">·</span>
          <span :class="gaOptOut ? 'text-success' : 'text-muted'">
            {{ gaOptOut ? t('gaStatOff') : t('gaStatOn') }}
          </span>
        </span>
      </div>
      <svg class="w-4 h-4 text-muted shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
    </button>
    <div v-else class="p-6 pt-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-lg font-semibold text-accent">{{ t('privacyTitle') }}</h2>
        <div class="flex items-center gap-2">
          <span :class="gaOptOut ? 'badge-success' : 'text-xs px-2 py-1 rounded-full bg-paper-2 text-muted'">
            {{ gaOptOut ? t('gaStatOff') : t('gaStatOn') }}
          </span>
          <button
            class="text-xs text-muted hover:text-ink-2 transition px-2 py-1 rounded cursor-pointer"
            :aria-label="t('collapse')"
            :aria-expanded="!props.collapsed"
            @click="emit('toggle')"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
          </button>
        </div>
      </div>
      <label class="flex items-start gap-3 cursor-pointer select-none">
        <input v-model="gaOptOut" type="checkbox" class="mt-1 accent-red-500" @change="toggleGaOptOut" />
        <span>
          <span class="text-sm text-ink font-medium block">{{ t('gaOptOutLabel') }}</span>
          <span class="text-xs text-muted block mt-0.5">{{ t('gaOptOutHint') }}</span>
        </span>
      </label>

      <!-- 上报信息透明化说明（3.4：采集范围 + 隐私承诺） -->
      <div class="mt-4 rounded-lg bg-paper-3/60 p-4 text-xs leading-relaxed">
        <p class="font-medium text-ink-2 mb-2">{{ t('gaReportTitle') }}</p>
        <ul class="list-disc pl-4 space-y-1 text-muted">
          <li>{{ t('gaReportItem1') }}</li>
          <li>{{ t('gaReportItem2') }}</li>
          <li>{{ t('gaReportItem3') }}</li>
          <li>{{ t('gaReportItem4') }}</li>
        </ul>
        <p class="mt-3 pt-3 border-t border-rule/40 font-medium text-ink-2">{{ t('gaNeverUploadTitle') }}</p>
        <p class="text-muted">{{ t('gaNeverUploadText') }}</p>
      </div>
    </div>
  </div>
</template>