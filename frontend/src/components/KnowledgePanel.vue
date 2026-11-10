<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { t, tf } from '@/i18n'
import { useToast } from '@/composables/useToast'
import { useModalA11y } from '@/composables/useModalA11y'

interface SearchItem {
  document_id?: number
  title: string
  rel_path?: string
  category: string
  heading?: string
  snippet: string
  score?: number
  modified_at?: string
  source: 'project' | 'watch'
  report_path?: string
}

interface DocDetails {
  id: number
  rel_path: string
  title: string
  category: string
  word_count: number
  modified_at: string
  content: string
}

interface StatusData {
  ready: boolean
  document_count: number
  section_count: number
  database_path: string
  categories: Record<string, number>
  top_tools: string[]
  graph_nodes?: number | null
  graph_edges?: number | null
}

const { showToast } = useToast()

const loading = ref(false)
const syncing = ref(false)
const searchQuery = ref('')
const selectedCategory = ref('')
const crossSearch = ref(true)
const statusData = ref<StatusData | null>(null)
const results = ref<SearchItem[]>([])
const hasSearched = ref(false)

// Document Modal
const activeDoc = ref<DocDetails | null>(null)
const docLoading = ref(false)
const isModalOpen = ref(false)

const categoriesList = computed(() => {
  if (!statusData.value?.categories) return []
  return Object.keys(statusData.value.categories).sort()
})

async function fetchStatus() {
  try {
    const res = await fetch('/api/knowledge/status').then((r) => r.json())
    if (res.ok && res.data) {
      statusData.value = res.data
    }
  } catch (e) {
    console.error('Failed to fetch knowledge status:', e)
  }
}

async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) {
    results.value = []
    hasSearched.value = false
    return
  }

  loading.value = true
  hasSearched.value = true
  try {
    const params = new URLSearchParams({
      q,
      cross_search: crossSearch.value ? 'true' : 'false',
      limit: '20',
    })
    if (selectedCategory.value) {
      params.append('category', selectedCategory.value)
    }

    const res = await fetch(`/api/knowledge/search?${params.toString()}`).then((r) => r.json())
    if (res.ok) {
      const list: SearchItem[] = []
      if (res.results && Array.isArray(res.results)) {
        list.push(...res.results.map((r: any) => ({ ...r, source: 'project' as const })))
      }
      if (res.watch_results && Array.isArray(res.watch_results)) {
        list.push(...res.watch_results.map((r: any) => ({ ...r, source: 'watch' as const })))
      }
      results.value = list
    } else {
      showToast(res.detail || 'Search failed', 2500, 'error')
    }
  } catch (e: any) {
    showToast(e.message || 'Search error', 2500, 'error')
  } finally {
    loading.value = false
  }
}

function handleCategoryClick(cat: string) {
  if (selectedCategory.value === cat) {
    selectedCategory.value = ''
  } else {
    selectedCategory.value = cat
  }
  if (searchQuery.value.trim()) {
    doSearch()
  }
}

function handleToolClick(tool: string) {
  searchQuery.value = tool
  doSearch()
}

async function triggerSync() {
  syncing.value = true
  try {
    const res = await fetch('/api/knowledge/sync?rebuild=false', { method: 'POST' }).then((r) => r.json())
    if (res.ok) {
      showToast(
        `Synchronized: ${res.result.indexed_or_updated} updated, ${res.result.total_documents} total docs`,
        3000,
        'success'
      )
      await fetchStatus()
      if (searchQuery.value.trim()) {
        await doSearch()
      }
    } else {
      showToast(res.detail || 'Sync failed', 2500, 'error')
    }
  } catch (e: any) {
    showToast(e.message || 'Sync error', 2500, 'error')
  } finally {
    syncing.value = false
  }
}

async function openDocument(item: SearchItem) {
  if (item.source !== 'project' || !item.document_id) {
    return
  }
  docLoading.value = true
  isModalOpen.value = true
  try {
    const res = await fetch(`/api/knowledge/document/${item.document_id}`).then((r) => r.json())
    if (res.ok && res.document) {
      activeDoc.value = res.document
    } else {
      showToast(res.detail || 'Failed to load document', 2500, 'error')
      isModalOpen.value = false
    }
  } catch (e: any) {
    showToast(e.message || 'Failed to load document', 2500, 'error')
    isModalOpen.value = false
  } finally {
    docLoading.value = false
  }
}

