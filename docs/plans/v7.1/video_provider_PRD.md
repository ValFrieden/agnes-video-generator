# PRD — 视频 Provider 抽象（v7.1 阶段 2）

> 状态：🟢 已实施
> 背景：五条流水线此前直接实例化 ``AgnesVideoAPI``（无 Provider 接口，chat 侧已有
> ``core/api/chat_providers.py`` 先例）。换视频服务商需逐处改码；用户侧 fal.ai
> 实验（`fal_clip_pipeline.py`）证明了真实需求。目标：agnes 为默认内置 Provider，
> fal.ai 为首个外部 Provider，换服务商 = 换环境变量。

## 一、方案

- **契约**：`core/api/video_providers.py::VideoProviderBase`——与 `AgnesVideoAPI`
  现有公开面同形（`submit_video` / `wait_for_video` / `resolve_image_ref` /
  `shutdown_event`），流水线调用点零改动（`video_api` / `video_generator` 属性
  名不变，creative/anchor、simple/manuscript/poetry 两派均兼容）。
- **能力描述**：`VideoProviderCapabilities`（max_reference_images、负向提示词、
  seed、时长档位、画幅、`default_params` 如 Kling `cfg_scale=0.5`、notes）。
- **工厂**：`create_video_provider(api_key, default_model, shutdown_event)`，
  读 `AGNES_VIDEO_PROVIDER`（`agnes`（默认）| `fal`）。
  **agnes 分支调用时导入** `core.api.agnes_video.AgnesVideoAPI`，保证既有
  `monkeypatch("core.api.agnes_video.AgnesVideoAPI")` mock 回归补丁继续生效；
  各流水线模块同名符号保留（conftest 按路径打点）。
- **FalVideoProvider**：`fal_client.submit` → `request_id` 作为 video_id；
  `status`/`result` 轮询（`asyncio.to_thread` 包同步 SDK）；本地参考图经
  `fal_client.upload_file` 上传 CDN；T2V 端点由 I2V 端点派生；时长吸附
  {5,10}；画幅复用 `width_height_to_aspect_ratio`；`negative_prompt` 透传，
  seed 不支持（记 debug）；`cfg_scale` 默认 0.5（0.4–0.6 运动一致性最优，
  >0.7 易破坏帧几何——外部实测结论）。

## 二、配置

| 环境变量 | 默认 | 说明 |
|---|---|---|
| `AGNES_VIDEO_PROVIDER` | `agnes` | `agnes` / `fal`；未知值工厂抛错（任务失败可见，不静默回退） |
| `FAL_VIDEO_MODEL` | `fal-ai/kling-video/v1.5/pro/image-to-video` | fal endpoint id |
| `FAL_KEY` | — | 由 fal_client 自行读取，不入 config.json（付费密钥） |

`fal-client` 为可选依赖（缺失时工厂/提交给出 `pip install fal-client` 明确提示）。

## 三、已知限制（MVP，后续迭代）

1. fal 任务**跨服务重启续传受限**：`request_id → endpoint` 映射在内存，
   重启后回退 I2V 主端点（T2V 任务的续传等待会寻错端点）。
2. `progress_callback`（agnes 队列满实时推送协议）在 fal Provider 为 no-op。
3. Kling 单参考图：2+ 参考图取第一张（creative 多图 keyframes 协议不适用）。
4. fal 无服务端撤销：停止任务依赖 `shutdown_event` 在轮询间隙抛
   `VideoTaskCancelled`（最长滞后一个轮询间隔）。
5. 模型下拉（/api/models）仍为 agnes 目录；provider=fal 时该下拉不生效。

## 四、测试

- `tests/test_video_providers.py`：工厂默认/未知值、fal submit（T2V/I2V 路径、
  时长吸附、多图截断、cfg_scale 透传）、status 轮询→result→VideoOutput、
  shutdown 取消、resolve_image_ref 透传/上传、流水线经工厂接线
  （manuscript 默认 agnes；env=fal 时拿到 FalVideoProvider）。
  fal_client 以 sys.modules 注入的 stub 覆盖，不触网。
