// 与后端 models/task.py 对齐的类型定义（仅前端需要的字段）

export type TaskType = 'simple' | 'creative' | 'manuscript' | 'anchor' | 'poetry' | 'music_video' | 'image'

export interface TaskState {
  task_id: string
  task_type?: TaskType
  status?: string
  dir_name?: string
  current_step?: string
  current_status?: string
  current_progress?: number
  current_message?: string
  // v7.0：结构化消息——后端下发 i18n key + 插值参数，前端用 22 语言文案渲染；
  // 未命中 key（旧后端 / 未覆盖）时回退 current_message。
  current_message_key?: string
  current_message_params?: Record<string, string | number>
  final_video_file?: string
  idea?: string
  prompt?: string
  manuscript_text?: string
  script_text?: string
  poem_text?: string
  scene_count?: number
  paragraph_count?: number
  paragraphs?: unknown[]
  creative_name?: string
  // v6.1：后台是否有活跃 pipeline（服务重启后遗留的 pending/queued 任务为 false）
  active?: boolean
  // GA 埋点：error_collector 内存聚合的上游接口报错（按状态码计数，轮询增量上报）
  upstream_errors?: UpstreamError[]
  [key: string]: any
}

export interface UpstreamError {
  status_code: number
  model_type: string
  api_method: string
  count: number
  first_ts: string
  last_ts: string
}

export interface TaskListItem {
  task_id: string
  task_type?: TaskType
  status?: string
  creative_name?: string
  idea?: string
  prompt?: string
  manuscript_text?: string
  script_text?: string
  poem_text?: string
  scene_count?: number
  paragraph_count?: number
  dir_name?: string
  // v6.0 手动模式
  current_mode?: 'auto' | 'manual'
  current_checkpoint?: string
  awaiting_user?: boolean
  // P2 项目概览：来自 task_state.json；旧任务为空串（按「未知日期」处理）
  created_at?: string
  updated_at?: string
  song_title?: string
  bpm?: number
}

export interface StepDef {
  key: string
  labelKey: string
  /** v7.1：该步骤仅在 state 对应布尔字段为真时显示（如 keyframes → generate_keyframes） */
  requires?: string
}

export interface Voice {
  id: string
  name: string
  local_name?: string
  region?: string
  region_code?: string
  gender?: 'male' | 'female'
  lang?: string
  style_tags?: string[]
  preview_text?: string
}

export interface VoiceGroup {
  code: string
  label: string
  count: number
  voices: Voice[]
}

export interface VoiceCatalog {
  languages: VoiceGroup[]
  compat_hint?: Record<string, string[]>
}

export interface Artifact {
  artifact_id: string
  category: 'text' | 'image' | 'video' | 'audio' | 'json' | 'subtitle'
  label_key: string
  step_key: string
  scope_index?: number | null
  size: number
  exists: boolean
  deletable: boolean
}

export interface Workspace {
  path: string
  name?: string
  is_default?: boolean
}

// ── 风格预设库（P0-1）──
export interface Preset {
  id: string
  category?: string
  prompt: string
  name?: string
  created_at?: string
  kind?: 'system' | 'user'
}

// ── SYNTX 电影级摄像机预设 ──
export interface CameraMovementPreset {
  id: string
  name_ru: string
  name_en: string
  category: 'dramatic' | 'dynamic' | 'perspective' | 'atmospheric'
  category_ru: string
  prompt_modifier: string
  description_ru: string
  description_en: string
  icon: string
}

// ── 产物画廊（P1，纯只读）──
export interface GalleryItem {
  task_id: string
  dir_name: string
  task_type: TaskType
  status: string
  kind: 'video' | 'image'
  description?: string
  title?: string
  media_url?: string
  thumb_url?: string | null
}

export interface LutPreset {
  id: string
  name: string
  description: string
  path?: string
}

export interface WorkspaceAsset {
  id: string
  name: string
  kind: 'character' | 'style' | 'prop'
  prompt: string
  continuity_locks: string
  image_file?: string
  image_url?: string | null
  created_at?: string
}
