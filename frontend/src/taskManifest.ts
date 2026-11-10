import type { StepDef, TaskState, TaskType } from './types'

/**
 * Centralized Task-Type Manifest (P2-10):
 * Single source of truth for labels, creation tabs, pause checkpoints,
 * progress steps, task info fields, and task-cloning draft mapping.
 */
export interface TaskInputFieldDef {
  field: string
  label: string
}

export interface TaskConfigFieldDef {
  field: string
  label: string
  fmt?: (v: any) => string
}

export interface TaskTypeManifestEntry {
  key: TaskType
  labelKey: string
  createLabelKey?: string
  createDescKey?: string
  supportsManual: boolean
  pausePoints: { key: string; labelKey: string }[]
  defaultPausePoints: string[]
  steps: StepDef[]
  stepFieldMap: Record<string, string>
  inputFields: TaskInputFieldDef[]
  configFields: TaskConfigFieldDef[]
  draftKey?: string
}

export const TASK_MANIFEST: Record<TaskType, TaskTypeManifestEntry> = {
  creative: {
    key: 'creative',
    labelKey: 'typeCreative',
    createLabelKey: 'ttCreative',
    createDescKey: 'ttDescCreative',
    supportsManual: true,
    pausePoints: [
      { key: 'image_analysis', labelKey: 'cpImageAnalysis' },
      { key: 'story', labelKey: 'cpStory' },
      { key: 'script', labelKey: 'cpScript' },
      { key: 'character_ref', labelKey: 'cpCharacterRef' },
      { key: 'end_frame_prompts', labelKey: 'cpEndFramePrompts' },
      { key: 'end_frame_gen', labelKey: 'cpEndFrameGen' },
      { key: 'videos', labelKey: 'cpVideos' },
      { key: 'audio', labelKey: 'cpAudio' },
      { key: 'subtitle', labelKey: 'cpSubtitle' },
      { key: 'final', labelKey: 'cpFinal' },
    ],
    defaultPausePoints: ['story', 'script', 'character_ref', 'videos', 'subtitle'],
    steps: [
      { key: 'init', labelKey: 'cStepInit' },
      { key: 'scene_config', labelKey: 'cStepSceneConfig' },
      { key: 'image_analysis', labelKey: 'cStepImageAnalysis' },
      { key: 'story', labelKey: 'cStepStory' },
      { key: 'character_ref', labelKey: 'cStepCharacterRef' },
      { key: 'script', labelKey: 'cStepScript' },
      { key: 'end_frame_prompts', labelKey: 'cStepEndFramePrompts' },
      { key: 'end_frame_gen', labelKey: 'cStepEndFrameGen' },
      { key: 'video_gen', labelKey: 'cStepVideoGen' },
      { key: 'audio', labelKey: 'cStepAudio' },
      { key: 'subtitle', labelKey: 'cStepSubtitle' },
      { key: 'concatenate', labelKey: 'cStepConcat' },
    ],
    stepFieldMap: {
      scene_config: 'step_scene_config',
      image_analysis: 'step_image_analysis',
      story: 'step_story',
      character_ref: 'step_character_ref',
      script: 'step_script',
      end_frame_prompts: 'step_end_frame_prompts',
      end_frame_gen: 'step_end_frame_generation',
      video_gen: 'step_video_generation',
      audio: 'step_audio',
      subtitle: 'step_subtitle',
      concatenate: 'step_concatenation',
    },
    inputFields: [{ field: 'idea', label: 'tiIdea' }],
    configFields: [
      { field: 'video_width', label: 'tiWidth', fmt: (v) => String(v ?? '') },
      { field: 'video_height', label: 'tiHeight', fmt: (v) => String(v ?? '') },
      { field: 'scene_count', label: 'tiScenes', fmt: (v) => String(v ?? '') },
      { field: 'chaining_mode', label: 'tiChaining' },
      { field: 'style', label: 'tiStyle' },
    ],
    draftKey: 'creative',
  },
  simple: {
    key: 'simple',
    labelKey: 'typeSimple',
    createLabelKey: 'ttSimple',
    createDescKey: 'ttDescSimple',
    supportsManual: false,
    pausePoints: [],
    defaultPausePoints: [],
    steps: [
      { key: 'submit', labelKey: 'sStepSubmit' },
      { key: 'video_gen', labelKey: 'sStepVideoGen' },
    ],
    stepFieldMap: {},
    inputFields: [{ field: 'prompt', label: 'tiPrompt' }],
    configFields: [
      { field: 'mode', label: 'tiMode' },
      { field: 'duration', label: 'tiDuration', fmt: (v) => String(v ?? '') },
    ],
    draftKey: 'simple-video',
  },
  manuscript: {
    key: 'manuscript',
    labelKey: 'typeManuscript',
    createLabelKey: 'ttManuscript',
    createDescKey: 'ttDescManuscript',
    supportsManual: true,
    pausePoints: [
      { key: 'scenes', labelKey: 'cpScenes' },
      { key: 'keyframes', labelKey: 'cpKeyframes' },
      { key: 'videos', labelKey: 'cpVideos' },
      { key: 'audio', labelKey: 'cpAudio' },
      { key: 'subtitle', labelKey: 'cpSubtitle' },
      { key: 'final', labelKey: 'cpFinal' },
    ],
    defaultPausePoints: ['scenes', 'keyframes', 'videos', 'subtitle'],
    steps: [
      { key: 'split_text', labelKey: 'mStepSplit' },
      { key: 'scene_prompts', labelKey: 'mStepScenePrompts' },
      { key: 'keyframes', labelKey: 'mStepKeyframes', requires: 'generate_keyframes' },
      { key: 'video_gen', labelKey: 'mStepVideoGen' },
      { key: 'qc', labelKey: 'mStepQc', requires: 'qc_enabled' },
      { key: 'audio', labelKey: 'mStepAudio' },
      { key: 'subtitle', labelKey: 'mStepSubtitle' },
      { key: 'concatenate', labelKey: 'mStepConcat' },
    ],
    stepFieldMap: {
      split_text: 'step_split',
      scene_prompts: 'step_scene_prompts',
      keyframes: 'step_keyframes',
      video_gen: 'step_video_generation',
      qc: 'step_qc',
      audio: 'step_audio',
      subtitle: 'step_subtitle',
      concatenate: 'step_concatenation',
    },
    inputFields: [{ field: 'manuscript_text', label: 'tiManuscript' }],
    configFields: [
      { field: 'scene_count', label: 'tiScenes', fmt: (v) => String(v ?? '') },
      { field: 'paragraph_count', label: 'tiParagraphs', fmt: (v) => String(v ?? '') },
    ],
    draftKey: 'manuscript',
  },
  anchor: {
    key: 'anchor',
    labelKey: 'typeAnchor',
    createLabelKey: 'ttAnchor',
    createDescKey: 'ttDescAnchor',
    supportsManual: true,
    pausePoints: [
      { key: 'scenes', labelKey: 'cpScenes' },
      { key: 'references', labelKey: 'cpReferences' },
      { key: 'videos', labelKey: 'cpVideos' },
      { key: 'audio', labelKey: 'cpAudio' },
      { key: 'subtitle', labelKey: 'cpSubtitle' },
      { key: 'final', labelKey: 'cpFinal' },
    ],
    defaultPausePoints: ['scenes', 'videos'],
    steps: [
      { key: 'generate_anchor', labelKey: 'aStepGenerateAnchor' },
      { key: 'split_text', labelKey: 'aStepSplit' },
      { key: 'clip_prompts', labelKey: 'aStepClipPrompts' },
      { key: 'clip_gen', labelKey: 'aStepClipGen' },
      { key: 'audio', labelKey: 'aStepAudio' },
      { key: 'subtitle', labelKey: 'aStepSubtitle' },
      { key: 'concatenate', labelKey: 'aStepConcat' },
    ],
    stepFieldMap: {
      generate_anchor: 'step_generate_anchor',
      split_text: 'step_split',
      clip_prompts: 'step_clip_prompts',
      clip_gen: 'step_clip_generation',
      audio: 'step_audio',
      subtitle: 'step_subtitle',
      concatenate: 'step_concatenation',
    },
    inputFields: [
      { field: 'script_text', label: 'tiScript' },
      { field: 'anchor_prompt', label: 'tiAnchorPrompt' },
    ],
    configFields: [
      { field: 'audio_source', label: 'tiAudioSource' },
      { field: 'video_width', label: 'tiWidth', fmt: (v) => String(v ?? '') },
      { field: 'video_height', label: 'tiHeight', fmt: (v) => String(v ?? '') },
    ],
    draftKey: 'anchor',
  },
  poetry: {
    key: 'poetry',
    labelKey: 'typePoetry',
    createLabelKey: 'ttPoetry',
    createDescKey: 'ttDescPoetry',
    supportsManual: true,
    pausePoints: [
      { key: 'scenes', labelKey: 'cpScenes' },
      { key: 'keyframes', labelKey: 'cpKeyframes' },
      { key: 'videos', labelKey: 'cpVideos' },
      { key: 'audio', labelKey: 'cpAudio' },
      { key: 'subtitle', labelKey: 'cpSubtitle' },
      { key: 'final', labelKey: 'cpFinal' },
    ],
    defaultPausePoints: ['scenes', 'keyframes', 'videos', 'subtitle'],
    steps: [
      { key: 'build_scenes', labelKey: 'pStepBuildScenes' },
      { key: 'keyframes', labelKey: 'pStepKeyframes', requires: 'generate_keyframes' },
      { key: 'video_generation', labelKey: 'pStepVideoGen' },
      { key: 'qc', labelKey: 'pStepQc', requires: 'qc_enabled' },
      { key: 'audio', labelKey: 'pStepAudio' },
      { key: 'subtitle', labelKey: 'pStepSubtitle' },
      { key: 'concatenation', labelKey: 'pStepConcat' },
    ],
    stepFieldMap: {
      build_scenes: 'step_build_scenes',
      keyframes: 'step_keyframes',
      video_generation: 'step_video_generation',
      qc: 'step_qc',
      audio: 'step_audio',
      subtitle: 'step_subtitle',
      concatenation: 'step_concatenation',
    },
    inputFields: [{ field: 'poem_text', label: 'tiPoem' }],
    configFields: [
      { field: 'video_width', label: 'tiWidth', fmt: (v) => String(v ?? '') },
      { field: 'video_height', label: 'tiHeight', fmt: (v) => String(v ?? '') },
      { field: 'scene_count', label: 'tiScenes', fmt: (v) => String(v ?? '') },
      { field: 'style', label: 'tiStyle' },
    ],
    draftKey: 'poetry',
  },
  music_video: {
    key: 'music_video',
    labelKey: 'typeMusicVideo',
    createLabelKey: 'ttMusicVideo',
    createDescKey: 'ttDescMusicVideo',
    supportsManual: true,
    pausePoints: [
      { key: 'scenes', labelKey: 'cpScenes' },
      { key: 'references', labelKey: 'cpReferences' },
      { key: 'videos', labelKey: 'cpVideos' },
      { key: 'final', labelKey: 'cpFinal' },
    ],
    defaultPausePoints: ['scenes', 'videos'],
    steps: [
      { key: 'build_scenes', labelKey: 'mvStepBuildScenes' },
      { key: 'reference_images', labelKey: 'mvStepReference' },
      { key: 'video_generation', labelKey: 'pStepVideoGen' },
      { key: 'concatenation', labelKey: 'pStepConcat' },
    ],
    stepFieldMap: {
      build_scenes: 'step_build_scenes',
      reference_images: 'step_reference_images',
      video_generation: 'step_video_generation',
      concatenation: 'step_concatenation',
    },
    inputFields: [
      { field: 'song_title', label: 'mvSongTitle' },
      { field: 'music_prompt', label: 'mvMusicPrompt' },
    ],
    configFields: [
      { field: 'bpm', label: 'mvBpm', fmt: (v) => String(v ?? '') },
      { field: 'scene_count', label: 'tiScenes', fmt: (v) => String(v ?? '') },
      { field: 'visual_style', label: 'tiStyle' },
    ],
    draftKey: 'music-video',
  },
  image: {
    key: 'image',
    labelKey: 'typeImage',
    supportsManual: false,
    pausePoints: [],
    defaultPausePoints: [],
    steps: [],
    stepFieldMap: {},
    inputFields: [{ field: 'prompt', label: 'tiPrompt' }],
    configFields: [],
    draftKey: 'simple-image',
  },
}

