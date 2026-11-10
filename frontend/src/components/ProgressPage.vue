<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed, watch } from 'vue'
import { t } from '@/i18n'
import { appState } from '@/store'
import { useProgress } from '@/composables/useProgress'
import { useArtifacts } from '@/composables/useArtifacts'
import { useNavigation } from '@/composables/useNavigation'
import { useCompletionNotify } from '@/composables/useCompletionNotify'
import { useModalA11y } from '@/composables/useModalA11y'
import { useToast } from '@/composables/useToast'
import * as api from '@/api'
import { TASK_MANIFEST, buildDraftFromTaskState } from '@/taskManifest'
import type { TaskType } from '@/types'
import { etaForTask, formatDuration } from '@/utils/progressEta'
import ProgressHeader from './ProgressHeader.vue'
import StepTimeline from './StepTimeline.vue'
import ArtifactCard from './ArtifactCard.vue'
import CheckpointDetail from './CheckpointDetail.vue'
import FeedbackPanel from './FeedbackPanel.vue'
import LutSelector from '@/components/shared/LutSelector.vue'
import { isDeterministicError, isLocalNetworkError } from '@/utils/feedback'

const { showToast } = useToast()

const {
  progressPct,
  progressMessage,
  resultVideoVisible,
  resultVideoSrc,
  steps,
  stepStates,
  taskFailed,
  taskNotFound,
  failedMessage,
  liveFailedStep,
  awaitingCheckpoint,
  retryCount,
  connectionLost,
  retryFailedTask,
  mountProgressPage,
  unmountProgressPage,
} = useProgress()

const {
  artifactsAreaVisible,
  artifactGroups,
  imageModalUrl,
  stepLabelMap,
  closeImageModal,
} = useArtifacts()

const { goBack } = useNavigation()

// P2 完成通知：任务在后台跑完时提醒用户（需用户显式开启）
const { permission: notifyPermission, enabled: notifyEnabled, enable: enableNotify, disable: disableNotify, notify: notifyCompletion } = useCompletionNotify()
watch(taskFailed, (failed) => {
  if (!failed) return
  notifyCompletion(appState.progressTaskId || '', false, failedMessage.value || '')
})
watch(resultVideoSrc, () => {
  resultVideoError.value = false
})
watch(progressPct, (pct, prev) => {
  if (pct >= 100 && (prev ?? 0) < 100 && !taskFailed.value) {
    notifyCompletion(appState.progressTaskId || '', true, '')
  }
})

// 产物流按执行顺序排列（steps 顺序优先，未知 step 保持后端相对顺序）
const orderedGroups = computed(() => {
  const order = steps.value.map((s) => s.key)
  const map: Record<string, (typeof artifactGroups.value)[0]> = {}
  artifactGroups.value.forEach((g) => {
    if (!map[g.stepKey]) map[g.stepKey] = g
  })
  const keys = Object.keys(map)
  keys.sort((a, b) => {
    const ia = order.indexOf(a)
    const ib = order.indexOf(b)
    if (ia === -1 && ib === -1) return 0
    if (ia === -1) return 1
    if (ib === -1) return -1
    return ia - ib
  })
  return keys.map((k) => map[k])
})

// 折叠状态：默认只展开「最近一个环节」的产物，之前的历史环节自动折叠
// （暂停点时主体聚焦当前检查点产物；自动模式时主体聚焦最近生成环节）
const collapsed = ref<Record<string, boolean>>({})
function toggleCollapse(key: string) {
  collapsed.value[key] = !collapsed.value[key]
}

// 当前聚焦分组 = 最新产物分组（暂停点高亮 + 大图展示；自动模式为主体的最近环节）
const focusGroup = computed(() => {
  const groups = orderedGroups.value
  return groups.length ? groups[groups.length - 1].stepKey : null
})

function isCollapsed(key: string): boolean {
  if (key in collapsed.value) return collapsed.value[key]
  // 仅展开最近一个环节，之前的全部自动折叠（页面主体留给当前环节/暂停点产物）
  return key !== focusGroup.value
}

// 当前暂停点产物分组（用于高亮 + 大图展示）
const checkpointGroup = computed(() => {
  if (!awaitingCheckpoint.value) return null
  return focusGroup.value
})

