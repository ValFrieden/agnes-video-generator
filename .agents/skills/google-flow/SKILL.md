---
name: google-flow
description: >-
  Automates video and image generation with Google Flow (flow.google.com) and Google Veo / Imagen
  using Google AI Pro subscription credits via browser automation (MCP). Use whenever the user
  wants to generate videos, clips, scenes, storyboards, or images with Google Flow, Veo, or their
  Google AI Pro plan.
---

# Google Flow & Veo Automation Skill

This skill guides the agent in generating high-quality AI videos and images using **Google Flow** (`flow.google.com`) and **Google Veo 3.1** via the local Browser-MCP server. It leverages the user's **Google AI Pro** subscription (1,000 monthly credits + 50 daily credits) without third-party API costs.

---

## 1. Pre-Flight Check (Chrome CDP Port 9222)

Before issuing any Flow generation commands, verify that Chrome is running with Remote Debugging enabled on port 9222:

```powershell
powershell -NoProfile -Command "Invoke-RestMethod -Uri 'http://127.0.0.1:9222/json/version' -TimeoutSec 2"
```

* **If active:** Output contains `"Browser": "Chrome/..."`. You are ready to proceed.
* **If not active:** Inform the user or launch the launcher script:
  `d:\Projects\VideoGenerator\tools\google-flow-browser-mcp\start-chrome-flow.bat`

---

## 2. MCP Tools Overview

The `google-flow` MCP server provides the following tools:

| Tool | Purpose | Key Parameters |
| :--- | :--- | :--- |
| `flow_connect` | Connects Playwright to the active Chrome session and opens Flow. | `open_flow`: true |
| `flow_status` | Returns browser connection state and queue info. | `full`: true/false |
| `flow_generate_video` | Generates video via the Flow agent with cost guard, downloads the new clip in 720p. | `prompt`, `model`, `ratio`, `duration`, `auto_confirm`, `max_credits`, `start_frame`, `end_frame`, `chain_from_video`, `reference_images`, `output_folder` |
| `flow_credit_balance` | Reads credit balance and the project setting „Vor dem Generieren bestätigen“. Read-only. | None |
| `flow_generate_image` | Generates images using Imagen 4 or Nano Banana. | `prompt`, `model`, `ratio`, `auto_confirm`, `output_folder` |
| `flow_download_latest`| Fallback download trigger if media is ready in the DOM. | None |
| `flow_screenshot` | Takes a diagnostic screenshot of the current Flow UI. | `name` |

---

## 3. Video Generation Workflow (Veo)

### A. Calling via MCP Tools (in Chat)

To generate a video clip:
1. Ensure `flow_connect` has been called at least once in the session.
2. Call `flow_generate_video` with:
   * **`prompt`**: Detailed, cinematic visual description (see Prompt Guide below).
   * **`model`**:
     * `"Veo 3.1 - Fast"` (Default, fast generation, low credit usage)
     * `"Veo 3.1 - Quality"` (Maximum quality and fidelity)
     * `"Veo 3.1 - Lite"` (Drafts and quick tests)
     * `"Omni Flash"` (Rapid sketches)
   * **`duration`**: `"4s"`, `"6s"`, `"8s"`, or `"10s"` (Default: `"8s"`).
   * **`ratio`**: `"16:9"` (horizontal) or `"9:16"` (portrait/shorts).
   * **`auto_confirm`**: Default `false` → the agent is asked for the price, the request is declined, result `ready_for_confirmation` with `estimated_credits`. Show the price to the user; only after their OK call again with `true`.
   * **`max_credits`**: Upper limit per clip (default 20 from `maxCreditsPerVideo`). Above it, or above the balance → `cost_blocked`.
   * **Continuity:** same location → `chain_from_video` (last frame of the previous clip becomes the start frame, optional `end_frame` = next keyframe); new location → `reference_images` (character sheet). Frames and `reference_images` cannot be combined.
   * **`output_folder`**: Target destination path for the resulting `.mp4`.

   **Cost guard rules (verified 2026-10-23):**
   * The project setting „Vor dem Generieren bestätigen“ (prompt `Settings` panel) must be **Immer**. On **Nie** the tool refuses with `CONFIRM_POLICY_OFF`. Change it only after asking the user.
   * **MANDATORY APPROVAL CLICK**: Whenever a prompt is sent, Google Flow displays a confirmation card: *„Soll ich diese 1 Videogenerierung starten? Das kostet 100 Guthabenpunkte“*. **You MUST immediately click the single-generation „Genehmigen“ button**! If left unclicked, Flow times out after 2-3 minutes with *„The generation timed out while waiting for confirmation...“* and no video is generated.
   * Never click „Immer genehmigen“ on the agent cost card. It switches the project to „Nie“ (auto-spend). The tool only ever clicks the one-time „Genehmigen“.
   * Price unreadable → `cost_unreadable`, nothing is approved (fail-closed).