export const CREATE_TASK_TYPES: TaskTypeManifestEntry[] = [
  TASK_MANIFEST.creative,
  TASK_MANIFEST.simple,
  TASK_MANIFEST.manuscript,
  TASK_MANIFEST.anchor,
  TASK_MANIFEST.poetry,
  TASK_MANIFEST.music_video,
]

export const TYPE_LABEL_KEY_MAP: Record<string, string> = Object.fromEntries(
  Object.values(TASK_MANIFEST).map((entry) => [entry.key, entry.labelKey]),
)

export function buildDraftFromTaskState(state: TaskState): { draftKey: string; createTab: string; payload: Record<string, any> } | null {
  const type = (state.task_type || 'creative') as TaskType
  const w = state.video_width || 768
  const h = state.video_height || 1152
  const res = `${w}x${h}`

  if (type === 'creative') {
    return {
      draftKey: 'creative',
      createTab: 'creative',
      payload: {
        name: state.creative_name ? `${state.creative_name} (copy)` : '',
        idea: state.idea || '',
        durationSource: state.duration_source === 'prompt' ? 'prompt' : 'manual',
        sceneCount: state.scene_count || 3,
        uniform: state.uniform_duration ?? true,
        uniformDuration: (state.scene_durations && state.scene_durations[0]) || 5,
        independentDurations: state.scene_durations || [],
        style: state.style || '',
        cameraMovement: state.camera_movement || '',
        draftMode: !!state.draft_mode,
        lutId: state.lut_id || '',
        chaining: state.chaining_mode || 'keyframes',
        resolution: res,
      },
    }
  }
  if (type === 'simple') {
    return {
      draftKey: 'simple-video',
      createTab: 'simple',
      payload: {
        prompt: state.prompt || '',
        mode: state.mode || 't2v',
        duration: String(state.duration || 5),
        resolution: res,
        seed: state.seed != null ? String(state.seed) : '',
        negative: state.negative_prompt || '',
        system: state.system_prompt || '',
        cameraMovement: state.camera_movement || '',
        lutId: state.lut_id || '',
      },
    }
  }
  if (type === 'manuscript') {
    return {
      draftKey: 'manuscript',
      createTab: 'manuscript',
      payload: {
        name: state.creative_name ? `${state.creative_name} (copy)` : '',
        text: state.manuscript_text || '',
        resolution: res,
        keyframes: !!state.generate_keyframes,
        qc: !!state.qc_enabled,
        lutId: state.lut_id || '',
      },
    }
  }
  if (type === 'anchor') {
    return {
      draftKey: 'anchor',
      createTab: 'anchor',
      payload: {
        prompt: state.anchor_prompt || '',
        script: state.script_text || '',
        resolution: res,
        audioSource: state.audio_source || 'post_stitch',
        lutId: state.lut_id || '',
      },
    }
  }
  if (type === 'poetry') {
    return {
      draftKey: 'poetry',
      createTab: 'poetry',
      payload: {
        name: state.creative_name ? `${state.creative_name} (copy)` : '',
        poem: state.poem_text || '',
        sceneCount: state.scene_count || 3,
        uniform: state.uniform_duration ?? true,
        uniformDuration: (state.scene_durations && state.scene_durations[0]) || 5,
        independentDurations: state.scene_durations || [],
        scenePrompts: Array.isArray(state.user_scene_prompts) ? state.user_scene_prompts.join('\n') : '',
        style: state.style || '',
        resolution: res,
        keyframes: !!state.generate_keyframes,
        qc: !!state.qc_enabled,
        lutId: state.lut_id || '',
      },
    }
  }
  if (type === 'music_video') {
    return {
      draftKey: 'music-video',
      createTab: 'music_video',
      payload: {
        songTitle: state.song_title || '',
        visualStyle: state.visual_style || 'Cinematic Music Video',
        bpm: state.bpm || 120,
        sceneCount: state.scene_count || 6,
        resolution: res,
        generateMusic: !!state.generate_music,
        musicPrompt: state.music_prompt || '',
        musicStyle: state.music_style || '',
        instrumental: !!state.instrumental,
        sunoModel: state.suno_model || 'V6',
        lutId: state.lut_id || '',
      },
    }
  }
  return null
}
