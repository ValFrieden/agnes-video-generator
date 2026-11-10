import { ref, reactive, computed } from 'vue'
// i18n: nur Deutsch + Russisch als UI-Sprachen (v7.1).
import de from './langs/de.json'
import ru from './langs/ru.json'

export const LANGS: { code: string; label: string }[] = [
  { code: 'de', label: '🇩🇪 Deutsch' },
  { code: 'ru', label: '🇷🇺 Русский' },
]

const RTL_LANGS = ['ar', 'fa', 'ur']

const langData = reactive<Record<string, Record<string, string>>>({ de, ru })

const currentLang = ref('de')

function initLang(): string {
  try {
    const stored = localStorage.getItem('lang')
    if (stored === 'de' || stored === 'ru') return stored
  } catch {
    /* ignore */
  }
  try {
    const nav = (navigator.language || '').toLowerCase()
    if (nav.startsWith('ru')) return 'ru'
  } catch {
    /* ignore */
  }
  return 'de'
}

export function t(key: string): string {
  const lang = currentLang.value
  const data = langData[lang]
  const val = (data && data[key]) ?? (langData['de'] && langData['de'][key]) ?? (langData['ru'] && langData['ru'][key]) ?? key
  return val
}

export function tf(key: string, params?: Record<string, string | number>): string {
  const template = t(key)
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (m, name: string) => {
    const v = params[name]
    return v === undefined || v === null ? m : String(v)
  })
}

export function applyLanguage(lang: string) {
  const allowed = lang === 'ru' ? 'ru' : 'de'
  currentLang.value = allowed
  try {
    localStorage.setItem('lang', currentLang.value)
  } catch {
    /* ignore */
  }
  document.documentElement.lang = currentLang.value
  document.documentElement.dir = RTL_LANGS.includes(currentLang.value) ? 'rtl' : 'ltr'
}

const langLoaders = import.meta.glob('./langs/*.json')
const loadingLang = ref<string | null>(null)

async function loadLang(lang: string): Promise<void> {
  if (!lang || langData[lang]) return
  const loader = langLoaders[`./langs/${lang}.json`]
  if (!loader) return
  loadingLang.value = lang
  try {
    const mod = (await loader()) as { default: Record<string, string> }
    langData[lang] = mod.default
  } catch (e) {
    /* ignore */
  } finally {
    loadingLang.value = null
  }
}

export function escapeHtml(s: unknown): string {
  if (s === null || s === undefined) return ''
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export function useI18n() {
  const lang = computed(() => currentLang.value)

  function switchLang(l: string) {
    applyLanguage(l)
    void loadLang(l)
  }

  function isDefaultValue(value: string, i18nKey: string): boolean {
    const allDefaults = new Set(Object.values(langData).map((l) => l[i18nKey]).filter(Boolean))
    return allDefaults.has(value) || value === ''
  }

  return { lang, currentLang, t, tf, switchLang, isDefaultValue, applyLanguage, loadingLang, loadLang }
}

currentLang.value = initLang()
void loadLang(currentLang.value)

export { currentLang }