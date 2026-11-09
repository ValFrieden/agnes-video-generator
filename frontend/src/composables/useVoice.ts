import { ref, reactive, computed, watch } from 'vue'
import { appState } from '@/store'
import * as api from '@/api'
import { t, currentLang } from '@/i18n'
import { useToast } from './useToast'
import { useConfirm } from './useConfirm'
import type { Voice } from '@/types'

const { showToast } = useToast()
const { confirmAsync } = useConfirm()

export const DEFAULT_VOICES_BY_LANG: Record<string, string> = {
  zh: 'zh-CN-XiaoxiaoNeural',
  en: 'en-US-JennyNeural',
  de: 'de-DE-KatjaNeural',
  ru: 'ru-RU-SvetlanaNeural',
  fr: 'fr-FR-DeniseNeural',
  es: 'es-ES-ElviraNeural',
  it: 'it-IT-ElsaNeural',
  ja: 'ja-JP-NanamiNeural',
  ko: 'ko-KR-SunHiNeural',
  pt: 'pt-BR-FranciscaNeural',
  nl: 'nl-NL-ColetteNeural',
  id: 'id-ID-GadisNeural',
  ms: 'ms-MY-YasminNeural',
  ar: 'ar-SA-ZariyahNeural',
  tr: 'tr-TR-EmelNeural',
  vi: 'vi-VN-HoaiMyNeural',
  th: 'th-TH-PremwadeeNeural',
  tl: 'fil-PH-BlessicaNeural',
  hi: 'hi-IN-SwaraNeural',
  fa: 'fa-IR-DilaraNeural',
  bn: 'bn-IN-TanishaaNeural',
  ur: 'ur-PK-UzmaNeural',
}

export function getDefaultVoiceForLang(langCode: string): string {
  const catalog = appState.voiceCatalog
  if (catalog && Array.isArray(catalog.languages)) {
    const grp = catalog.languages.find((g: any) => g.code === langCode)
    if (grp && Array.isArray(grp.voices) && grp.voices.length > 0) {
      return grp.voices[0].id
    }
  }
  return DEFAULT_VOICES_BY_LANG[langCode] || 'zh-CN-XiaoxiaoNeural'
}

// 任务的音色选择（c/m/a/p/s），按当前界面语言动态初始化
const initialVoice = getDefaultVoiceForLang(currentLang.value)
export const voiceSelections = reactive<Record<string, string>>({
  c: initialVoice,
  m: initialVoice,
  a: initialVoice,
  p: initialVoice,
  s: initialVoice,
})

// 用户是否显式手动挑选了音色（手动挑选后切语言不覆盖；未挑选时跟随语言变化）
const userCustomizedVoices = reactive<Record<string, boolean>>({
  c: false,
  m: false,
  a: false,
  p: false,
  s: false,
})

// 监听语言切换：未手动自定义的音色自动随语言更新，防止 cross-script 422 报错
watch(currentLang, (newLang) => {
  const def = getDefaultVoiceForLang(newLang)
  ;(['c', 'm', 'a', 'p', 's'] as const).forEach((k) => {
    if (!userCustomizedVoices[k]) {
      voiceSelections[k] = def
    }
  })
})

// picker 弹窗状态
const pickerVisible = ref(false)
const pickerTask = ref<string | null>(null)
const activeLang = ref('zh')
const query = ref('')
const selectedId = ref<string | null>(null)

let vpAudio: HTMLAudioElement | null = null
let vpAudioUrl: string | null = null
const playingId = ref<string | null>(null)

const voiceIndex = computed(() => appState.voiceIndex)

async function initVoiceSelector() {
  try {
    const catalog = await api.getVoices()
    appState.voiceCatalog = catalog
    catalog.languages.forEach((g: any) =>
      g.voices.forEach((v: Voice) => {
        appState.voiceIndex[v.id] = v
      }),
    )
  } catch (e) {
    console.error('load voices failed:', e)
    appState.voiceCatalog = { languages: [], compat_hint: {} }
  }
}

function voiceDesc(v: Voice): string {
  if (!v) return ''
  return `${v.region} · ${v.gender === 'female' ? t('voiceGenderFemale') : t('voiceGenderMale')}`
}