// 步骤定位：点击时间线滚动到对应产物分组
function scrollToStep(stepKey: string) {
  const el = document.getElementById('artifact-group-' + stepKey)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// ── v6.1 问题反馈：失败任务重试（断点续传自愈偶发故障）──
async function onRetryTask() {
  const taskId = appState.progressTaskId
  if (taskId) await retryFailedTask(taskId)
}

// Logikcheck Befund 2：任务不存在时提供回列表出口（hash 写入后由
// hashchange 路由接管，正确停止轮询并挂载列表）
function goToTaskList() {
  location.hash = '#/list'
}

// ── 任务信息展示（优化 v6.1：展示用户输入提示词与各项配置）──
const taskInfo = ref<any>(null)
const taskInfoOpen = ref(true)

// P1 剩余时间：由 created_at + 当前进度线性外推（见 utils/progressEta.ts）。
// 进度太低 / 旧任务无时间戳时估算函数返回 insufficient，这里就不显示——不猜。
const eta = computed(() =>
  etaForTask({ created_at: taskInfo.value?.created_at } as any, progressPct.value),
)
const etaText = computed(() =>
  eta.value.state === 'estimating' && eta.value.remainingSec !== null
    ? formatDuration(eta.value.remainingSec)
    : '',
)

const taskInputs = computed(() => TASK_MANIFEST[appState.currentTaskType as TaskType]?.inputFields || [])
const taskConfigs = computed(() => TASK_MANIFEST[appState.currentTaskType as TaskType]?.configFields || [])

// v6.1 问题反馈：诊断报告用的关键配置字符串列表（复用 taskConfigs 展示逻辑）
const feedbackConfigs = computed(() =>
  taskConfigs.value
    .map((c) => {
      const v = c.fmt ? c.fmt(taskInfo.value?.[c.field]) : taskInfo.value?.[c.field]
      return v ? `${t(c.label)}: ${v}` : null
    })
    .filter((s): s is string => !!s),
)

// v6.1 问题反馈：错误是否为确定性故障（命中则切换引导文案 + 弱化重试按钮）
// v6.4.8：本机网络/域名解析故障单列一类，引导是「查 DNS/代理」，不套参数类文案
const networkError = computed(() => isLocalNetworkError(failedMessage.value))
const deterministicError = computed(
  () => !networkError.value && isDeterministicError(failedMessage.value),
)
// 两类「重试大概率无效」的故障：统一弱化重试按钮
const retryIneffective = computed(() => networkError.value || deterministicError.value)

// 诊断报告的失败环节：优先后端实时环节名，回退页面挂载时的快照（issue #56/#57）
const reportFailedStep = computed(
  () => liveFailedStep.value || taskInfo.value?.current_step || '',
)

const imageModalVisible = computed(() => !!imageModalUrl.value)
const { containerRef: imageModalRef } = useModalA11y(imageModalVisible, closeImageModal)

// Task clone + Post-process editor (Trim · LUT · Aspect Crop)
const resultVideoError = ref(false)
const postOpen = ref(false)
const postStart = ref(0)
const postEnd = ref(0)
const postLutId = ref('')
const postAspect = ref<'keep' | '9:16' | '16:9' | '1:1'>('keep')
const postBusy = ref(false)
const postResult = ref<{ video_url: string; download_url: string } | null>(null)

function cloneCurrentTask() {
  if (!taskInfo.value) return
  const mapped = buildDraftFromTaskState(taskInfo.value)
  if (!mapped) {
    showToast(t('taskCloneUnsupported'), 3000)
    return
  }
  localStorage.setItem('wb_draft_' + mapped.draftKey, JSON.stringify(mapped.payload))
  appState.createTaskType = mapped.createTab
  appState.view = 'create'
  appState.progressTaskId = null
  location.hash = '#/create'
  showToast(t('taskCloned'), 3000, 'success')
}

async function runPostprocess() {
  const id = appState.progressTaskId
  if (!id) return
  postBusy.value = true
  postResult.value = null
  try {
    const fd = new FormData()
    fd.append('start_sec', String(postStart.value || 0))
    fd.append('end_sec', String(postEnd.value || 0))
    fd.append('lut_id', postLutId.value)
    fd.append('aspect', postAspect.value)
    const res = await api.postprocessVideo(id, fd)
    if (res?.ok) {
      postResult.value = { video_url: res.video_url, download_url: res.download_url }
      showToast(t('postprocessDone'), 3000, 'success')
    }
  } catch (e: any) {
    showToast(e?.message || t('failCreate'), 4000, 'error')
  } finally {
    postBusy.value = false
  }
}

onMounted(async () => {
  const taskId = appState.progressTaskId
  if (!taskId) return
  taskInfo.value = await mountProgressPage(taskId, appState.currentDirName)
})

onUnmounted(() => {
  unmountProgressPage()
})
</script>

<template>
  <div class="progress-page min-h-screen">
    <ProgressHeader />

    <div class="max-w-6xl mx-auto px-4 py-6 lg:flex lg:gap-6">
      <!-- 左侧：环节状态列表（宽屏） -->
      <aside class="hidden lg:block w-[240px] shrink-0">
        <div class="sticky top-[120px]">
          <StepTimeline @locate="scrollToStep" />
        </div>
      </aside>

      <!-- 主工作台 -->
      <main class="flex-1 min-w-0">
        <!-- 移动端环节胶囊条 -->
        <div class="lg:hidden mb-4">
          <StepTimeline horizontal @locate="scrollToStep" />
        </div>

        <!-- 状态区 -->
        <div class="neu-card rounded-3xl p-6 mb-5 border border-rule/30">
          <div class="flex items-center justify-between mb-2.5">
            <span class="text-sm font-medium text-muted">{{ t('progress') }}</span>
            <span class="flex items-center gap-2">
              <span
                v-if="etaText"
                class="text-xs text-muted"
                role="status"
                aria-live="polite"
              >{{ t('etaRemaining').replace('{time}', etaText) }}</span>
              <span class="text-sm text-accent font-bold tabular-nums">{{ progressPct }}%</span>
            </span>
          </div>
          <!-- P2 完成通知开关：浏览器需用户手势才能申请权限，故放在进度区显眼处 -->
          <div v-if="notifyPermission !== 'unsupported'" class="flex items-center gap-2 mb-3">
            <button
              v-if="!notifyEnabled"
              type="button"
              class="text-[11px] px-3 py-1 rounded-xl neu-raised hover:neu-sunken text-ink-2 hover:text-ink transition flex items-center gap-1.5"
              :disabled="notifyPermission === 'denied'"
              @click="enableNotify"
            >
              <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span>{{ notifyPermission === 'denied' ? t('notifyBlocked') : t('notifyEnable') }}</span>
            </button>
            <button
              v-else
              type="button"
              class="text-[11px] px-3 py-1 rounded-xl neu-sunken text-success hover:text-ink transition flex items-center gap-1.5"
              @click="disableNotify"
            >
              <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span>{{ t('notifyOn') }}</span>
            </button>
          </div>
          <!-- P1 a11y：轮询更新的进度对屏幕阅读器也要可感知（role=progressbar） -->
          <div
            class="w-full neu-sunken rounded-full h-3.5 p-0.5 overflow-hidden"
            role="progressbar"
            :aria-valuenow="progressPct"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-label="t('progress')"
          >
            <div class="bg-accent h-full rounded-full transition-all duration-500 shadow-sm" :style="{ width: progressPct + '%' }"></div>
          </div>

          <!-- 失败信息 -->
          <div v-if="taskFailed" class="mt-4 p-4 panel-danger rounded-lg space-y-2" role="alert">
            <p class="text-danger font-medium">{{ t('genFailed') }}</p>
            <p class="text-muted text-xs">{{ failedMessage || t('genFailedMsg') }}</p>
            <!-- v6.1 问题反馈：重试引导（偶发故障优先断点续传自愈，多次失败再上报） -->
            <div class="pt-2 border-t border-danger/30 space-y-2">
              <!-- 引导文案：网络/域名类 → 自查环境；确定性故障 → 建议直接反馈；其余 → 断点续传自愈 -->
              <p class="text-xs leading-relaxed" :class="retryIneffective ? 'text-warning' : 'text-muted'">
                {{ networkError ? t('fbNetworkHint') : deterministicError ? t('fbDeterministicHint') : t('fbRetryHint') }}
              </p>
              <div class="flex items-center gap-3 flex-wrap">
                <button
                  class="text-xs px-3 py-1.5 transition rounded-lg flex items-center gap-1.5"
                  :class="retryIneffective ? 'bg-paper-2/40 border border-rule text-muted hover:text-ink-2' : 'bg-accent text-accent-ink hover:opacity-90'"
                  @click="onRetryTask"
                >
                  <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>{{ t('btnRetry') }}</span>
                </button>
                <span v-if="retryCount > 0" class="text-xs text-muted">{{ t('fbRetriedN').replace('{n}', String(retryCount)) }}</span>
              </div>
              <!-- v6.1 问题反馈：反馈区（渐进展开 + 复制 + FAQ + GitHub Issue） -->
              <FeedbackPanel
                v-if="appState.progressTaskId"
                :task-id="appState.progressTaskId"
                :task-type="appState.currentTaskType || 'creative'"
                :mode="taskInfo?.mode"
                :failed-step="reportFailedStep"
                :error-message="failedMessage || ''"
                :retry-count="retryCount"
                :configs="feedbackConfigs"
                @retry="onRetryTask"
              />
            </div>
          </div>
          <!-- 任务不存在（已删除 / 链接失效）：明确终态 + 回列表入口 -->
          <div v-else-if="taskNotFound" class="mt-4 p-4 panel-danger rounded-lg space-y-3" role="alert">
            <p class="text-danger font-medium">{{ t('taskNotFound') }}</p>
            <button
              class="text-xs px-3 py-1.5 rounded-lg bg-paper-2/40 border border-rule text-ink-2 hover:text-ink transition"
              @click="goToTaskList"
            >
              {{ t('tabList') }}
            </button>
          </div>
          <!-- 进度消息（HTML 渲染，来自后端安全文案） -->
          <!-- P1 a11y：轮询文案对屏幕阅读器播报，polite 避免打断用户操作 -->
          <div
            v-else
            class="mt-4 text-sm text-muted"
            role="status"
            aria-live="polite"
            aria-atomic="true"
            v-html="progressMessage"
          ></div>

          <!-- 1.7：连接异常横幅（连续轮询失败 N 次后展示） -->
          <div
            v-if="connectionLost"
            class="mt-3 rounded-lg panel-danger px-3 py-2 text-xs text-danger"
            role="status"
            aria-live="polite"
          >
            {{ t('connLost') }}
          </div>
        </div>

        <!-- 任务信息（用户输入提示词 + 各项配置，v6.1） -->
        <div v-if="taskInfo" class="glass-card rounded-2xl mb-4 overflow-hidden">
          <button class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-paper-2/30 transition" @click="taskInfoOpen = !taskInfoOpen">
            <span class="text-sm transition-transform" :class="taskInfoOpen ? 'rotate-90' : ''">▸</span>
            <span class="text-sm font-medium text-ink-2">{{ t('taskInfo') }}</span>
            <span class="ml-auto text-xs text-muted">{{ taskInfoOpen ? t('ppCollapse') : t('ppExpand') }}</span>
          </button>

          <div v-show="taskInfoOpen" class="px-4 pb-4 space-y-3">
            <!-- 输入提示词 -->
            <div v-for="f in taskInputs" :key="f.field" class="space-y-1">
              <div class="text-xs text-muted">{{ t(f.label) }}</div>
              <p class="text-sm text-ink-2 bg-paper-2/30 rounded-lg px-3 py-2 whitespace-pre-wrap break-words leading-relaxed">
                {{ taskInfo[f.field] || '-' }}
              </p>
            </div>

            <!-- 关键配置 -->
            <div v-if="taskConfigs.length" class="flex flex-wrap gap-x-6 gap-y-2 pt-1">
              <div v-for="c in taskConfigs" :key="c.field" class="flex items-center gap-1.5 text-xs">
                <span class="text-muted">{{ t(c.label) }}:</span>
                <span class="text-ink-2 font-mono">{{ c.fmt ? c.fmt(taskInfo[c.field]) : (taskInfo[c.field] || '-') }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 产物流：逐步追加（按环节分组，已完成折叠） -->
        <div v-if="artifactsAreaVisible" class="space-y-3">
          <div
            v-for="g in orderedGroups"
            :id="'artifact-group-' + g.stepKey"
            :key="g.stepKey"
            class="artifact-group glass-card rounded-2xl overflow-hidden"
            :class="g.stepKey === checkpointGroup ? 'border-amber-500/40 ring-1 ring-amber-500/20' : ''"
          >
            <button
              class="w-full flex items-center gap-3 px-4 py-3 text-left transition hover:bg-paper-2/30"
              :class="g.stepKey === checkpointGroup ? 'bg-amber-500/5' : ''"
              @click="toggleCollapse(g.stepKey)"
            >
              <span class="text-sm transition-transform" :class="isCollapsed(g.stepKey) ? '' : 'rotate-90'">▸</span>
              <span class="text-sm font-medium" :class="g.stepKey === checkpointGroup ? 'text-warning' : 'text-ink-2'">{{ t(stepLabelMap[g.stepKey] || g.stepKey) }}</span>
              <span v-if="g.stepKey === checkpointGroup" class="badge-warning shrink-0">⏸ {{ t('awaitingUser') }}</span>
              <span class="text-xs text-muted">{{ g.items.length }} {{ t('itemsUnit') }}</span>
              <span class="ml-auto text-xs text-muted">{{ isCollapsed(g.stepKey) ? t('ppExpand') : t('ppCollapse') }}</span>
            </button>

            <div v-show="!isCollapsed(g.stepKey)" class="px-4 pb-4 space-y-2" :class="g.stepKey === checkpointGroup ? 'px-5 pb-5' : ''">
              <ArtifactCard v-for="art in g.items" :key="art.artifact_id" :art="art" :large="g.stepKey === checkpointGroup" />
            </div>
          </div>
        </div>

        <!-- 暂停审查区：紧跟最新产物（就近操作） -->
        <CheckpointDetail
          v-if="awaitingCheckpoint && appState.currentTaskId"
          :task-id="appState.currentTaskId"
          :checkpoint="awaitingCheckpoint"
        />

        <!-- 结果视频 -->
        <div v-if="resultVideoVisible" class="mt-4 p-5 neu-card rounded-3xl border border-rule/30">
          <div class="flex items-center gap-2 mb-3">
            <span class="w-3 h-3 rounded-full bg-success inline-block shadow-sm"></span>
            <p class="text-success text-sm font-semibold">{{ t('videoComplete') }}</p>
          </div>
          <div class="neu-sunken rounded-2xl p-2 mb-4 bg-paper-3/40">
            <video :src="resultVideoSrc" controls class="w-full rounded-xl max-h-96 shadow-sm" @error="resultVideoError = true"></video>
            <p v-if="resultVideoError" class="text-xs text-danger mt-2">{{ t('videoLoadFailed') }}</p>
          </div>
          <div class="mt-3 flex flex-wrap items-center gap-2.5">
            <a
              :href="resultVideoSrc + '?download=1'"
              download
              class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold transition glow-btn"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
              {{ t('downloadVideo') }}
            </a>
            <button
              v-if="taskInfo"
              type="button"
              class="px-4 py-2.5 rounded-xl text-xs font-medium bg-paper-2 border border-rule text-ink-2 hover:text-ink transition"
              @click="cloneCurrentTask"
            >
              {{ t('taskCloneBtn') }}
            </button>
            <button
              type="button"
              class="px-4 py-2.5 rounded-xl text-xs font-medium bg-paper-2 border border-rule text-ink-2 hover:text-ink hover:border-accent/50 transition"
              :aria-expanded="postOpen"
              @click="postOpen = !postOpen"
            >
              {{ t('postprocessToggle') }}
            </button>
          </div>

          <!-- Post-Process Editor (Trim · LUT · Aspect Crop) -->
          <div v-if="postOpen" class="mt-4 p-4 rounded-2xl bg-paper border border-rule space-y-3">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label class="block text-xs text-muted mb-1">{{ t('mvTrimStart') }}</label>
                <input v-model.number="postStart" type="number" min="0" step="0.5" class="w-full glass-input rounded-lg px-3 py-1.5 text-xs text-ink" />
              </div>
              <div>
                <label class="block text-xs text-muted mb-1">{{ t('mvTrimEnd') }}</label>
                <input v-model.number="postEnd" type="number" min="0" step="0.5" class="w-full glass-input rounded-lg px-3 py-1.5 text-xs text-ink" />
              </div>
              <div>
                <label class="block text-xs text-muted mb-1">{{ t('postprocessAspect') }}</label>
                <select v-model="postAspect" class="w-full glass-input rounded-lg px-3 py-1.5 text-xs text-ink">
                  <option value="keep">{{ t('postprocessAspectKeep') }}</option>
                  <option value="9:16">9:16</option>
                  <option value="16:9">16:9</option>
                  <option value="1:1">1:1</option>
                </select>
              </div>
            </div>
            <LutSelector v-model="postLutId" />
            <button
              type="button"
              class="px-4 py-2 rounded-lg text-xs font-semibold glow-btn disabled:opacity-50"
              :disabled="postBusy"
              @click="runPostprocess"
            >
              {{ postBusy ? t('loading') : t('postprocessApply') }}
            </button>

            <div v-if="postResult" class="pt-3 border-t border-rule/50 space-y-2">
              <video :src="postResult.video_url" controls class="w-full rounded-xl max-h-80"></video>
              <a
                :href="postResult.download_url"
                download
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold glow-btn"
              >
                {{ t('postprocessDownload') }}
              </a>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-xs">
            <span class="w-2 h-2 rounded-full bg-success inline-block"></span>
            <a href="https://video.lichuanyang.top/learn" target="_blank" rel="noopener" class="text-accent hover:text-ink transition-colors">{{ t('doneTipTiktok') }}</a>
            <span class="text-rule select-none">·</span>
            <a href="https://video.lichuanyang.top/learn" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('doneTipMore') }}</a>
          </div>
        </div>

        <!-- 官网导流资源（更多资源链接，与主页一致） -->
        <div class="mt-8 border-t border-rule/30 pt-6 text-center">
          <p class="text-xs text-muted mb-3">{{ t('moreResources') }}</p>
          <div class="flex justify-center flex-wrap gap-x-5 gap-y-2 text-xs">
            <a href="https://video.lichuanyang.top" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('projectHome') }}</a>
            <a href="https://video.lichuanyang.top/demo" target="_blank" rel="noopener" class="text-accent hover:text-ink transition-colors">{{ t('onlineDemo') }}</a>
            <a href="https://video.lichuanyang.top/guides/prompt-tips" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('usageGuide') }}</a>
            <a href="https://video.lichuanyang.top/guides/prompt-tips" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('promptTips') }}</a>
            <a href="https://video.lichuanyang.top/faq" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('faqTitle') }}</a>
            <a href="https://video.lichuanyang.top/api-docs" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('modelOverview') }}</a>
            <a href="https://video.lichuanyang.top/api-docs" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('apiCall') }}</a>
            <a href="https://video.lichuanyang.top/api-docs" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('apiDocs') }}</a>
            <a href="https://video.lichuanyang.top/learn" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('appScenarios') }}</a>
            <a href="https://video.lichuanyang.top/zh/guides/free-ai-tools" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('agentMoreTools') }}</a>
            <a href="https://github.com/lcy362/flint" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">{{ t('flintLinkLabel') }}</a>
            <a href="https://github.com/lcy362/agnes-video-generator" target="_blank" rel="noopener" class="text-muted hover:text-ink-2 transition-colors">GitHub</a>
          </div>
        </div>
      </main>
    </div>

    <!-- 图片放大弹窗 -->
    <div
      v-if="imageModalUrl"
      ref="imageModalRef"
      class="fixed inset-0 z-[75] flex items-center justify-center bg-black/80 p-4"
      role="dialog"
      aria-modal="true"
      :aria-label="t('imagePreviewTitle')"
      @click.self="closeImageModal"
    >
      <div class="relative max-w-[90vw] max-h-[90vh]">
        <button
          type="button"
          class="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-paper-2 border border-rule text-ink flex items-center justify-center hover:border-accent transition"
          :aria-label="t('close')"
          @click="closeImageModal"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <img :src="imageModalUrl" :alt="t('imagePreviewTitle')" class="max-w-[90vw] max-h-[85vh] rounded-lg" />
      </div>
    </div>
  </div>
</template>
