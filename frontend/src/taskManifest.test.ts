import { describe, it, expect } from 'vitest'
import { TASK_MANIFEST, CREATE_TASK_TYPES, buildDraftFromTaskState } from './taskManifest'

describe('taskManifest', () => {
  it('exposes all 6 creatable video types including music_video', () => {
    const keys = CREATE_TASK_TYPES.map((e) => e.key)
    expect(keys).toEqual(['creative', 'simple', 'manuscript', 'anchor', 'poetry', 'music_video'])
  })

  it('keeps pause points consistent for manual-supported types', () => {
    for (const entry of Object.values(TASK_MANIFEST)) {
      if (entry.supportsManual) {
        expect(entry.pausePoints.length).toBeGreaterThan(0)
        const validKeys = new Set(entry.pausePoints.map((p) => p.key))
        for (const def of entry.defaultPausePoints) {
          expect(validKeys.has(def)).toBe(true)
        }
      } else {
        expect(entry.pausePoints).toEqual([])
      }
    }
  })

  it('builds draft payload when cloning a task state', () => {
    const draft = buildDraftFromTaskState({
      task_id: 'abc123',
      task_type: 'creative',
      creative_name: 'Rainy Noir',
      idea: 'Detective walks in neon rain',
      scene_count: 4,
      uniform_duration: false,
      scene_durations: [5, 8, 5, 6],
      video_width: 1280,
      video_height: 720,
      lut_id: 'cinematic_teal_orange',
      draft_mode: true,
    })
    expect(draft).not.toBeNull()
    expect(draft?.draftKey).toBe('creative')
    expect(draft?.createTab).toBe('creative')
    expect(draft?.payload.idea).toBe('Detective walks in neon rain')
    expect(draft?.payload.resolution).toBe('1280x720')
    expect(draft?.payload.lutId).toBe('cinematic_teal_orange')
    expect(draft?.payload.draftMode).toBe(true)
  })
})
