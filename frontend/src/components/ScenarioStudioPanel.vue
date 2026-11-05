<script setup lang="ts">
// 剧本工坊（Scenario Studio）—— 把后端 ScenarioDirector 端到端搬到界面上。
// 此前 /api/scenario/generate 有完整实现却没有任何前端消费者（审计发现），
// 这里补上：一句话 → 3 幕 Beat Sheet + 角色卡 + 分镜板 + 自检结论。
import { computed, ref } from 'vue'
import { t } from '@/i18n'
import { generateScenario } from '@/api'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()

const idea = ref('')
const style = ref('Vintage Gouache Cel Animation, Edward Hopper lighting, cinematic 16:9')
const duration = ref(96)
const bpm = ref(120)
const scenes = ref(12)
const anchor = ref('A vibrant canary-yellow umbrella')

const busy = ref(false)
const error = ref('')
const result = ref<any>(null)
const openPrompts = ref<number | null>(null)

const blockers = computed(() =>
  (result.value?.project?.review || []).filter((i: any) => i.severity === 'blocker'),
)
const warnings = computed(() =>
  (result.value?.project?.review || []).filter((i: any) => i.severity !== 'blocker'),
)
const shots = computed(() => result.value?.project?.shots || [])
const character = computed(() => result.value?.project?.character || null)

function timecode(shot: any): string {
  const fmt = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
  }
  return `${fmt(shot.start_time_s)} – ${fmt(shot.end_time_s)}`
}

async function generate() {
  if (!idea.value.trim()) {
    showToast(t('scIdeaRequired'), 2200, 'error')
    return
  }
  busy.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await generateScenario({
      idea: idea.value,
      style: style.value,
      duration: Number(duration.value),
      bpm: Number(bpm.value),
      scenes: Number(scenes.value),
      anchor: anchor.value,
    })
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    busy.value = false
  }
}

function downloadMarkdown() {
  const md = result.value?.markdown || ''
  if (!md) return
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'scenario.md'
  a.click()
  URL.revokeObjectURL(url)
}

async function copyMarkdown() {
  const md = result.value?.markdown || ''
  if (!md) return
  try {
    await navigator.clipboard.writeText(md)
    showToast(t('scCopied'), 1800, 'success')
  } catch {
    showToast(t('scCopyFailed'), 2200, 'error')
  }
}