### B. Calling via Unified CLI & Engine (`core.flow_pipeline` / `GoogleFlowEngine` - Recommended)

Die native Python-Engine (`core.api.google_flow_engine.GoogleFlowEngine`) nutzt Playwright über CDP ohne Ad-hoc-Zwischenskripte:
* **Automatischer Chrome-Start**: Ist Port 9222 nicht aktiv, startet die Engine Chrome automatisch im Hintergrund (`start-chrome-flow.bat`).
* **Mehrsprachige Genehmigung**: Erkennt Bestätigungskarten auf Deutsch („Genehmigen“), Russisch („Сгенерировать“ / „Подтвердить“) und Englisch („Approve“).
* **Anti-Chimären-Schutz**: Striktes Hochladen per FileChooser nach genauem lokalem Pfad; blindes Auswählen per DOM-Index (`items[0]`) ist verboten.
* **Auto-QC-Trio**: Nach jedem Download generiert FFmpeg automatisch den 25%/50%/75% Kontaktbogen.

CLI-Aufruf (Standardweg für Agenten):
```bash
.venv\Scripts\python.exe -m core.flow_pipeline video \
  --shot S04 \
  --frame path/to/scene_04_keyframe.png \
  --motion "Slow tracking shot from behind, authentic physics, wind in leaves" \
  --out path/to/clips/clip_04.mp4 \
  --model "Veo 3.1 - Fast"
```

Python-Direktaufruf:
```python
from core.api.google_flow_engine import GoogleFlowEngine

engine = GoogleFlowEngine(cdp_url="http://127.0.0.1:9222")
await engine.connect()

success = await engine.generate_scene(
    prompt="Slow tracking shot from behind, walking through forest, realistic lighting",
    reference_image_path="kuda_idu_frames/spina_04.png",
    output_clip_path="kuda_idu_frames/clips/clip_04.mp4",
    skip_if_exists=True
)
await engine.close()
```

---

## 3.1 Native Characters & Scenes in Google Flow (0 Credits Identity Locking)

Google Flow bietet eine eingebaute **Characters**- und **Scenes**-Verwaltung. Statt Rohbilder bei jedem Shot neu als Chips anzuhängen, wird ein Charakter einmalig im Flow-Projekt registriert und im Prompt per `@Name` gebunden:

### A. Charakterverwaltung via CLI (`core.flow_pipeline`)

1. **Vorhandene Charaktere auflisten:**
   ```bash
   python -m core.flow_pipeline character list
   ```

2. **Neuen Charakter anlegen (0 Credits via Upload):**
   ```bash
   python -m core.flow_pipeline character create --name Valeri --images path/to/turnaround.png path/to/portrait.png --desc "Caucasian man, brown hair, stubble, blue eyes"
   ```
   > ⚠️ **Kostenschutz-Regel**: Lokale Bilder hochzuladen kostet **0 Credits**. Niemals im Flow-UI auf „Generieren“ innerhalb des Charakter-Menüs klicken.

### B. Video-Generierung mit Charakter-Bindung & Szenen-Montage

```bash
python -m core.flow_pipeline video   --shot S04   --frame path/to/start_frame.png   --motion "Slow tracking shot, wind in birch leaves."   --out clips/clip_04.mp4   --character Valeri   --add-to-scene
```
* **`--character Valeri`**: Bindet `@Valeri` nativ über das Auto-Complete-Menü in ProseMirror ein, sodass Veo 3.1 die Gesichtszüge und Proportionen fixiert.
* **`--add-to-scene`**: Fügt den fertig gerenderten Clip automatisch der Flow-Szene hinzu.

---

## 4. Prompt Engineering Guide for Veo

Google Veo responds best to concrete, filmic camera and scene cues:

1. **Camera Motion First**: Specify camera trajectory (e.g. `Slow tracking shot`, `Smooth forward dolly`, `Static camera with dynamic wind motion`, `Low angle tilt up`).
2. **Subject & Action**: Clarify who/what is moving and what remains static (e.g. `Rain ripples on wet asphalt, yellow umbrella catches golden light`).
3. **Lighting & Atmosphere**: Mood and lighting (e.g. `Cinematic moody rainy evening, neon city reflections in puddles, atmospheric haze, 35mm film grain`).
4. **Style Consistency**: For projects like music videos, append the global style block:
   `Maintain consistent art style: Anime/cinematic semi-realistic, vivid colors, smooth motion, high detail.`

---

## 5. Troubleshooting & Diagnostics

* **Port 9222 refused:** Chrome was closed or started without `--remote-debugging-port=9222`. Re-run `start-chrome-flow.bat`.
* **Login expired:** Check the Chrome window and refresh `flow.google.com` to ensure the session is logged in.
* **UI change / Element not found:** Take a screenshot using `flow_screenshot(name="diagnostic")` to inspect the current Flow DOM state.
