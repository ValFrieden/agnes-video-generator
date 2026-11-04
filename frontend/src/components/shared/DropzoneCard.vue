<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { t } from '@/i18n'

const props = withDefaults(
  defineProps<{
    modelValue: File | null
    title?: string
    hint?: string
    badge?: string
    accept?: string
  }>(),
  {
    title: '',
    hint: '',
    badge: '',
    accept: 'image/*',
  },
)

const emit = defineEmits<{
  (e: 'update:modelValue', file: File | null): void
  (e: 'change', file: File | null): void
}>()

const previewUrl = ref<string>('')
const isDragging = ref(false)
const fileInput = ref<HTMLInputElement>()

watch(
  () => props.modelValue,
  (file) => {
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
      previewUrl.value = ''
    }
    if (file) {
      previewUrl.value = URL.createObjectURL(file)
    }
  },
  { immediate: true },
)

onUnmounted(() => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
})

function onFileSelected(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files && files.length > 0) {
    setFile(files[0])
  }
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    setFile(files[0])
  }
}

function setFile(file: File) {
  emit('update:modelValue', file)
  emit('change', file)
}

function removeFile() {
  if (fileInput.value) fileInput.value.value = ''
  emit('update:modelValue', null)
  emit('change', null)
}

function triggerBrowse() {
  fileInput.value?.click()
}
</script>

<template>
  <div class="relative">
    <input
      ref="fileInput"
      type="file"
      :accept="accept"
      class="hidden"
      @change="onFileSelected"
    />

    <!-- Has File: Preview Card -->
    <div
      v-if="previewUrl"
      class="relative group rounded-2xl neu-raised border border-rule/50 overflow-hidden p-3.5 flex items-center gap-4 transition"
    >
      <!-- Thumbnail -->
      <div class="relative w-20 h-20 rounded-xl overflow-hidden shrink-0 bg-black/40 border border-rule/60 shadow-inner">
        <img :src="previewUrl" alt="Preview" class="w-full h-full object-cover" />
      </div>

      <!-- File Details -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span v-if="badge" class="px-2.5 py-0.5 rounded-full text-[10px] font-medium bg-accent/20 text-accent border border-accent/30 shadow-sm">
            {{ badge }}
          </span>
          <span class="text-xs font-semibold text-ink truncate">
            {{ modelValue?.name }}
          </span>
        </div>
        <p class="text-[11px] text-muted truncate">
          {{ ((modelValue?.size || 0) / 1024).toFixed(1) }} KB
        </p>

        <!-- Actions -->
        <div class="flex items-center gap-3 mt-2">
          <button
            type="button"
            class="text-xs text-accent hover:underline flex items-center gap-1.5 transition cursor-pointer font-medium"
            @click="triggerBrowse"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
            <span>{{ t('chooseImage') }}</span>
          </button>
          <button
            type="button"
            class="text-xs text-danger hover:opacity-80 flex items-center gap-1.5 transition cursor-pointer font-medium"
            @click="removeFile"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            <span>{{ t('clear') }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Empty: Drag & Drop Area -->
    <div
      v-else
      class="bg-paper-2/40 border border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200"
      :class="
        isDragging
          ? 'border-accent ring-1 ring-accent/30'
          : 'border-rule hover:border-accent/60'
      "
      @click="triggerBrowse"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
    >
      <div class="w-10 h-10 mx-auto mb-2 text-muted/60 flex items-center justify-center">
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
      </div>
      <p class="text-xs font-semibold text-ink mb-0.5">
        {{ title || t('chooseImage') }}
      </p>
      <p class="text-[11px] text-muted">
        {{ hint || t('dropzoneHint') || 'Drag & drop image here or click to browse' }}
      </p>
    </div>
  </div>
</template>
