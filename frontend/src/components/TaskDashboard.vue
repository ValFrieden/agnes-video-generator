<script setup lang="ts">
// 项目概览（Project Dashboard）—— 把任务列表上方那块空白变成可读的仪表盘。
// 纯前端聚合：数据来自 useTasks().tasks（一次 /api/tasks 轮询已在跑），
// 不新增接口、不新增轮询。图表用 div 宽度画，不引图表库。
import { computed } from 'vue'
import { t } from '@/i18n'
import { useTasks } from '@/composables/useTasks'
import { computeActivity, computeTaskStats, computeTypeSlices } from '@/utils/taskStats'
import { TYPE_LABEL_KEY_MAP } from '@/taskManifest'

const { tasks } = useTasks()

const total = computed(() => tasks.value.length)
const stats = computed(() => computeTaskStats(tasks.value))
const counts = computed(() => stats.value.counts)
const successRate = computed(() => stats.value.successRate)
const activeNow = computed(() => stats.value.activeNow)

const byType = computed(() =>
  computeTypeSlices(tasks.value).map((slice) => ({
    ...slice,
    labelKey: TYPE_LABEL_KEY_MAP[slice.key] || 'typeCreative',
  })),
)

const activity = computed(() => computeActivity(tasks.value, 14))
const activityMax = computed(() => Math.max(1, ...activity.value.map((d) => d.count)))
const hasActivity = computed(() => activity.value.some((d) => d.count > 0))

function barHeight(count: number): string {
  // 最小可见高度 6%，避免「有一天有任务」看起来像空的
  return `${count ? Math.max(6, (count / activityMax.value) * 100) : 0}%`
}
</script>

<template>
  <section v-if="total" class="neu-card rounded-2xl p-5 mb-5 border border-rule/30">
    <div class="flex items-center gap-2 mb-3.5">
      <div class="w-7 h-7 rounded-lg neu-raised flex items-center justify-center text-accent">
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      </div>
      <h2 class="text-sm font-semibold text-ink">{{ t('dbTitle') }}</h2>
      <span class="text-xs text-muted ml-auto tabular-nums px-2.5 py-0.5 rounded-full neu-sunken">{{ t('dbTotal').replace('{n}', String(total)) }}</span>
    </div>

    <!-- Unified Divided KPI Strip (app-screens.md §5 standard) -->
    <div class="grid grid-cols-2 sm:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-rule/40 rounded-xl neu-sunken border border-rule/30 mb-4 overflow-hidden">
      <div class="p-3">
        <div class="text-xs text-muted mb-1">{{ t('statusRunning') }} / {{ t('statusQueued') }}</div>
        <div class="text-2xl font-semibold tabular-nums" :class="activeNow ? 'text-accent' : 'text-ink'">{{ activeNow }}</div>
      </div>
      <div class="p-3">
        <div class="text-xs text-muted mb-1">{{ t('statusCompleted') }}</div>
        <div class="text-2xl font-semibold tabular-nums text-success">{{ counts.completed }}</div>
      </div>
      <div class="p-3">
        <div class="text-xs text-muted mb-1">{{ t('statusFailed') }}</div>
        <div class="text-2xl font-semibold tabular-nums" :class="counts.failed > 0 ? 'text-danger' : 'text-ink'">{{ counts.failed }}</div>
      </div>
      <div class="p-3">
        <div class="text-xs text-muted mb-1">{{ t('dbSuccessRate') }}</div>
        <div class="text-2xl font-semibold tabular-nums" :class="successRate === null ? 'text-muted' : successRate >= 80 ? 'text-success' : 'text-warning'">
          {{ successRate === null ? '-' : successRate + '%' }}
        </div>
      </div>
    </div>

    <!-- 类型分布 -->
    <div v-if="byType.length" class="mb-4">
      <div class="text-xs text-muted mb-2">{{ t('dbByType') }}</div>
      <div class="space-y-2">
        <div v-for="row in byType" :key="row.key" class="flex items-center gap-2">
          <span class="text-xs text-ink-2 w-28 shrink-0 truncate">{{ t(row.labelKey) }}</span>
          <div class="flex-1 h-2 neu-sunken rounded-full overflow-hidden p-0.5">
            <div class="h-full rounded-full bg-accent" :style="{ width: row.pct + '%' }"></div>
          </div>
          <span class="text-xs text-muted w-10 text-right tabular-nums shrink-0">{{ row.value }}</span>
        </div>
      </div>
    </div>

    <!-- 最近 14 天活动 -->
    <div v-if="hasActivity">
      <div class="text-xs text-muted mb-2">{{ t('dbActivity') }}</div>
      <div class="flex items-end gap-1.5 h-16 border-b border-rule/40 pb-1 neu-sunken rounded-xl p-2" role="img" :aria-label="t('dbActivity')">
        <div
          v-for="day in activity"
          :key="day.key"
          class="flex-1 flex flex-col justify-end items-center group h-full"
          :title="day.key + ' · ' + day.count"
        >
          <div
            class="w-full rounded-t-sm bg-accent/60 group-hover:bg-accent transition-colors"
            :style="{ height: barHeight(day.count) }"
          ></div>
        </div>
      </div>
      <div class="flex justify-between text-[11px] text-muted mt-1.5 tabular-nums">
        <span>{{ activity[0]?.key }}</span>
        <span>{{ activity[activity.length - 1]?.key }}</span>
      </div>
    </div>
    <p v-else class="text-xs text-muted">{{ t('dbNoActivity') }}</p>
  </section>
</template>
