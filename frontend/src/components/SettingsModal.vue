<script setup lang="ts">
import { computed } from 'vue'
import { t } from '@/i18n'
import { appState } from '@/store'
import { useModalA11y } from '@/composables/useModalA11y'
import ConfigPanel from './ConfigPanel.vue'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'close'): void
}>()

function close() {
  emit('update:visible', false)
  emit('close')
}

const { containerRef } = useModalA11y(
  computed(() => props.visible),
  close,
)

const isConfigured = computed(() => !!appState.apiKeySource)
</script>

<template>
  <teleport to="body">
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-out"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="visible"
        ref="containerRef"
        class="fixed inset-0 z-[70] flex items-center justify-center p-4 sm:p-6"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-modal-title"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="close"></div>

        <!-- Modal Box -->
        <div
          class="relative w-full max-w-4xl max-h-[90vh] flex flex-col bg-paper rounded-2xl border border-rule shadow-2xl overflow-hidden transition-all transform scale-100"
          @click.stop
        >
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-rule/60 bg-paper-2 shrink-0">
            <div class="flex items-center gap-3">
              <svg class="w-5 h-5 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
              <div>
                <h3 id="settings-modal-title" class="text-base font-semibold text-ink">
                  {{ t('advancedSettings') }} / {{ t('modelTitle') }}
                </h3>
                <p class="text-xs text-muted">
                  API Key · {{ t('modelTitle') }} · {{ t('providerSupplier') || 'Providers' }} · {{ t('workspaceTitle') || 'Workspace' }}
                </p>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <span
                class="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border"
                :class="
                  isConfigured
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                "
              >
                <span class="w-2 h-2 rounded-full" :class="isConfigured ? 'bg-emerald-500' : 'bg-amber-500'"></span>
                {{ isConfigured ? t('apiKeyConfigured') : t('apiKeyNotConfigured') }}
              </span>

              <button
                class="p-2 rounded-lg text-muted hover:text-ink hover:bg-paper-3 transition"
                :aria-label="t('cancel')"
                @click="close"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Body with ConfigPanel -->
          <div class="flex-1 overflow-y-auto p-6 space-y-4">
            <ConfigPanel />
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-end px-6 py-3 border-t border-rule/60 bg-paper-2 shrink-0">
            <button
              class="px-5 py-2 rounded-xl text-sm font-medium bg-accent text-accent-ink hover:bg-accent/90 transition shadow-sm"
              @click="close"
            >
              {{ t('save') }} / OK
            </button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>
