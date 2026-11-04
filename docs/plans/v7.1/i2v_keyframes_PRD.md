# PRD — I2V-first 关键帧模式（稿件 / 诗词流水线）

> 状态：🟢 已实施（v7.1 特性线第一项）
> 背景：项目审计 + 用户诉求——现代视频流水线的 Image-to-Video 模式：先固定参考帧
> （人物 / 物体 / 风格不随场景漂移），再送去动画。creative 已有 keyframes 链、
> anchor 本质是 i2v；本 PRD 把该模式带给 manuscript / poetry 两种纯 T2V 流水线。

## 一、问题

稿件 / 诗词流水线逐段直接 t2v 提交（`manuscript_video.py` / `multi_scene._generate_videos`），
同一人物 / 风格在不同段落间随机漂移，用户只能反复重跑整段，浪费视频配额
（视频提交 1×Key/分钟，且队列饱和 503 是上游最主要痛点）。

## 二、方案（免费 Agnes 栈内实现）

每段先经 `agnes-image-2.5-flash` 生成**关键帧**（首帧静图），再把关键帧作为
唯一参考提交视频（1 参考图 → v2.0 `ti2vid` / 2.5 `reference`，见
`core/api/agnes_video.py` submit_video 的 n_refs 分支，无需改 API 层）。

**链式一致性**：场景 i 的关键帧默认以场景 i-1 的关键帧做 i2i 参考（视觉链，
对齐 creative 尾帧链做法）；首场景无参考走 t2i。稿件已有逐段用户参考图时，
该段关键帧的 i2i 参考优先用用户图（用户显式输入 > 链）。

**收益**：
- 画面一致性：漂移在「帧」上就被锁住；
- 配额经济：坏帧在图片桶（20×Key×0.8/分钟）暴露，不必烧视频桶；
- 手动模式：关键帧是独立检查点，可在动画前审查 / AI 修改 / 重生成。

## 三、用户可见行为

- 稿件 / 诗词表单新增开关「先生成关键帧（推荐）」，默认**关**（不改变既有
  行为与回归基线；验证后再考虑翻默认）。
- 开启后进度时间线出现「关键帧」步骤（场景拆分之后、视频生成之前）；
  关闭时不出现（前端按 `state.generate_keyframes` 过滤）。
- 手动模式暂停点新增 `keyframes`（默认暂停点包含之）；关键帧产物
  （`para_{i}/keyframe.png` / `scene_{i}/keyframe.png`）出现在产物区，
  可走 AI 修改 / 在线查看 / 重生成通道。
- 修改某段关键帧 → 级联重置该段视频与成片（dependency graph 新增
  `keyframe:{i}` 边）。

## 四、技术要点

| 触点 | 内容 |
|------|------|
| `models/task.py` | `SceneTask.keyframe_file`、`ManuscriptParagraph.keyframe_file`；两任务态新增 `generate_keyframes: bool = False` + `step_keyframes: StepStatus` |
| `core/pipelines/__init__.py` | `CHECKPOINT_KEYFRAMES = "keyframes"`，挂入 `ALL_CHECKPOINTS` / `_STEP_TO_CHECKPOINT` / `_PAUSE_PROGRESS_BY_STEP` |
| `core/pipelines/multi_scene.py` | 模板 run() 在参考图后插入条件步骤 `step_keyframes`；通用实现 `_generate_scene_keyframes()`（逐场景、断点续传、链式 i2i）+ 钩子（prompt / refs / 目录 / 持久化）；`_get_scene_ref_images` 在开启时优先返回关键帧 |
| `core/pipelines/manuscript_video.py` | 实例化 `AgnesImageAPI`（构造参数 `image_model` 原本就传入但未用）；覆写：用户逐段参考图优先做 i2i 参考、关键帧落 `para_{i}/`、同步 `paragraphs[].keyframe_file`、`_generate_videos` 提交时用关键帧 |
| `core/pipelines/poetry_video.py` | 构造新增 `image_model` 并实例化 `AgnesImageAPI`（`web/deps.py` 同步传参） |
| `core/artifacts.py` | 两类型产物定义 + 步骤序列插入 keyframe 条目；`_SCHEMA_HINTS["keyframe"]` |
| `core/dependency_graph.py` | `T_KEYFRAME`、`scene_prompts/script → keyframe`、`keyframe:{i} → video/final`；粗粒度检查点表与边 |
| `core/i18n_backend.py` | `progress.multi_scene.keyframes_running/_done/keyframe_scene`（zh/en） |
| `web/routes/task_creation_routes.py` | 稿件 / 诗词端点新增 `generate_keyframes: bool = Form(False)` |
| 前端 | `steps.ts`（STEPS + STEP_FIELD_MAP + `requires` 过滤）、`types.ts StepDef.requires`、`useProgress.resetSteps(state)`、`useArtifacts.stepLabelMap`、`CreatePanel` 暂停点、两表单开关、zh/en(/ru) 文案 |

## 五、不做（本期）

- creative 流水线不改（已有 keyframes 链模式）。
- 关键帧 prompt 不做独立 LLM 改写（直接复用场景 prompt，其中已含风格）。
- 不翻默认值、不动上游重试策略。

## 六、测试与回归

- 单测：`tests/test_keyframes_stage.py`——链式参考序列、断点续传跳过已存在、
  开启后视频提交引用关键帧。
- mock 回归 conftest 补 patch 路径（manuscript/poetry 的 `AgnesImageAPI`）。
- 大版本回归新增场景（后续补跑）：M5 = 短稿件 + 关键帧开；P2 = 诗词 + 关键帧开。

## 七、v7.1.1 增量：静态/运动双提示词（manuscript）

来源：外部方案分析（I2V 最佳实践）——静图提示词含运动动词会导致构图漂移，
动画提示词只含静态描述则画面呆板；I2V 需要两份侧重不同的提示词。

- `core/screenwriter/scenes.py` 新增 `generate_scene_prompts_for_paragraph_keyframes()`：
  JSON 模式返回 `{"image_prompt"（静态构图，禁动作动词）, "motion_prompt"（摄像机+
  主体运动，克制定向）}`；非 dict / 缺字段防御归一为空串。
- `ManuscriptParagraph` / `SceneTask` 新增 `motion_prompt` 字段（空串 =
  未生成/旧任务，提交时回退 `scene_prompt`，完全向后兼容）。
- 提交侧：manuscript `_generate_videos` 与 multi_scene 默认钩子
  `_get_scene_video_prompt` 在关键帧模式开启时优先 `motion_prompt`；
  关键帧生成继续用 `scene_prompt`（静态）。
- prompts.json 的 `scene_prompts` 条目携带 `motion_prompt`，产物修改级联
  （`para_fields_all`）覆盖该字段。
- poetry 不改：其「原诗句 | 画面描述」行格式与用户可复制提示词工具共用同一
  契约（`_poetry_scene_prompts` 被 UI 端点复用），且 15-30 字短描述本身偏静态。
