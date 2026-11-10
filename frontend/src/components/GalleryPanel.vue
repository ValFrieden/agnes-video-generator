<script setup lang="ts">
// 产物画廊（P1）：纯只读网格 + 类型/状态筛选；点卡片跳任务详情
import { t } from '@/i18n'
import { useGallery } from '@/composables/useGallery'
import { useNavigation } from '@/composables/useNavigation'
import { statusTextCls, statusLabelKey } from '@/utils/status'
import StoryboardExtractorCard from './StoryboardExtractorCard.vue'

const { items, loading, loadError, filter, status, loadGallery, applyFilter, applyStatus } = useGallery()
const { goProgress } = useNavigation()

function openItem(id: string) {
  goProgress(id, 'gallery')
}

function playPreview(e: Event) {
  ;(e.target as HTMLVideoElement).play().catch(() => {})
}
function pausePreview(e: Event) {
  const v = e.target as HTMLVideoElement
  v.pause()
  v.currentTime = 0
}
</script>

<template>
  <div>
    <!-- Filter Bar -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <span class="text-xs text-muted">{{ t('galleryReadonlyHint') }}</span>
      <span class="flex-1"></span>
      <select
        class="neu-sunken rounded-xl px-3.5 py-2 text-sm text-ink cursor-pointer border border-rule/30 focus:border-accent/40 outline-none"
        :value="filter"
        :aria-label="t('filterAll')"
        @change="applyFilter(($event.target as HTMLSelectElement).value as any)"
      >
        <option value="all">{{ t('filterAll') }}</option>
        <option value="video">{{ t('filterVideo') }}</option>
        <option value="image">{{ t('filterImage') }}</option>
      </select>
      <select
        class="neu-sunken rounded-xl px-3.5 py-2 text-sm text-ink cursor-pointer border border-rule/30 focus:border-accent/40 outline-none"
        :value="status"
        :aria-label="t('filterStatusAll')"
        @change="applyStatus(($event.target as HTMLSelectElement).value as any)"
      >
        <option value="all">{{ t('filterStatusAll') }}</option>
        <option value="completed">{{ t('filterStatusCompleted') }}</option>
        <option value="failed">{{ t('filterStatusFailed') }}</option>
      </select>
    </div>

    <!-- Loading Skeleton Grid -->
    <div
      v-if="loading && !items.length"
      class="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-4"
      role="status"
      aria-live="polite"
      :aria-label="t('loading')"
    >
      <div v-for="i in 6" :key="i" class="glass-card rounded-2xl overflow-hidden animate-pulse">
        <div class="aspect-video bg-paper-3"></div>
        <div class="p-3.5 space-y-2">
          <div class="h-4 bg-paper-3 rounded w-2/3"></div>
          <div class="h-3 bg-paper-3 rounded w-1/2"></div>
        </div>
      </div>
    </div>

    <!-- Load Error State -->
    <div
      v-if="loadError && !loading"
      class="flex flex-wrap items-center gap-3 mb-4 p-3 rounded-xl panel-danger"
      role="alert"
    >
      <span class="text-sm text-danger">{{ t('galleryLoadError') }}</span>
      <button class="btn-danger-soft px-3 py-1 text-xs" @click="loadGallery">
        {{ t('btnRetry') }}
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !loadError && !items.length" class="glass-card rounded-2xl p-8 text-center space-y-3">
      <div class="flex justify-center text-muted/40">
        <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <p class="text-muted text-sm">{{ t('galleryEmpty') }}</p>
      <a href="#/create" class="inline-block text-xs px-4 py-2 rounded-lg glow-btn">
        {{ t('tabCreate') }}
      </a>
    </div>

    <!-- Grid -->
    <div v-if="items.length" class="grid grid-cols-2 sm:grid-cols-3 gap-4">
      <article
        v-for="it in items"
        :key="it.task_id"
        class="neu-raised rounded-2xl overflow-hidden cursor-pointer group transition-all hover:translate-y-[-2px] border border-rule/20"
        role="button"
        tabindex="0"
        :aria-label="it.title"
        @click="openItem(it.task_id)"
        @keydown.enter.prevent="openItem(it.task_id)"
        @keydown.space.prevent="openItem(it.task_id)"
      >
        <div class="relative aspect-video bg-paper-2 overflow-hidden neu-sunken">
          <img
            v-if="it.kind === 'video' && it.thumb_url"
            :src="it.thumb_url"
            class="absolute inset-0 w-full h-full object-cover transition group-hover:opacity-0"
            loading="lazy"
            alt=""
          />
          <video
            v-if="it.kind === 'video'"
            :src="it.media_url"
            :poster="it.thumb_url || undefined"
            class="absolute inset-0 w-full h-full object-cover transition"
            :class="it.thumb_url ? 'opacity-0 group-hover:opacity-100' : ''"
            preload="none"
            muted
            playsinline
            loop
            @mouseenter="playPreview"
            @mouseleave="pausePreview"
          ></video>
          <img v-else-if="it.kind === 'image'" :src="it.media_url" class="absolute inset-0 w-full h-full object-cover" loading="lazy" alt="" />
          <span class="absolute top-2.5 left-2.5 px-2.5 py-0.5 rounded-full text-[10px] uppercase neu-sunken bg-paper/80 font-bold backdrop-blur-sm">
            {{ it.kind }}
          </span>
        </div>
        <div class="p-3.5">
          <div class="flex items-center justify-between gap-2 mb-1">
            <span class="text-sm font-semibold text-ink truncate">{{ it.title }}</span>
            <span class="text-xs px-2 py-0.5 rounded-full neu-sunken font-medium" :class="statusTextCls(it.status)">
              {{ t(statusLabelKey(it.status)) }}
            </span>
          </div>
          <p v-if="it.description" class="text-xs text-muted line-clamp-2 leading-relaxed">{{ it.description }}</p>
        </div>
      </article>
    </div>

    <!-- FFmpeg Scene Storyboard Extractor -->
    <StoryboardExtractorCard :videos="items" />
  </div>
</template>