// Logikcheck Befund 9: Drehbuch-Studio Szenario direkt in CreativeForm übernehmen
function applyToCreativeForm() {
  const proj = result.value?.project
  if (!proj) return
  window.dispatchEvent(new CustomEvent('apply-scenario-to-creative', { detail: proj }))
  showToast(t('scApplied') || 'In Kreativ-Formular übernommen!', 2500, 'success')
  const el = document.getElementById('sc-idea')
  if (el) {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}
</script>

<template>
  <section class="neu-card rounded-3xl p-6 mb-5 border border-rule/30">
    <div class="flex items-center gap-2.5 mb-1">
      <div class="w-8 h-8 rounded-xl neu-raised flex items-center justify-center text-accent">
        <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"/></svg>
      </div>
      <h2 class="text-base font-semibold text-ink">{{ t('scTitle') }}</h2>
    </div>
    <p class="text-xs text-muted mb-4">{{ t('scSubtitle') }}</p>

    <!-- 输入区 -->
    <label class="block text-sm text-muted mb-1.5" for="sc-idea">{{ t('scIdea') }}</label>
    <textarea
      id="sc-idea"
      v-model="idea"
      rows="3"
      class="neu-sunken w-full rounded-xl px-3.5 py-2.5 text-sm text-ink mb-3.5 border border-rule/30 focus:border-accent/40 outline-none transition"
      :placeholder="t('scIdeaPlaceholder')"
    ></textarea>

    <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
      <div class="col-span-2 sm:col-span-3">
        <label class="block text-xs text-muted mb-1" for="sc-style">{{ t('scStyle') }}</label>
        <input id="sc-style" v-model="style" class="neu-sunken w-full rounded-xl px-3.5 py-2 text-sm text-ink border border-rule/30 focus:border-accent/40 outline-none transition" />
      </div>
      <div>
        <label class="block text-xs text-muted mb-1" for="sc-duration">{{ t('scDuration') }}</label>
        <input id="sc-duration" v-model.number="duration" type="number" min="10" class="neu-sunken w-full rounded-xl px-3.5 py-2 text-sm text-ink border border-rule/30 focus:border-accent/40 outline-none transition" />
      </div>
      <div>
        <label class="block text-xs text-muted mb-1" for="sc-bpm">{{ t('scBpm') }}</label>
        <input id="sc-bpm" v-model.number="bpm" type="number" min="40" max="240" class="neu-sunken w-full rounded-xl px-3.5 py-2 text-sm text-ink border border-rule/30 focus:border-accent/40 outline-none transition" />
      </div>
      <div>
        <label class="block text-xs text-muted mb-1" for="sc-scenes">{{ t('scScenes') }}</label>
        <input id="sc-scenes" v-model.number="scenes" type="number" min="1" max="40" class="neu-sunken w-full rounded-xl px-3.5 py-2 text-sm text-ink border border-rule/30 focus:border-accent/40 outline-none transition" />
      </div>
      <div class="col-span-2 sm:col-span-3">
        <label class="block text-xs text-muted mb-1" for="sc-anchor">{{ t('scAnchor') }}</label>
        <input id="sc-anchor" v-model="anchor" class="neu-sunken w-full rounded-xl px-3.5 py-2 text-sm text-ink border border-rule/30 focus:border-accent/40 outline-none transition" />
      </div>
    </div>

    <button
      class="px-5 py-2.5 rounded-xl text-sm font-semibold neu-raised hover:neu-sunken text-accent transition disabled:opacity-50 glow-btn"
      :disabled="busy"
      :aria-busy="busy"
      @click="generate"
    >
      {{ busy ? t('scGenerating') : t('scGenerate') }}
    </button>

    <!-- 状态区 -->
    <p v-if="busy" class="text-xs text-muted mt-3" role="status" aria-live="polite">{{ t('scGeneratingHint') }}</p>
    <div v-if="error" class="mt-3 p-3 rounded-lg panel-danger text-sm text-danger" role="alert">{{ error }}</div>

    <!-- 结果 -->
    <div v-if="result" class="mt-6 space-y-5">
      <!-- 总览 + 自检结论 -->
      <div class="neu-raised rounded-2xl border border-rule/30 p-5">
        <div class="flex flex-wrap items-center gap-2 mb-2">
          <span class="text-sm font-semibold text-ink">{{ result.project?.title }}</span>
          <span
            class="text-xs px-2.5 py-0.5 rounded-full border neu-sunken"
            :class="blockers.length ? 'badge-danger' : 'badge-success'"
          >
            {{ blockers.length ? t('scVerdictRevise') : t('scVerdictOk') }}
          </span>
          <span class="text-xs text-muted">
            {{ t('scIssueCount').replace('{b}', String(blockers.length)).replace('{w}', String(warnings.length)) }}
          </span>
        </div>
        <p class="text-xs text-muted mb-1">{{ result.project?.logline }}</p>
        <p class="text-xs text-muted">
          {{ t('scMeta')
            .replace('{d}', String(result.project?.total_duration_s))
            .replace('{bpm}', String(result.project?.bpm))
            .replace('{n}', String(shots.length)) }}
        </p>

        <!-- 自检问题清单（SCN-*） -->
        <ul v-if="result.project?.review?.length" class="mt-3.5 space-y-1.5 neu-sunken rounded-xl p-3" role="list">
          <li
            v-for="issue in [...blockers, ...warnings]"
            :key="issue.rule_id + issue.location"
            class="text-xs leading-relaxed"
            :class="issue.severity === 'blocker' ? 'text-danger' : 'text-warning'"
          >
            <span class="font-mono font-medium">{{ issue.rule_id }}</span>
            · {{ issue.location }}: {{ issue.detail }}
            <span class="text-muted">→ {{ issue.fix_hint }}</span>
          </li>
        </ul>
      </div>

      <!-- 角色卡 -->
      <div v-if="character" class="neu-raised rounded-2xl border border-rule/30 p-5">
        <h3 class="text-sm font-semibold text-ink mb-2.5 inline-flex items-center gap-1.5">
          <svg class="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
          {{ t('scCharacterBible') }}
        </h3>
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
          <div><dt class="text-muted inline">{{ t('scCharName') }}: </dt><dd class="text-ink-2 font-medium inline">{{ character.name }} ({{ character.role }}, ~{{ character.age }})</dd></div>
          <div><dt class="text-muted inline">{{ t('scCharWardrobe') }}: </dt><dd class="text-ink-2 inline">{{ character.wardrobe }}</dd></div>
          <div class="sm:col-span-2"><dt class="text-muted inline">{{ t('scCharAppearance') }}: </dt><dd class="text-ink-2 inline">{{ character.appearance }}</dd></div>
        </dl>
        <p v-if="character.anchor_token" class="mt-2 text-xs text-muted italic">{{ character.anchor_token }}</p>

        <!-- 连续性锁 -->
        <div v-if="character.continuity_locks?.length" class="mt-3">
          <span class="text-xs text-muted inline-flex items-center gap-1">
            <svg class="w-3.5 h-3.5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
            {{ t('scLocks') }}:
          </span>
          <div class="flex flex-wrap gap-1.5 mt-1.5">
            <span
              v-for="lock in character.continuity_locks"
              :key="lock.key + lock.phrase"
              class="text-[11px] px-2.5 py-0.5 rounded-full neu-sunken text-ink-2 font-mono"
            >
              {{ lock.key }}: {{ lock.phrase }}
            </span>
          </div>
        </div>
        <div v-if="character.turnaround_prompts && Object.keys(character.turnaround_prompts).length" class="mt-2 text-xs text-muted">
          {{ t('scTurnaround') }}: {{ Object.keys(character.turnaround_prompts).length }}/5
        </div>
      </div>

      <!-- 分镜板 -->
      <div>
        <h3 class="text-sm font-semibold text-ink mb-2.5 inline-flex items-center gap-1.5">
          <svg class="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
          {{ t('scStoryboard') }}
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          <article
            v-for="shot in shots"
            :key="shot.scene_number"
            class="neu-raised rounded-2xl p-4 transition-all hover:translate-y-[-1px] border border-rule/20"
          >
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm font-bold text-accent">#{{ String(shot.scene_number).padStart(2, '0') }}</span>
              <span class="text-[10px] text-muted font-mono px-2 py-0.5 rounded-full neu-sunken">{{ timecode(shot) }}</span>
            </div>
            <p class="text-[11px] text-muted mb-1 font-medium">{{ shot.beat_type }} · {{ shot.shot_size }} · {{ shot.camera_movement }}</p>
            <p class="text-xs text-ink-2 leading-relaxed mb-1.5">{{ shot.action_description }}</p>
            <p class="text-[11px] text-muted mb-1 inline-flex items-center gap-1">
              <svg class="w-3.5 h-3.5 text-accent shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
              {{ shot.lighting_and_color }}
            </p>
            <div class="flex flex-wrap gap-1 mt-1">
              <span v-if="shot.emotion" class="badge-info text-[10px] px-2 py-0.5 rounded-full neu-sunken">{{ shot.emotion }}</span>
              <span v-if="shot.transition" class="badge-neutral text-[10px] px-2 py-0.5 rounded-full neu-sunken">{{ shot.transition }}</span>
            </div>
            <button
              class="mt-2 text-[11px] text-accent font-medium hover:text-ink transition"
              :aria-expanded="openPrompts === shot.scene_number"
              @click="openPrompts = openPrompts === shot.scene_number ? null : shot.scene_number"
            >
              {{ openPrompts === shot.scene_number ? t('scHidePrompt') : t('scShowPrompt') }}
            </button>
            <pre
              v-if="openPrompts === shot.scene_number"
              class="mt-1.5 text-[10px] text-muted whitespace-pre-wrap break-words neu-sunken rounded-xl p-2.5 max-h-48 overflow-auto border border-rule/30"
            >{{ shot.video_prompt }}</pre>
          </article>
        </div>
      </div>

      <!-- 导出 / 采用 -->
      <div class="flex flex-wrap items-center gap-3">
        <button class="inline-flex items-center gap-1.5 text-xs px-4 py-2.5 rounded-xl neu-raised hover:neu-sunken text-accent font-semibold transition glow-btn" @click="applyToCreativeForm">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>
          {{ t('scApplyToForm') || 'In Kreativ-Formular übernehmen' }}
        </button>
        <button class="inline-flex items-center gap-1.5 text-xs px-4 py-2.5 rounded-xl neu-raised hover:neu-sunken text-ink-2 font-medium transition" @click="downloadMarkdown">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
          {{ t('scDownload') }}
        </button>
        <button class="inline-flex items-center gap-1.5 text-xs px-4 py-2.5 rounded-xl neu-raised hover:neu-sunken text-ink-2 font-medium transition" @click="copyMarkdown">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"/></svg>
          {{ t('scCopy') }}
        </button>
      </div>
    </div>
  </section>
</template>
