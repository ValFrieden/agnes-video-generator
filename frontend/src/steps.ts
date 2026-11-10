import { TASK_MANIFEST } from './taskManifest'
import type { StepDef, TaskType } from './types'

export const STEPS: Record<string, StepDef[]> = Object.fromEntries(
  Object.values(TASK_MANIFEST)
    .filter((entry) => entry.steps.length > 0)
    .map((entry) => [entry.key, entry.steps]),
)

export const STEP_FIELD_MAP: Record<string, Record<string, string>> = Object.fromEntries(
  Object.values(TASK_MANIFEST)
    .filter((entry) => Object.keys(entry.stepFieldMap).length > 0)
    .map((entry) => [entry.key, entry.stepFieldMap]),
)

export function getStepsForType(taskType?: TaskType | string, state?: any): StepDef[] {
  const all = STEPS[taskType as string] || STEPS.creative
  // v7.1：按 state 布尔字段过滤条件步骤（如 keyframes 仅 generate_keyframes 时显示）
  return all.filter((s) => !s.requires || !!(state && state[s.requires]))
}

export function isStepDoneInState(state: any, stepKey: string, taskType?: string): boolean {
  const map = STEP_FIELD_MAP[taskType as string] || STEP_FIELD_MAP.creative
  const field = map[stepKey]
  return field ? state[field] === 'completed' : false
}
