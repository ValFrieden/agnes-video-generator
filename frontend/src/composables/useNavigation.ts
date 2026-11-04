import { appState } from '@/store'

// 顶层视图导航 + URL hash 同步（无 vue-router，零后端改动）
// hash 规则：'#/progress/<taskId>' | '#/list' | '#/gallery' | '#/simple' | '#/create'

export function useNavigation() {
  // 打开任务详情页：始终在新标签页打开，原页面（主页）保持不变
  function goProgress(taskId: string, origin: 'create' | 'list' | 'gallery' | 'simple' = 'create') {
    // 来源标记不跨标签页传递（新标签页内默认回主页），仅在当前页记录
    appState.progressOrigin = origin
    const url = location.pathname + location.search + '#/progress/' + encodeURIComponent(taskId)
    window.open(url, '_blank', 'noopener')
  }

  // 同页打开任务详情（自动恢复场景用，避免自动重连时无限开新标签页）
  function goProgressInPage(taskId: string) {
    appState.view = 'progress'
    appState.progressTaskId = taskId
    appState.currentTaskId = taskId
    location.hash = '#/progress/' + encodeURIComponent(taskId)
  }

  // 显式跳转主页（去掉 hash 回到根视图）
  function goHome() {
    location.href = location.pathname + location.search
  }

  function goBack() {
    let origin: 'create' | 'list' | 'gallery' | 'simple' = 'create'
    if (appState.progressOrigin === 'list') origin = 'list'
    else if (appState.progressOrigin === 'simple') origin = 'simple'
    else if (appState.progressOrigin === 'gallery') origin = 'gallery'
    appState.view = origin
    appState.progressTaskId = null
    location.hash = '#/' + origin
  }

  function parseHash(): { view: 'create' | 'list' | 'simple' | 'gallery' | 'knowledge' | 'progress'; taskId?: string } {
    const h = location.hash || ''
    const m = h.match(/^#\/progress\/(.+)$/)
    if (m) return { view: 'progress', taskId: decodeURIComponent(m[1]) }
    if (h.startsWith('#/list')) return { view: 'list' }
    // Logikcheck Befund 8: '#/simple' wird vom Ein-Klick-Reiter geschrieben,
    // aber beim Reload nicht erkannt → Fall zurück auf „Erstellen"
    if (h.startsWith('#/simple')) return { view: 'simple' }
    if (h.startsWith('#/gallery')) return { view: 'gallery' }
    if (h.startsWith('#/knowledge')) return { view: 'knowledge' }
    return { view: 'create' }
  }

  return { goProgress, goProgressInPage, goHome, goBack, parseHash }
}
