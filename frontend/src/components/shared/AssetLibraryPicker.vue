<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { t } from '@/i18n'
import { getAssets, createAsset, deleteAsset } from '@/api'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import type { WorkspaceAsset } from '@/types'

const props = defineProps<{
  selectedId?: string
}>()

const emit = defineEmits<{
  (e: 'select', asset: WorkspaceAsset | null): void
}>()

const { showToast } = useToast()
const { confirmAsync } = useConfirm()

const assets = ref<WorkspaceAsset[]>([])
const loading = ref(false)
const openCreate = ref(false)
const saving = ref(false)

const newName = ref('')
const newKind = ref<'character' | 'style' | 'prop'>('character')
const newPrompt = ref('')
const newLocks = ref('')
const newFile = ref<File | null>(null)

async function load() {
  loading.value = true
  try {
    const res = await getAssets()
    if (res?.ok && Array.isArray(res.assets)) {
      assets.value = res.assets
    }
  } catch {
    /* ignore */
  } finally {
    loading.value = false
  }
}

onMounted(load)

function toggleSelect(asset: WorkspaceAsset) {
  if (props.selectedId === asset.id) {
    emit('select', null)
  } else {
    emit('select', asset)
  }
}

function onFileChange(e: Event) {
  newFile.value = (e.target as HTMLInputElement).files?.[0] || null
}

async function saveNewAsset() {
  if (!newName.value.trim()) {
    showToast(t('assetNameRequired'), 2500, 'error')
    return
  }
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('name', newName.value.trim())
    fd.append('kind', newKind.value)
    fd.append('prompt', newPrompt.value.trim())
    fd.append('continuity_locks', newLocks.value.trim())
    if (newFile.value) fd.append('image', newFile.value)
    const res = await createAsset(fd)
    if (res?.ok && res.asset) {
      assets.value.unshift(res.asset)
      emit('select', res.asset)
      newName.value = ''
      newPrompt.value = ''
      newLocks.value = ''
      newFile.value = null
      openCreate.value = false
      showToast(t('assetSaved'), 2500, 'success')
    }
  } catch (e: any) {
    showToast(e?.message || t('failCreate'), 3500, 'error')
  } finally {
    saving.value = false
  }
}

async function removeAssetItem(id: string) {
  if (!(await confirmAsync(t('assetDeleteConfirm')))) return
  try {
    await deleteAsset(id)
    assets.value = assets.value.filter((a) => a.id !== id)
    if (props.selectedId === id) emit('select', null)
    showToast(t('assetDeleted'), 2000, 'success')
  } catch (e: any) {
    showToast(e?.message || t('failDelete'), 3000, 'error')
  }
}
</script>

<template>
  <div class="rounded-xl border border-rule bg-paper-2/50 p-3.5 space-y-3">
    <div class="flex items-center justify-between gap-2">
      <div>
        <h4 class="text-xs font-semibold text-ink">{{ t('assetLibTitle') }}</h4>
        <p class="text-[11px] text-muted">{{ t('assetLibHint') }}</p>
      </div>
      <button
        type="button"
        class="px-2.5 py-1 rounded-lg text-xs font-medium bg-paper-3 border border-rule text-ink-2 hover:text-ink hover:border-accent/50 transition"
        @click="openCreate = !openCreate"
      >
        {{ openCreate ? t('cancel') : t('assetAddBtn') }}
      </button>
    </div>

    <!-- Create Asset Form -->
    <div v-if="openCreate" class="rounded-lg border border-rule bg-paper p-3 space-y-2.5">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <input
          v-model="newName"
          class="sm:col-span-2 glass-input rounded-lg px-3 py-1.5 text-xs text-ink placeholder-muted"
          :placeholder="t('assetNamePlaceholder')"
        />
        <select v-model="newKind" class="glass-input rounded-lg px-2.5 py-1.5 text-xs text-ink">
          <option value="character">{{ t('assetKindChar') }}</option>
          <option value="style">{{ t('assetKindStyle') }}</option>
          <option value="prop">{{ t('assetKindProp') }}</option>
        </select>
      </div>
      <input
        v-model="newPrompt"
        class="w-full glass-input rounded-lg px-3 py-1.5 text-xs text-ink placeholder-muted"
        :placeholder="t('assetPromptPlaceholder')"
      />
      <input
        v-model="newLocks"
        class="w-full glass-input rounded-lg px-3 py-1.5 text-xs text-ink placeholder-muted"
        :placeholder="t('assetLocksPlaceholder')"
      />
      <div class="flex flex-wrap items-center justify-between gap-2">
        <input
          type="file"
          accept="image/*"
          class="text-xs text-muted file:mr-2 file:py-1 file:px-2.5 file:rounded-lg file:border file:border-rule file:text-xs file:bg-paper-2 file:text-ink-2"
          @change="onFileChange"
        />
        <button
          type="button"
          class="px-3.5 py-1.5 rounded-lg text-xs font-semibold glow-btn disabled:opacity-50"
          :disabled="saving"
          @click="saveNewAsset"
        >
          {{ saving ? t('submitting') : t('save') }}
        </button>
      </div>
    </div>

    <!-- Asset Chips -->
    <div v-if="loading" class="text-xs text-muted">{{ t('loading') }}</div>
    <div v-else-if="!assets.length" class="text-xs text-muted">{{ t('assetLibEmpty') }}</div>
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-2">
      <div
        v-for="asset in assets"
        :key="asset.id"
        class="flex items-center gap-2.5 p-2 rounded-lg border transition"
        :class="
          selectedId === asset.id
            ? 'border-accent bg-accent/10'
            : 'border-rule bg-paper hover:border-accent/40'
        "
      >
        <button
          type="button"
          class="flex items-center gap-2.5 flex-1 min-w-0 text-left"
          @click="toggleSelect(asset)"
        >
          <img
            v-if="asset.image_url"
            :src="asset.image_url"
            :alt="asset.name"
            class="w-10 h-10 rounded-md object-cover border border-rule shrink-0"
          />
          <div
            v-else
            class="w-10 h-10 rounded-md bg-paper-3 border border-rule flex items-center justify-center text-xs text-muted shrink-0"
          >
            {{ asset.name.slice(0, 2).toUpperCase() }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-1.5">
              <span class="text-xs font-semibold text-ink truncate">{{ asset.name }}</span>
              <span class="badge-neutral text-[10px] px-1.5 py-0">{{ asset.kind }}</span>
            </div>
            <p v-if="asset.prompt || asset.continuity_locks" class="text-[11px] text-muted truncate">
              {{ asset.continuity_locks || asset.prompt }}
            </p>
          </div>
        </button>
        <button
          type="button"
          class="p-1 text-muted hover:text-danger transition shrink-0"
          :aria-label="t('delete')"
          :title="t('delete')"
          @click="removeAssetItem(asset.id)"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