function closeModal() {
  isModalOpen.value = false
  activeDoc.value = null
}

const { containerRef: docModalRef } = useModalA11y(isModalOpen, closeModal)

function getCategoryColor(category: string): string {
  // P0: vorher rohe Tailwind-Palette (purple-400/blue-400/neutral-300) — im hellen
  // Thema zu blass. Jetzt semantische Badge-Klassen aus style.css, die aus den
  // Design-Tokens mischen und in beiden Themen lesbar bleiben.
  switch (category) {
    case 'Rules & Standards':
      return 'badge-warning'
    case 'Screenplays & Playbooks':
      return 'badge-info'
    case 'Architecture & Dev':
      return 'badge-neutral'
    case 'Plans & Roadmaps':
      return 'badge-success'
    default:
      return 'badge-neutral'
  }
}

onMounted(() => {
  fetchStatus()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header Hero Banner -->
    <div class="glass-card rounded-2xl p-6 relative overflow-hidden">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 mb-1.5">
            <svg class="w-5 h-5 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <h2 class="text-xl sm:text-2xl font-bold text-ink">{{ t('knowledgeTitle') }}</h2>
          </div>
          <p class="text-sm text-muted">{{ t('knowledgeSubtitle') }}</p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <!-- Sync Button -->
          <button
            class="px-3.5 py-2 rounded-lg text-xs font-medium glass-card border border-rule/50 hover:border-accent/40 text-ink flex items-center gap-2 transition cursor-pointer"
            :disabled="syncing"
            @click="triggerSync"
          >
            <svg
              class="w-3.5 h-3.5"
              :class="{ 'animate-spin': syncing }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span>{{ syncing ? t('knowledgeSyncing') : t('knowledgeBtnSync') }}</span>
          </button>

          <!-- Open Code Graph Button -->
          <a
            href="/graphify-out/graph.html"
            target="_blank"
            rel="noopener"
            class="px-3.5 py-2 rounded-lg text-xs font-semibold glow-btn flex items-center gap-1.5 transition"
          >
            <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>{{ t('knowledgeBtnOpenGraph') }}</span>
          </a>
        </div>
      </div>

      <!-- Quick KPI Stats Cards -->
      <div v-if="statusData" class="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-4 border-t border-rule/30">
        <div class="p-3 rounded-xl bg-paper/60 border border-rule/30">
          <div class="text-xs text-muted">{{ t('knowledgeTotalDocs') }}</div>
          <div class="text-lg font-bold text-ink mt-0.5 tabular-nums">{{ statusData.document_count }}</div>
        </div>
        <div class="p-3 rounded-xl bg-paper/60 border border-rule/30">
          <div class="text-xs text-muted">{{ t('knowledgeTotalSections') }}</div>
          <div class="text-lg font-bold text-accent mt-0.5 tabular-nums">{{ statusData.section_count }}</div>
        </div>
        <div v-if="statusData.graph_nodes != null" class="p-3 rounded-xl bg-paper/60 border border-rule/30">
          <div class="text-xs text-muted">{{ t('knowledgeCodeNodes') }}</div>
          <div class="text-lg font-bold text-ink mt-0.5 tabular-nums">{{ statusData.graph_nodes.toLocaleString() }}</div>
        </div>
        <div v-if="statusData.graph_edges != null" class="p-3 rounded-xl bg-paper/60 border border-rule/30">
          <div class="text-xs text-muted">{{ t('knowledgeGraphEdges') }}</div>
          <div class="text-lg font-bold text-ink mt-0.5 tabular-nums">{{ statusData.graph_edges.toLocaleString() }}</div>
        </div>
      </div>
    </div>

    <!-- Search Box and Filters -->
    <div class="glass-card rounded-2xl p-5 space-y-4">
      <div class="relative">
        <input
          v-model="searchQuery"
          type="text"
          class="w-full glass-input rounded-xl px-4 py-3 pl-11 text-sm text-ink placeholder:text-muted/60 focus:outline-none"
          :placeholder="t('knowledgeSearchPlaceholder')"
          @keydown.enter="doSearch"
        />
        <svg
          class="w-5 h-5 text-muted absolute left-3.5 top-3.5 pointer-events-none"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>

        <button
          v-if="searchQuery"
          class="absolute right-3.5 top-3 text-muted hover:text-ink text-sm px-1.5 py-0.5 rounded transition flex items-center justify-center cursor-pointer"
          :aria-label="t('clear')"
          @click="searchQuery = ''; results = []; hasSearched = false"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>

      <!-- Controls row: Category dropdown & Cross-Search toggle -->
      <div class="flex flex-wrap items-center justify-between gap-3 text-xs">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-muted">{{ t('knowledgeCategoryLabel') }}:</span>
          <select
            v-model="selectedCategory"
            class="glass-input rounded-lg px-2.5 py-1.5 text-xs text-ink cursor-pointer"
            @change="doSearch"
          >
            <option value="">{{ t('knowledgeCategoriesAll') }}</option>
            <option v-for="cat in categoriesList" :key="cat" :value="cat">
              {{ cat }} ({{ statusData?.categories[cat] || 0 }})
            </option>
          </select>

          <!-- Cross-search toggle -->
          <label class="flex items-center gap-1.5 cursor-pointer ml-2 select-none text-muted hover:text-ink transition">
            <input
              v-model="crossSearch"
              type="checkbox"
              class="rounded border-rule bg-paper text-accent focus:ring-0 cursor-pointer"
              @change="searchQuery && doSearch()"
            />
            <span>{{ t('knowledgeCrossSearchLabel') }}</span>
          </label>
        </div>

        <button
          class="px-4 py-2 rounded-lg text-xs font-semibold glow-btn transition ml-auto"
          :disabled="loading"
          @click="doSearch"
        >
          <span v-if="loading" class="inline-block animate-spin mr-1">⌛</span>
          <span>{{ t('knowledgeBtnSearch') }}</span>
        </button>
      </div>

      <!-- Category Filter Pills -->
      <div v-if="statusData?.categories" class="flex flex-wrap gap-1.5 pt-2 border-t border-rule/20">
        <button
          v-for="(cnt, cat) in statusData.categories"
          :key="cat"
          class="px-2.5 py-1 rounded-full text-xs transition border flex items-center gap-1.5"
          :class="
            selectedCategory === cat
              ? 'bg-accent/20 text-accent border-accent/50 font-semibold'
              : 'bg-paper/40 text-muted border-rule/40 hover:border-rule hover:text-ink'
          "
          @click="handleCategoryClick(cat as string)"
        >
          <span>{{ cat }}</span>
          <span class="text-[10px] opacity-70">({{ cnt }})</span>
        </button>
      </div>

      <!-- Top Tools Chips -->
      <div v-if="statusData?.top_tools?.length" class="flex flex-wrap items-center gap-1.5 text-[11px] text-muted">
        <span>{{ t('knowledgePopularTags') }}:</span>
        <button
          v-for="tool in statusData.top_tools.slice(0, 10)"
          :key="tool"
          class="px-2 py-0.5 rounded bg-paper-2 hover:bg-paper-3 text-ink-2 hover:text-accent border border-rule/30 transition"
          @click="handleToolClick(tool)"
        >
          #{{ tool }}
        </button>
      </div>
    </div>

    <!-- Results Count Bar -->
    <div v-if="hasSearched" class="flex items-center justify-between text-xs text-muted px-1">
      <div>{{ tf('knowledgeSearchHits', { count: results.length }) }}</div>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="glass-card rounded-xl p-4 animate-pulse space-y-2">
        <div class="h-4 bg-paper-3 rounded w-1/3"></div>
        <div class="h-3 bg-paper-3 rounded w-3/4"></div>
        <div class="h-3 bg-paper-3 rounded w-1/2"></div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="hasSearched && !results.length"
      class="glass-card rounded-2xl p-8 text-center text-muted space-y-3"
    >
      <div class="flex justify-center text-muted">
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
      </div>
      <p class="text-sm max-w-md mx-auto">{{ t('knowledgeEmpty') }}</p>
    </div>

    <!-- Search Results Grid / List -->
    <div v-else-if="results.length" class="space-y-3">
      <article
        v-for="(item, idx) in results"
        :key="idx"
        class="glass-card rounded-xl p-4 transition hover:border-accent/40 group relative"
      >
        <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
          <div class="flex items-center gap-2 flex-wrap">
            <!-- Source Tag -->
            <span
              class="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border"
              :class="
                item.source === 'watch'
                  ? 'badge-danger'
                  : 'badge-info'
              "
            >
              {{ item.source === 'watch' ? t('knowledgeSourceVideo') : t('knowledgeSourceDoc') }}
            </span>

            <!-- Category Badge -->
            <span
              class="text-[11px] px-2 py-0.5 rounded-md border font-medium"
              :class="getCategoryColor(item.category)"
            >
              {{ item.category }}
            </span>
          </div>

          <!-- File path or report path -->
          <span class="text-xs text-muted/70 font-mono truncate max-w-xs">
            {{ item.rel_path || item.report_path || '' }}
          </span>
        </div>

        <!-- Title & Heading -->
        <h3 class="text-base font-semibold text-ink group-hover:text-accent transition flex items-center gap-2">
          <span>{{ item.title }}</span>
          <span v-if="item.heading" class="text-xs text-muted font-normal">→ {{ item.heading }}</span>
        </h3>

        <!-- Snippet with highlighted search matches -->
        <div
          class="text-xs text-muted leading-relaxed mt-2.5 bg-paper/40 p-2.5 rounded-lg border border-rule/20 font-mono overflow-x-auto whitespace-pre-wrap"
          v-html="item.snippet"
        ></div>

        <!-- Actions -->
        <div class="flex items-center justify-end gap-2 mt-3 pt-2 border-t border-rule/20">
          <button
            v-if="item.source === 'project'"
            class="text-xs px-2.5 py-1 rounded bg-paper-2 hover:bg-paper-3 text-ink hover:text-accent transition flex items-center gap-1.5 border border-rule/30 cursor-pointer"
            @click="openDocument(item)"
          >
            <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
            <span>{{ t('knowledgeViewDoc') }}</span>
          </button>
        </div>
      </article>
    </div>

    <!-- Document Preview Modal -->
    <div
      v-if="isModalOpen"
      ref="docModalRef"
      class="fixed inset-0 z-[75] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      :aria-label="activeDoc?.title || t('knowledgeDocViewerTitle')"
      @click.self="closeModal"
    >
      <div class="glass-card rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl border border-rule/50 bg-paper-2">
        <!-- Modal Header -->
        <div class="flex items-center justify-between p-4 border-b border-rule/40">
          <div>
            <h3 class="text-base font-bold text-ink flex items-center gap-2">
              <svg class="w-4 h-4 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <span>{{ activeDoc?.title || t('knowledgeDocViewerTitle') }}</span>
            </h3>
            <p v-if="activeDoc" class="text-xs text-muted font-mono mt-0.5">
              {{ activeDoc.rel_path }} · {{ activeDoc.word_count }} words
            </p>
          </div>
          <button
            class="text-muted hover:text-ink text-sm p-1.5 rounded-lg hover:bg-paper-3 transition cursor-pointer flex items-center justify-center"
            :aria-label="t('close')"
            @click="closeModal"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-6 overflow-y-auto flex-1 text-xs text-ink-2 leading-relaxed space-y-4 font-mono select-text">
          <div v-if="docLoading" class="text-center py-12 text-muted">
            <span class="inline-block animate-spin text-xl mb-2">⌛</span>
            <div>{{ t('loading') }}</div>
          </div>
          <div v-else-if="activeDoc" class="whitespace-pre-wrap bg-paper/70 p-4 rounded-xl border border-rule/30">
            {{ activeDoc.content }}
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="p-3 border-t border-rule/40 flex justify-end">
          <button class="px-4 py-1.5 rounded-lg text-xs font-medium glass-card hover:bg-paper-3 text-ink transition" @click="closeModal">
            {{ t('knowledgeClose') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
