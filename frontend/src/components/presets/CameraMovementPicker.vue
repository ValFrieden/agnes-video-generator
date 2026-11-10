<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { t, currentLang } from '@/i18n'
import { getCameraMovements } from '@/api'
import type { CameraMovementPreset } from '@/types'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const open = ref(false)
const loading = ref(false)
const presets = ref<CameraMovementPreset[]>([])
const selectedCategory = ref<string>('all')
const searchQuery = ref<string>('')

onMounted(async () => {
  try {
    loading.value = true
    const res = await getCameraMovements()
    if (res?.presets) {
      presets.value = res.presets
    }
  } catch (err) {
    console.error('Failed to load camera movements', err)
  } finally {
    loading.value = false
  }
})

const selectedPreset = computed(() => {
  return presets.value.find((p) => p.id === props.modelValue)
})

const categories = computed(() => [
  { id: 'all', name: t('camCatAll') },
  { id: 'dramatic', name: t('camCatDramatic') },
  { id: 'dynamic', name: t('camCatDynamic') },
  { id: 'perspective', name: t('camCatPerspective') },
  { id: 'atmospheric', name: t('camCatAtmospheric') },
])

const filteredPresets = computed(() => {
  let list = presets.value
  if (selectedCategory.value !== 'all') {
    list = list.filter((p) => p.category === selectedCategory.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter(
      (p) =>
        p.name_ru.toLowerCase().includes(q) ||
        p.name_en.toLowerCase().includes(q) ||
        p.description_ru.toLowerCase().includes(q) ||
        p.description_en.toLowerCase().includes(q) ||
        p.prompt_modifier.toLowerCase().includes(q),
    )
  }
  return list
})

function presetName(p: CameraMovementPreset): string {
  return currentLang.value === 'ru' ? p.name_ru : p.name_en
}

function presetDesc(p: CameraMovementPreset): string {
  return currentLang.value === 'ru' ? p.description_ru : p.description_en
}

function selectMovement(id: string) {
  if (props.modelValue === id) {
    emit('update:modelValue', '')
  } else {
    emit('update:modelValue', id)
    open.value = false
  }
}

function clearSelection() {
  emit('update:modelValue', '')
}
</script>

<template>
  <div class="relative w-full">
    <div class="flex flex-wrap items-center gap-2">
      <div
        v-if="selectedPreset"
        class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-accent/15 border border-accent/40 text-accent text-xs"
      >
        <span class="font-medium">{{ presetName(selectedPreset) }}</span>
        <button
          type="button"
          class="text-accent hover:text-ink transition-colors p-0.5"
          :aria-label="t('clear')"
          :title="t('clear')"
          @click.stop="clearSelection"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <button
        type="button"
        class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition cursor-pointer"
        :class="
          selectedPreset
            ? 'bg-paper-2 border-rule text-ink-2 hover:text-ink hover:border-accent/40'
            : 'bg-paper-2 border-rule text-ink-2 hover:text-ink hover:border-accent/50'
        "
        :aria-expanded="open"
        @click="open = !open"
      >
        <svg class="w-3.5 h-3.5 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M4 6h8a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2z" />
        </svg>
        <span>{{ selectedPreset ? t('camChange') : t('camPick') }}</span>
        <span class="text-[10px] text-muted">{{ open ? '▲' : '▼' }}</span>
      </button>
    </div>

    <div
      v-if="open"
      class="mt-2 p-3.5 rounded-xl bg-paper-2 border border-rule shadow-lg z-30 flex flex-col gap-3 max-h-[380px] overflow-y-auto"
    >
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-rule pb-2">
        <div class="text-xs font-semibold text-ink">
          {{ t('camCatalogTitle') }}
        </div>
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="t('camSearchPlaceholder')"
          :aria-label="t('camSearchPlaceholder')"
          class="px-2.5 py-1.5 text-xs rounded-lg glass-input text-ink placeholder-muted w-full sm:w-48"
        />
      </div>

      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="cat in categories"
          :key="cat.id"
          type="button"
          class="px-2.5 py-1 rounded-lg text-[11px] font-medium border transition"
          :class="
            selectedCategory === cat.id
              ? 'bg-accent text-accent-ink border-accent'
              : 'bg-paper border-rule text-muted hover:text-ink-2'
          "
          @click="selectedCategory = cat.id"
        >
          {{ cat.name }}
        </button>
      </div>

      <div v-if="loading" class="text-xs text-muted py-4 text-center">{{ t('loading') }}</div>
      <div v-else-if="!filteredPresets.length" class="text-xs text-muted py-4 text-center">{{ t('voiceEmpty') }}</div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <button
          v-for="p in filteredPresets"
          :key="p.id"
          type="button"
          class="p-2.5 rounded-lg border text-left transition flex flex-col justify-between"
          :class="
            modelValue === p.id
              ? 'bg-accent/10 border-accent text-ink'
              : 'bg-paper border-rule hover:border-accent/40 text-ink-2'
          "
          @click="selectMovement(p.id)"
        >
          <div>
            <div class="flex items-center justify-between gap-1">
              <span class="text-xs font-semibold text-ink">{{ presetName(p) }}</span>
              <span class="badge-neutral text-[10px] px-1.5 py-0">{{ p.category }}</span>
            </div>
            <p class="text-[11px] text-muted mt-1 line-clamp-2 leading-snug">{{ presetDesc(p) }}</p>
          </div>
          <div class="mt-2 pt-1 border-t border-rule/60 text-[10px] text-accent font-mono truncate w-full">
            {{ p.prompt_modifier }}
          </div>
        </button>
      </div>
    </div>
  </div>
</template>
