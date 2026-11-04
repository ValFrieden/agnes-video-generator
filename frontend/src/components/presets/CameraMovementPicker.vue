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

const categories = computed(() => {
  const isRu = currentLang.value === 'ru'
  return [
    { id: 'all', name: isRu ? 'Все (20)' : 'All (20)' },
    { id: 'dramatic', name: isRu ? 'Драматические' : 'Dramatic' },
    { id: 'dynamic', name: isRu ? 'Динамические' : 'Dynamic' },
    { id: 'perspective', name: isRu ? 'Ракурсные' : 'Perspective' },
    { id: 'atmospheric', name: isRu ? 'Атмосферные' : 'Atmospheric' },
  ]
})

const filteredPresets = computed(() => {
  let list = presets.value
  if (selectedCategory.value !== 'all') {
    list = list.filter((p) => p.category === selectedCategory.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter((p) =>
      p.name_ru.toLowerCase().includes(q) ||
      p.name_en.toLowerCase().includes(q) ||
      p.description_ru.toLowerCase().includes(q) ||
      p.prompt_modifier.toLowerCase().includes(q)
    )
  }
  return list
})

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
    <!-- Active Selection Chip or Trigger Button -->
    <div class="flex items-center gap-2">
      <div v-if="selectedPreset" class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-500/15 border border-indigo-500/30 text-indigo-200 text-xs">
        <span class="font-medium">🎬 {{ currentLang === 'ru' ? selectedPreset.name_ru : selectedPreset.name_en }}</span>
        <button
          type="button"
          class="text-indigo-400 hover:text-white transition-colors"
          title="Сбросить"
          @click.stop="clearSelection"
        >
          ✕
        </button>
      </div>

      <button
        type="button"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
        :class="selectedPreset ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300' : 'bg-gradient-to-r from-purple-500/20 to-indigo-500/20 hover:from-purple-500/30 hover:to-indigo-500/30 border border-purple-500/30 text-purple-200'"
        @click="open = !open"
      >
        <span>🎥</span>
        <span>{{ selectedPreset ? (currentLang === 'ru' ? 'Сменить движение камеры' : 'Change camera') : (currentLang === 'ru' ? '20 движений камеры (SYNTX)' : '20 Camera Movements (SYNTX)') }}</span>
        <span class="text-[10px] text-zinc-400">{{ open ? '▲' : '▼' }}</span>
      </button>
    </div>

    <!-- Dropdown Modal / Picker Grid -->
    <div
      v-if="open"
      class="mt-2 p-3 rounded-xl bg-zinc-900/95 border border-zinc-700/80 shadow-2xl backdrop-blur-md z-30 flex flex-col gap-3 max-h-[380px] overflow-y-auto"
    >
      <!-- Header & Search -->
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-zinc-800 pb-2">
        <div class="flex items-center gap-1.5 text-xs font-medium text-zinc-300">
          <span>🎬</span>
          <span>{{ currentLang === 'ru' ? 'Кинематографический операторский каталог' : 'Cinematic Camera Presets' }}</span>
        </div>
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="currentLang === 'ru' ? 'Поиск пресета...' : 'Search movement...'"
          class="px-2.5 py-1 text-xs rounded-md bg-zinc-800 border border-zinc-700 text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-indigo-500 w-full sm:w-48"
        />
      </div>

      <!-- Category Filter Tabs -->
      <div class="flex flex-wrap gap-1">
        <button
          v-for="cat in categories"
          :key="cat.id"
          type="button"
          class="px-2 py-0.5 rounded text-[11px] font-medium transition-all"
          :class="selectedCategory === cat.id ? 'bg-indigo-600 text-white shadow-sm' : 'bg-zinc-800/80 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700'"
          @click="selectedCategory = cat.id"
        >
          {{ cat.name }}
        </button>
      </div>

      <!-- Presets Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <div
          v-for="p in filteredPresets"
          :key="p.id"
          class="p-2.5 rounded-lg border text-left cursor-pointer transition-all flex flex-col justify-between"
          :class="modelValue === p.id ? 'bg-indigo-600/20 border-indigo-500 text-indigo-100 shadow' : 'bg-zinc-800/50 hover:bg-zinc-800 border-zinc-700/50 hover:border-zinc-600 text-zinc-300'"
          @click="selectMovement(p.id)"
        >
          <div>
            <div class="flex items-center justify-between gap-1">
              <span class="text-xs font-semibold text-zinc-200">
                {{ currentLang === 'ru' ? p.name_ru : p.name_en }}
              </span>
              <span class="text-[10px] px-1.5 py-0.2 rounded bg-zinc-700/60 text-zinc-400">
                {{ p.category }}
              </span>
            </div>
            <p class="text-[11px] text-zinc-400 mt-1 line-clamp-2 leading-snug">
              {{ currentLang === 'ru' ? p.description_ru : p.description_en }}
            </p>
          </div>

          <div class="mt-2 pt-1 border-t border-zinc-700/40 text-[10px] text-indigo-300/80 font-mono italic truncate">
            {{ p.prompt_modifier }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
