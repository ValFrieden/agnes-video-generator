<script setup lang="ts">
// 产物画廊（P1）：纯只读网格 + 类型/状态筛选；点卡片跳任务详情
// 不含任何删除 / 确认弹窗（删除管理保留在「任务列表」Tab）
import { t } from '@/i18n'
import { useGallery } from '@/composables/useGallery'
import { useNavigation } from '@/composables/useNavigation'
import { statusTextCls, statusLabelKey } from '@/utils/status'

const { items, loading, loadError, filter, status, loadGallery, applyFilter, applyStatus } = useGallery()
const { goProgress } = useNavigation()

function openItem(id: string, dir: string, type: string) {
  goProgress(id, 'gallery')
}

// P0 Befund：Galerie wird ausschließlich beim Aktivieren des Tabs geladen
// (App.vue switchMainTab / applyHashRoute / initialer Hash). Der frühere
// onMounted-Load hier feuerte beim App-Start, obwohl das Panel via v-show
// unsichtbar war — Ursprung der Boot-Zeit-Fehlerflut durch Medien-Requests.
// Deshalb bewusst KEIN eigenes Laden in diesem Panel.

// Logikcheck Befund 3：兑现注释承诺的「hover 播放」——muted + playsinline 下
// 浏览器允许编程播放；失败（如浏览器策略）静默忽略，点击卡片仍进详情页。
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
    <!-- 筛选栏 -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <span class="text-xs text-muted">{{ t('galleryReadonlyHint') }}</span>
      <span class="flex-1"></span>
      <select
        class="neu-sunken rounded-xl px-3.5 py-2 text-sm text-ink cursor-pointer border border-rule/30 focus:border-accent/40 outline-none"
        :value="filter"
        @change="applyFilter(($event.target as HTMLSelectElement).value as any)"
      >
        <option value="all">{{ t('filterAll') }}</option>
        <option value="video">{{ t('filterVideo') }}</option>
        <option value="image">{{ t('filterImage') }}</option>
      </select>
      <select
        class="neu-sunken rounded-xl px-3.5 py-2 text-sm text-ink cursor-pointer border border-rule/30 focus:border-accent/40 outline-none"
        :value="status"
        @change="applyStatus(($event.target as HTMLSelectElement).value as any)"
      >
        <option value="all">{{ t('filterStatusAll') }}</option>
        <option value="completed">{{ t('filterStatusCompleted') }}</option>
        <option value="failed">{{ t('filterStatusFailed') }}</option>
      </select>
    </div>

    <!-- 网格 -->
    <!-- P1 a11y：第一次加载显示「lädt」而非空白，并按轮询更新告知屏幕阅读器 -->
    <p
      v-if="loading && !items.length"
      class="text-muted text-sm mb-4"
      role="status"
      aria-live="polite"
    >
      {{ t('loading') }}
    </p>
    <!-- Logikcheck Befund 10: Ladefehler getrennt vom echten Leerzustand zeigen -->
    <div
      v-if="loadError && !loading"
      class="flex flex-wrap items-center gap-3 mb-4 p-3 rounded-xl panel-danger"
      role="alert"
    >
      <span class="text-sm text-danger">{{ t('galleryLoadError') }}</span>
      <button
        class="btn-danger-soft"
        @click="loadGallery"
      >
        {{ t('btnRetry') }}
      </button>
    </div>
    <p v-if="!loading && !loadError && !items.length" class="text-muted text-sm">{{ t('galleryEmpty') }}</p>
    <div v-if="items.length" class="grid grid-cols-2 sm:grid-cols-3 gap-4">
      <article
        v-for="it in items"
        :key="it.task_id"
        class="neu-raised rounded-2xl overflow-hidden cursor-pointer group transition-all hover:translate-y-[-2px] border border-rule/20"
        @click="openItem(it.task_id, it.dir_name, it.task_type)"
      >
        <div class="relative aspect-video bg-paper-2 overflow-hidden neu-sunken">
          <!-- 视频：优先用服务端惰性缩略图作封面；缺失时用原生首帧；hover 播放 -->
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
          <!-- 图片：直链现有端点 -->
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
  </div>
</template>