function voiceName(task: string): string {
  const id = voiceSelections[task]
  const v = voiceIndex.value[id]
  if (v) return v.name
  return id ? id.split('-').pop()!.replace('Neural', '') : ''
}

function voiceDescription(task: string): string {
  const id = voiceSelections[task]
  const v = voiceIndex.value[id]
  return v ? voiceDesc(v) : ''
}

function openVoicePicker(task: string) {
  pickerTask.value = task
  activeLang.value = currentLang.value
  query.value = ''
  selectedId.value = voiceSelections[task] || null
  pickerVisible.value = true
  document.body.style.overflow = 'hidden'
}

function closeVoicePicker() {
  stopVoicePreview()
  pickerVisible.value = false
  document.body.style.overflow = ''
}

const activeGroup = computed(() => {
  const catalog = appState.voiceCatalog
  if (!catalog) return null
  return catalog.languages.find((g) => g.code === activeLang.value) || null
})

const filteredVoices = computed(() => {
  const group = activeGroup.value
  if (!group) return []
  const q = query.value.trim().toLowerCase()
  let voices = group.voices || []
  if (q) {
    voices = voices.filter((v) => {
      const hay = [v.name, v.local_name, v.region, (v.style_tags || []).join(' '), v.region_code, v.id]
        .join(' ')
        .toLowerCase()
      return hay.includes(q)
    })
  }
  return voices
})

function selectVoice(id: string) {
  selectedId.value = id
}

function updateCurrentSelection() {
  // 由组件读取 selectedId
}

function onVoiceSearch(value: string) {
  query.value = value
}

async function previewVoice(id: string) {
  if (playingId.value === id) {
    stopVoicePreview()
    return
  }
  stopVoicePreview()
  const v = voiceIndex.value[id]
  const text = v ? v.preview_text : ''
  const url = `/api/voices/preview?voice=${encodeURIComponent(id)}&text=${encodeURIComponent(text)}`
  playingId.value = id
  try {
    const r = await fetch(url)
    if (!r.ok) throw new Error('preview failed')
    const blob = await r.blob()
    vpAudioUrl = URL.createObjectURL(blob)
    vpAudio = new Audio(vpAudioUrl)
    vpAudio.onended = () => {
      playingId.value = null
      vpAudio = null
      if (vpAudioUrl) {
        URL.revokeObjectURL(vpAudioUrl)
        vpAudioUrl = null
      }
    }
    await vpAudio.play()
  } catch (err) {
    console.error('voice preview error:', err)
    playingId.value = null
    if (vpAudioUrl) {
      URL.revokeObjectURL(vpAudioUrl)
      vpAudioUrl = null
    }
    showToast(t('previewFailed'), 3000)
  }
}

function stopVoicePreview() {
  if (vpAudio) {
    vpAudio.pause()
    vpAudio = null
  }
  if (vpAudioUrl) {
    URL.revokeObjectURL(vpAudioUrl)
    vpAudioUrl = null
  }
  playingId.value = null
}

async function confirmVoiceSelection() {
  if (!pickerTask.value || !selectedId.value) {
    closeVoicePicker()
    return
  }
  const v = voiceIndex.value[selectedId.value]
  const voiceLang = v ? v.lang : selectedId.value.split('-')[0].toLowerCase()
  const compat = (appState.voiceCatalog && appState.voiceCatalog.compat_hint) || {}
  const supported = compat[voiceLang] || []
  if (voiceLang !== currentLang.value && !supported.includes(currentLang.value)) {
    const ok = await confirmAsync(t('voiceCompatWarning'))
    if (!ok) return
  }
  voiceSelections[pickerTask.value] = selectedId.value
  userCustomizedVoices[pickerTask.value] = true
  closeVoicePicker()
}

export function useVoice() {
  return {
    voiceSelections,
    pickerVisible,
    pickerTask,
    activeLang,
    query,
    selectedId,
    playingId,
    voiceIndex,
    activeGroup,
    filteredVoices,
    getDefaultVoiceForLang,
    voiceName,
    voiceDescription,
    initVoiceSelector,
    openVoicePicker,
    closeVoicePicker,
    selectVoice,
    onVoiceSearch,
    previewVoice,
    stopVoicePreview,
    confirmVoiceSelection,
  }
}
