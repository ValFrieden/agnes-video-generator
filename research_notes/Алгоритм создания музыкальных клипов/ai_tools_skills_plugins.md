# AI music video: tools, skills, plugins, MCP servers (as of 2026-11-07)

Research-only catalog. Nothing was installed and no generations were run. Stars and dates come from search snippets and may lag by weeks. Every entry carries a source URL. **Status flags:** `[OK]` active and verified by more than one source or an official page; `[?]` single or unverified source; `[LEGACY]` frozen or discontinued; `[TOS]` browser automation that may break the platform's Terms of Service.

Source tags: **(P-R)** Perplexity `perplexity_research`, **(P-A)** `perplexity_ask`, **(P-S)** `perplexity_search`. Every finding below came from Perplexity. WebFetch failed in this session (model error), so no page was opened directly. Verify prices on the official pricing pages before relying on them.

Note: the skill reference `deep-research/references/researcher.md` could not be read (the read was blocked outside the working directory). Standard research practice was used instead.

---

## 0. TL;DR for our stack (Claude Code + Flow/Veo via CDP 9222 + Kling MCP + Suno + Python/ffmpeg)

1. **Our pipeline already matches the 2026 best practice.** Most community skills follow the same rule: "math owns timing, LLM owns story". Demucs, then forced alignment, then a beat grid, then an LLM storyboard, then stills, then I2V, then frame-exact ffmpeg over the untouched master. There is nothing to replace it with; we can borrow parts.
2. **Most useful things to borrow (scripts and ideas, not whole products):**
   - **Dracowyn/ai-music-video-skill** (Claude Code skill). Scripts: `check_timebase.py` (stem-versus-mix offset; stem separators can shift audio by tens of ms), `fit_beat_grid.py`, `align_lyrics.py` with QA plots, `resolve_shots.py` (turns "the beat before line 12" into a timecode), `avsync_check.py` (finds where lip-sync drifts in a generated clip).
   - **scenario-labs/skills → scenario-seedance-music-video**: the formula for landing an action on a beat inside a shot (beat master time − shot `at` + planned head trim `in`), plus `av_sync_check.py`, `lipsync_check.py`, `dance_sync_check.py`.
   - **brahmsyaifullah/lyric-music-video**: Claude skill + Remotion template, `validate_edl.py`, `qa_sheet.sh`, RIFE interpolation, `veo_clip.py`.
   - **yongjip/song2mv**: `sync` / `beats` produce LRC, SRT and word-JSON on the beat grid.
   - **Timing via the Suno timestamped-lyrics endpoint** for Suno tracks (draft), then forced alignment on the vocal stem and correction by ear.
3. **Generation MCPs:** keep the Kling MCP (official, OAuth). For Flow, the closest open-source match to our setup is **RohaanA/google-flow-mcp** (`FLOW_CDP_URL=http://127.0.0.1:9222`, `FLOW_MAX_CREDITS_PER_CALL` cost guard). It is `[TOS]`. The official alternative is **Google GenMedia MCP** (Vertex AI API, billed separately from Flow credits).
4. **Assembly MCPs (optional):** `claudeclip` (contact sheets via `sample_frames`, useful for QA), `davinci-resolve-mcp` (if we hand off to Resolve), Remotion plugin (lyrics and titles).
5. **Reference (all-in-one) generators** for a quick draft or benchmark: Freebeat, Neural Frames, Revid (has an MCP), Vidu One-Click MV, Higgsfield MV Director, Google **Flow Music** (announced 2026-05-19). None gives our level of control over the character sheet and editing.

---

## 1. Dedicated AI music video generators (P-R, plus P-S for cost)

| Tool | Beat sync | Lyrics / lip-sync | Character consistency | Length | Price (USD/mo unless noted) | Status / source |
|---|---|---|---|---|---|---|
| Neural Frames | beat- and stem-reactive, Autopilot | lyrics extraction, captions, singing lip-sync | reusable characters | Autopilot up to 15 min | Knight 39 / Ninja 99 / Nirvana 299 | [OK] neuralframes.com/pricing |
| Kaiber Superstudio | Beat Sync on Creator/Pro only | lyric detection | partial | ~20 s clips | 10 / 29 / 99 | [OK] kaiber.ai/pricing |
| Freebeat | beats, drops, sections ("5-tier quantization") | timed lyrics, lip-sync | Character Bible, up to 2 characters | up to 6 min (Pro+) | Basic 4.99/wk, Pro 26.99, Ultimate 39.99, Creator 199 | [OK] Music Video Agent 2025-08-19, lyric agent 2026-10-28; Suno/Udio link-paste. Its own comparison is marketing: freebeat.ai/articles/i-ran-the-same-song-through-9-ai-music-video-generators... |
| Revid | beat or lyric timing | lyric captions, lip-sync | saved characters | full song | Growth 39 / Elite 89 / Ultra 199 | [OK] **has an MCP**: revid.ai/mcp; API: revid.ai/docs/workflows/music-to-video; 1 min = 180/600/1200 credits (Low/Pro/Ultra): revid.ai/blog/how-much-does-a-music-video-cost |
| Vidu One-Click MV | yes | subtitles, lip-sync | up to 7 reference images | 10–300 s | 10 / 43 / 115+ | [OK] API requires vocals: platform.vidu.com/docs/api-reference/solutions/entertainment/one-click-ai-mv |
| Higgsfield MV Director | beat cut + lip-sync | – | Soul ID | song + 1–4 photos | 19 / 59 / 129 | [OK] mv-director.higgsfield.app |
| Google Flow (+ Flow Music) | Scenebuilder has no beat cutting | – | Ingredients | Veo 8 s, Omni 15 s | AI Plus 4.99, Pro 19.99, Ultra 99.99–199.99 | [OK] Flow Music (song-led MV with Gemini Omni) announced 2026-05-19: blog.google/innovation-and-ai/models-and-research/google-labs/flow-updates/ |
| LTX Studio | no automatic beat cut | – | Elements | 3–20 s shots | 15 / 35 / 125 | [OK] |
| Runway | no | lip-sync | references | Gen-4.5 2–10 s, 720p | 15 / 35 / 95 | [OK] |
| Pika | no | – | Character Studio | up to 30 s | 10 / 35 / 95+ | [OK], old site being sunset |
| DomoAI | no | Talking Avatar sings | yes | 60 s | 13 / 42 / 142 | [OK] |
| Hailuo / MiniMax H3 | no | – | multimodal references | up to 15 s | 10.5 / 38 / 89 / 216 | [OK]; MiniMax music API closed to new users. H3 Max measured at $0.125 per 5 s at 480p: suno.bi/en/blog/lite-agent-cheap-ai-music-video-workflow [?] |
| CapCut | Auto Cut / Beat Sync | Auto Lyrics | – | Seedance 2.5 up to 30 s | web Pro 19.99 | [OK] |
| Rotor Videos | tempo-edits stock footage | yes | no AI generation | up to 10 min | 9.99–19.99 | [OK] |
| Videobolt | visualizer templates | lyric sync | – | up to 2 h | 9.99 / 24.99 / 39.99 | [OK] |
| OpusClip | – | lyric video tool | – | – | 15 / 29 | [OK], an editor |
| Suno Hooks | – | lyrics over **uploaded** footage | – | – | Pro 10, Premier 30 | [OK], does not generate video |
| Udio | – | – | – | – | – | [!] downloads disabled after the UMG deal: help.udio.com/en/articles/12683565 |
| Kling | **no one-step song-to-MV** | separate lip-sync tool | Elements / Omni | 3–15 s (3.0) | Std 6.99 / Pro 25.99 / Premier 64.99 | [OK] kling.ai/feature/ai-music-video-generator, kling.ai/feature/lip-sync |

**New entrants 2025–2026, mostly `[?]`** (one press release or blog each):
- One More Shot AI (2025-05)
- Musicful (2025-12)
- SunoMV / suno.bi, unofficial, not Suno (2026-03)
- BeatMV (2026-03)
- Atlabs Music Video (2026-06)
- Soundverse (prompt-to-MV 2026-10-15)
- YouCam Video AI MV (2026-07)
- OiiOii (2026-08)
- Agent Opus (2026-08)
- 1MV, TubeTube, MusicMV (late October 2026)
- Melodious chat-first director (2026-11-03)
- **Enkio MCP** for ChatGPT/Codex (press release, freep.com, 2026-11-05)
- **SelfyzAI MCP** (press release)

**Likely hallucinated or SEO content, do not trust:** resource.digen.ai/ai-video-generators-full-comparison-2026 cites "Kling BeatSync", "MiniMax MelodyVision $47 unlimited" and "Veo Engagement Pricing $0.003/view". No official source confirms these, and Kling officially has no song-to-MV feature.

**Kling 4.0 (up to 30 s, first and last frame):** appears only on a Russian reseller page (vc.ru/ai/3231511, 2026-11-02). `[?]` Not confirmed on kling.ai.

---

## 2. Claude Code / Agent Skills for music videos (P-S)

| Skill | What it does | Install | Date | Rating |
|---|---|---|---|---|
| **Dracowyn/ai-music-video-skill** | Claude acts as the full MV team: timing, storyboard, prompts, lip-sync checks, karaoke, render. Scripts: `make_approx.py`, `check_timebase.py`, `fit_beat_grid.py` (constant grid or tempo curve → `audio.json`), `align_lyrics.py` (word/syllable alignment + QA plots), `resolve_shots.py`, `avsync_check.py` | `git clone https://github.com/Dracowyn/ai-music-video-skill && cp -r .../skills/ai-music-video ~/.claude/skills/`; `pip install -r scripts/requirements.txt` | 2026-09-30 | **Top for us.** github.com/Dracowyn/ai-music-video-skill |
| **scenario-labs/skills**: `scenario-seedance-music-video`, `scenario-kinetic-music-video`, `scenario-video-assembly` | Shots planned on beats and sections, lyric transcription, master track never touched, assembly + verification. Kinetic variant: three.js lyric typography; `lyrics_align.py`, `plot_lyrics.py`, `lipsync_check.py`, `dance_sync_check.py`, `av_sync_check.py` | `npx -y skills add scenario-labs/skills --skill scenario-kinetic-music-video --agent claude-code` | 2026-08…11 | Strong; tied to Scenario/Seedance, but the scripts and rules carry over. github.com/scenario-labs/skills ; forks miskakaskinen/…, hommmm/… |
| **brahmsyaifullah/lyric-music-video** | Skill + Remotion template: word-synced karaoke (ElevenLabs STT + alignment to official lyrics), librosa beats, `veo_clip.py`, RIFE, `conform_clips.sh`, `validate_edl.py`, `qa_sheet.sh` | `cp -r skills/lyric-music-video ~/.claude/skills/` | 2026-09-26 | Good for lyric videos and EDL validation. github.com/brahmsyaifullah/lyric-music-video |
| **yongjip/song2mv** | `song2mv sync` → beat grid, word-timed lyrics, LRC, SRT, `mv.json`; `song2mv beats`; Claude skill in `.claude/skills/song2mv/` | clone | 2026-10-19 | alpha. github.com/yongjip/song2mv |
| **vargHQ/skills → varg-music-video** | "Direct an AI MV the way top X creators do": song map, beat-grid storyboard, stills first, Seedance, lip-sync (Sync v3), cuts on downbeats | `claude plugin marketplace add vargHQ/skills && claude plugin install varg@varg` | 2026-10-29 | beta; tied to varg.ai. Guide: github.com/vargHQ/awesome-ai-video-agents/blob/main/how-to/make-an-ai-music-video.md |
| **heygen-com/hyperframes → music-to-video** | Beat-synced lyric video, slideshow, kinetic promo | via skill-sets.md | 2026-11 | [?] skill-sets.md/skills/?category=media_generation |
| **NoizAI/skills → music-video** | 24 fps MV: p5.js/p5.brush animation or assembly of local clips; `mv.py init/analyze` (beats, onsets, low-frequency, loudness). Rule: scene intervals cover the song exactly once | `git clone https://github.com/NoizAI/skills.git ~/.claude/skills/music-video` | 2026-11 | Useful QA rule. aimcp.info/index.md/skills/88af16da-... |
| skills-hub.ai `song-to-music-video-2`, `music-video-storyboard-2` | Storyboard and per-shot prompts for Runway/Kling/Veo from lyrics + beat list; TikTok 15–30 s from the chorus | `npx @skills-hub-ai/cli install song-to-music-video-2 --target claude-code` | 2026-10-16 | Thin prompt-only skills. skills-hub.ai/skills/song-to-music-video-2 |
| tollens-ai/quality-education `.claude/skills/music-video` | Real production skill. Rule: **"time every sung word from the voice itself, never from the beat grid"**; karaoke preview before sign-off | – | 2026-09-24 | Good methodology example. github.com/tollens-ai/quality-education/blob/main/.claude/skills/music-video/SKILL.md |
| talsiach/take-one `references/music-video.md` | demucs → whisper → section map → storyboard approval → 30 s test | – | 2026 | Same flow as ours |
| madrobdestroyer/song-storyboard | "math owns timing, LLM owns story"; Demucs + wav2vec2 MMS_FA | – | 2026 | [?] |
| venetanji/creative-skills | ComfyUI Flux2 + LTX-2.3 + suno-mcp + music-video orchestrator | – | 2026 | [?] |
| coco-research/coco (hyperframes music-to-video) | `analyze-beatgrid.py`, `audiomap.json` | – | 2026 | [?] |
| VisualxIntelligence/motion-tools-and-skills → song-analysis | Demucs + CTC alignment + librosa | – | 2026 | [?] |
| guaardvark | Local AI suite: beat-synced MV director, "Film Crew", skills in `.agents/skills/`, `python -m backend.mcp install --skills` | – | 2026 | Heavyweight. github.com/guaardvark |
| remotion-dev/skills + official plugin | Remotion best practices, captions, render | `npx skills add remotion-dev/skills`; `claude plugin marketplace add remotion-dev/claude-code-plugin && claude plugin install remotion@remotion` | 2026 | [OK] remotion.dev/docs/ai/claude-code-plugin |
| MakeMyClip/editor | skill + CLI + MCP, exports FCPXML for Resolve/Premiere | – | 2026-05 | [?] |
| mrpaidsocial video-editor-agent | Claude skill pack; capcut-export is work in progress | – | 2026 | [?] |

**Skill catalogs:** skills.sh / `npx skills`, skill-sets.md, skillsdirectory.com, skills-hub.ai, aimcp.info, awesome lists (PhiloLabs/awesome-video-agents, renezander030/awesome-video-automation, vargHQ/awesome-ai-video-agents). MCP registry: **mcp.film** (stack.md, categories, compare), the official MCP Registry, Smithery, glama, PulseMCP.

---

## 3. Open-source song-to-MV pipelines, outside skills (P-S / P-R)

| Repo | Pipeline | Maturity |
|---|---|---|
| GeekatplayStudio/ComfyUI-Music-to-Video (2026-08) | Whisper, beat-cut 5–10 s segments, reference sheets, LTX 2.5 / MiniMax H3 | medium, ComfyUI |
| tsondo/musicvision (2026-02) | Whisper + LLM segmentation, FLUX storyboard, HuMo/LTX-2 lip-sync, **EDL/FCPXML export to Resolve**, React review UI | medium |
| hodgemann/mondo-music-video (2026-10) | beat/downbeat shot planner, LLM prompts, MCP tools, frame-exact assembly | early |
| JavaDerek/music-video-pipeline | stable-ts forced alignment, MiniMax H3 via ComfyUI | early |
| Merserk/BeatSync-Engine | Windows AMV beat editor, Qwen3-VL | niche |

The consensus across all these repos shapes our approach. None of them is a one-click product.

---

## 4. Lyric timing: what to use (P-A, citations below)

| Method | When | Weak spots |
|---|---|---|
| **Suno timestamped lyrics** (via third-party APIs: docs.kie.ai/suno-api/get-timestamped-lyrics, docs.sunoapi.org/suno-api/get-timestamped-lyrics, suno-api.io/en/docs/current-lyrics-timeline/) | Our Suno tracks: first draft | Returns `alignedWords` with `success` and `p_align`. Confidence does not guarantee accuracy. Section labels and gaps can slip in. Not an official Suno API. |
| **WhisperX** align (github.com/m-bain/whisperX) | Known text on the vocal stem | Speech model: melisma, long vowels, backing vocals, repeats |
| **stable-ts `align()`** (github.com/jianfch/stable-ts) | Retiming a known text | same |
| **torchaudio MMS_FA / wav2vec2** (pytorch.org/audio/stable/tutorials/forced_alignment_tutorial.html) | Custom pipeline; MMS covers many languages, Russian included | depends on the language and on the text being correct |
| **Demucs / MelBand-RoFormer** before alignment (github.com/facebookresearch/demucs, github.com/ZFTurbo/Music-Source-Separation-Training) | Dense mix | separation artifacts; **timing offset of the stem against the mix** (see `check_timebase.py` in Dracowyn) |
| LRC generators | Line-level karaoke | not enough for cuts on individual words |
| Musixmatch API (musixmatch.com/pro/api/) | Catalog releases with licensing | **not for our own Suno songs** |
| ElevenLabs STT + alignment to official lyrics | used in brahmsyaifullah | paid API |

Perplexity's verdict: no public benchmark compares these on sung vocals. Recommended order: Suno timeline as the draft, then forced alignment on both the stem and the mix (keep the better one), then a karaoke preview by ear. Plan broad visual beats on lines and phrases; set exact cuts on hand-corrected word starts.

---

## 5. MCP servers

### 5.1 Generation
- **Kling MCP (official, hosted, OAuth, Kling credits)** `[OK]`: already connected as `klingai`. A community Kling MCP has a wider tool set, including lip-sync.
- **Runway MCP (official, hosted OAuth)**: Gen-4.5 plus Seedance/Kling/Veo inside Runway. `[OK]` per mcp.film.
- **Higgsfield MCP**: `claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp`; 30+ models, up to 15 s. `[OK]`. Also `higgsfield-mcp-unified` (PyPI) `[?]`.
- **Luma API MCP**: `[LEGACY]`, frozen since April 2025.
- **Google GenMedia MCP** (GoogleCloudPlatform/genmedia-creative-studio/tree/main/experiments/mcp-genmedia) `[OK, experimental]`:
  - Go binaries for Veo t2v/i2v/extend/first-last, Omni, Lyria (music), Chirp, Nano Banana, and AVTool (ffmpeg).
  - Skills: genmedia-producer, genmedia-video-editor, genmedia-audio-engineer, story-generator.
  - Needs Vertex AI (a separate bill from Flow subscription credits). Imagen was shut down on 2026-08-17.
- **Aggregators:** kie.ai (neomorrison/kie-mcp, `@felores/kie-ai-mcp-server`), RunAPI (`@runapi.ai/suno-mcp`), Runware, PiAPI, GenMagic, **Createya-ai/createya-mcp** (Russian, billed in rubles, no VPN needed) `[?]`.
- **Revid MCP** (revid.ai/mcp): an end-to-end music-to-video service through MCP `[OK]`.

### 5.2 Google Flow (browser automation) `[TOS]`
- **RohaanA/google-flow-mcp**: `FLOW_CDP_URL=http://127.0.0.1:9222`, `FLOW_MAX_CREDITS_PER_CALL`. **Closest match to our setup** (CDP 9222, cost guard).
- felipedamacenoteodoro/mcp-google-flow (spending guards); hainguyen-keyti/google-flow-mcp (50 tools, spend ledger).
- ffroliva/gflow-cli (365 stars; movie manifests + MCP); kodelyx/flow-agent (256 stars); useapi/google-flow-api (82 stars, paid proxy).
- Souvik988, GTAI-1/flow-mcp, TMSSS05/google-flow-browser-mcp, miyakejima, molkex, ParkSangGwon; Auto-Flow Chrome extension.
- Prompt docs: raphaelbgr/ai-video-prompting (google-flow-veo-playbook.md), akinluyigithub/Google-Flow-Workflow.
- Lesson from aaronnorton.co.uk/books/music-video-ai (a P-S case study): **driving the web UI is cheaper than the API**. Generations that fall inside a subscription's "unlimited" window are billed per clip through the API. This is the economic argument for our CDP approach, but the ToS risk remains.

### 5.3 Suno (all unofficial; Suno has no public API)
- unforced/suno-mcp (CDP browser) `[TOS]`
- jchoi2x/suno-mcp (based on gcui-art/suno-api)
- travelhawk/suno-api-mcp (sunoapi.org)
- **AceDataCloud/SunoMCP** (in the official MCP Registry)
- CodeKeanu/suno-mcp
- `@runapi.ai/suno-mcp`
- Since 2026-09-03, Suno ties commercial rights to a file officially downloaded on a paid plan (vc.ru/ai/3140655) `[?]`. Keep this in mind when downloading through third-party APIs.

### 5.4 ffmpeg / editing
- **gulkoa/claudeclip** (`npx -y claudeclip`; `sample_frames` contact sheets, 2026-08)
- Galvez92/video-edit-mcp (HyperFrames captions, local Whisper, 2026-10)
- PlbKin190/video-editor-mcp (JSON-timeline render + QA, 2026-09; sibling video-atelier-mcp)
- mfortne/mcp-video-editing (`uvx --from mcp-video mcp-video`)
- Ashutos1997/ffmpeg-mcp-server (scene detection)
- alanveloper-epam, aitherlab-dev (Rust), pauloFroes, PedroMarianoAlmeida, yubraaj11, bitscorp-mcp, StigLau, beambuilder, kush36agrawal, gxtontata
- Comparison list: a1adams/mcp-servers-for-video-editing (2026-10-06)

Our own Python/ffmpeg scripts are more reliable for frame-exact assembly. These MCPs are mainly useful for quick QA (contact sheets, scene detection).

### 5.5 NLE
- **DaVinci Resolve:**
  - samuelgursky/davinci-resolve-mcp (~3.9k stars, v4.18.x; `npx davinci-resolve-mcp setup`). Needs Studio; Resolve 21.1 moved scripting to Studio.
  - hiteshK03 (150 stars, 162 tools, works on the free edition via an in-app bridge)
  - lordhoell (skill + 440+ tools), guycochran (Resolve 21), tooflex, apvlv
- **Premiere:**
  - hetpatel-11 (`adobe-premiere-pro-mcp`, 283 tools, **telemetry on by default**)
  - ayushozha/AdobePremiereProMCP (1,000+ tools), leancoderkavy, au-yong
  - koptsev63/premiere-claude-bridge (Premiere + Resolve)
- **CapCut / JianYing (draft JSON):**
  - GuanYixuan/pyJianYingDraft (4.8k stars), pyCapCut (737)
  - Hommy-master/capcut-mate (2.1k; FastAPI) + capcut-mate-skill
  - xuliang2024/cutcli-cookbook (MCP / Claude Code), juliang8507/cli-anything-capcut, Simon-del424/capcut-mate-mcp, CapCutAPI forks
- **Blender:** ahujasid/blender-mcp, renamed **mcp-for-blender** (~32k stars). `claude mcp add blender uvx mcp-for-blender`; socket port 9876; has telemetry (can be turned off); premium tier. Blender's official lab MCP server: blender.org/lab/mcp-server/ (Blender 5.1+). Relevant only for 3D previz or camera layout.

---

## 6. Case studies: time and cost (P-S)

| Source | Format | Time | Money | Notes |
|---|---|---|---|---|
| aaronnorton.co.uk/books/music-video-ai (2026-09) | 4 min narrative, hyper-realistic | **~90 h over 4 weeks** | **~£300** all-in (yearly generator subscription, LLM, free editor, 1 month of upscaler) | ~3 s per shot; 4 min ≈ 80 beats × several angles ≈ **240 clips**; "work in the cut, not the clip"; web UI cheaper than API |
| aivideobootcamp.com/blog/how-to-make-money-ai-music-videos (2026-07) | 3 min | **~36 h** (19 h generation and review + 4 pre-production + 8 edit/grade + 5 revisions) | **$250–700 compute** | 45 usable shots at an 8% keep rate = 577 generations; Kling O3 Std $0.084/s, Seedance 2.0 $0.24–0.30/s (fal.ai). Market rate $600–1,200 per video |
| visuals.fm/compare/ai-vs-traditional-music-video-cost (2026-10) | 3 min | not stated | Kling 3 Pro 1080p ≈ $368–424; Veo 3.1 Lite 1080p ≈ $62–71 | assumes a **3:1 generated-to-used ratio** (540 s generated for 180 s). Model choice changes the bill about 7× |
| freebeat.ai comparison (2026-07, vendor) | 6 min | Kling ~10 h, Runway ~12 h manual editing | Kling ~$160, Runway ~$280 | marketing source; useful only as a rough reference |
| suno.bi blog (2026-05/11, unofficial) | 40 s short | 1–40 min | $0.5–20 | H3 Max as a cheap preview layer; an "expensive chorus, cheap verses" strategy |
| onemoreshot.ai (2026-07) | 3 min | – | "$30–50 on Kling" | **underestimate**: ignores retake ratio |
| aituber.app (2026-05) | cinematic | 2–4 h | $20–50/mo | optimistic |

**Takeaways for our planning:**
- Budget a **3:1 to 12:1 generated-to-used ratio** (keep rate 8–33%).
- A 3-minute song needs about **45–80 shots**.
- Realistic labor is **36–90 hours**.
- Cost depends mostly on the model: Veo Lite/Fast is cheap; Kling Pro and Seedance cost 4–7× more.

Russian sources (vc.ru, prices in rubles):
- vc.ru/ai/3231511 (2026-11-02): Veo 3.1 at 19.7 ₽/s without audio vs 39.4 ₽/s with audio, so **turn generated audio off when the clip goes under our own music**; Veo 3.1 Fast at 9.8 ₽/s; Suno V6 at 4 ₽ per song.
- vc.ru/ai/3170394: Kling v3 Pro $0.05/s on fal.ai.
- habr.com/ru/companies/bothubchat/articles/1057036 (2026-07-08): Veo 3.1 $0.40/s, Fast $0.10–0.12/s, Lite $0.05/s on the Gemini API.

These are reseller prices. `[?]`

---

## 7. Official prompt formulas (P-S)

- **Veo 3.1 (Google Cloud):** `[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]`. Opens with the camera. Source: cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1
  - Reference images, 1080p and 4K all force an 8 s clip.
  - Up to 3 reference images, first/last frame, extend.
- **Kling (kling.ai/blog/ai-video-prompt, 2026-10):** `[Subject] + [Action & Motion] + [Environment] + [Camera Movement] + [Lighting] + [Style & Pacing] + [Constraints]`.
  - Negatives go inside the prompt; the newer API has no separate field.
  - Kling 3.0: 3–15 s, Custom Multi-Shot with a duration per shot (`Shot 1 (Xs): ...`), `@ElementName` for recurring subjects.
  - Source: kling.ai/blog/ai-video-generation-models
  - Kling's own examples include constraint phrasing such as "SFX only, no music, no score, no song", which fits our "the song is the only score" rule.
- **Runway Gen-4.5:**
  - T2V: `[Camera] shot of [subject] [action] in [environment]. [Supporting descriptions]`.
  - I2V: describe **motion only** (`The camera [motion] as the subject [action]`); do not redescribe the image.
  - Sequential timestamps work: `[00:01] X. [00:03] Y.`
  - Positive phrasing only: "smooth stable camera", not "no shake".
  - One action per 5–10 s clip.
  - Sources: help.runwayml.com/hc/en-us/articles/42460036199443, .../48324313115155, academy.runwayml.com/guides/prompting-guide, runway.com/resources/ai-video-prompting-guide
- Comparison of vendor formulas: aipromptgeneer.com/craft/official-formulas/
- A good model cheat sheet for Claude: SlavaSexton/ComfyUI-Agent-Kit `claude-code/skills/comfyui/MODELS/video-api.md`.

---

## 8. Integration recommendations (proposals; do not implement without approval)

1. **Timing layer:**
   - Add a Suno timestamped-lyrics fetch (via our existing Kie/third-party access, if any) as a draft.
   - Compare it with forced alignment on the Demucs stem.
   - Adopt the **stem-offset check** idea (`check_timebase.py`) and the **`resolve_shots.py`** idea (shot anchors expressed in musical terms).
2. **QA layer:** use `avsync_check.py` / `lipsync_check.py` ideas to find where a generated singing clip drifts and where to cut. A contact sheet (claudeclip `sample_frames` or our own ffmpeg tile) for each shot before assembly.
3. **Flow:** compare our `FLOW_MAX_CREDITS` guard with RohaanA/google-flow-mcp and hainguyen-keyti (spend ledger) for ideas. Our branch `fix/google-flow-p0-cost-guard` covers the same problem.
4. **Cost planning:** for each scene, store the expected keep rate and generation budget (3:1 baseline). Turn Veo's native audio off wherever possible.
5. **Do not adopt:**
   - all-in-one generators (we lose the character sheet and editing control)
   - Udio (downloads closed)
   - Luma MCP (frozen)
   - Premiere MCP with telemetry on

---

## 9. Perplexity calls in this session

- **perplexity_research:** AI music video generators, Nov 2026 (section 1). Citations: neuralframes.com/pricing, kaiber.ai/pricing, revid.ai/mcp, platform.vidu.com/docs/..., mv-director.higgsfield.app, blog.google/.../flow-updates/, help.udio.com/en/articles/12683565, kling.ai/feature/ai-music-video-generator, freep.com (Enkio/SelfyzAI).
- **perplexity_search:** ffmpeg/video MCPs, Resolve/Premiere MCPs, CapCut automation, Remotion skills, generation MCPs (mcp.film), GenMedia MCP, Suno MCPs, Flow MCPs, song-to-MV repos, music video skills, Blender MCP, case-study costs, Russian sources, official prompt guides. URLs are inline above.
- **perplexity_ask:** lyric alignment comparison (section 4). Citations: docs.kie.ai, docs.sunoapi.org, suno-api.io, musixmatch.com/pro/api, plus the GitHub docs for WhisperX, stable-ts, torchaudio, Demucs and MelBand-RoFormer.

**Not covered or not verified:**
- Telegram channels: not searched separately.
- Habr: covered only by pricing reviews, with no detailed MV pipeline write-up.
- Washed Out / Paul Trillo (Sora), Runway AIFF and Curious Refuge case studies: no cost figures found in this pass.
- Deforum, Parseq, ComfyUI audio-reactive nodes (Yvann-Nodes), auto-editor, MoviePy beat sync: not checked separately (out of scope for our I2V pipeline).
- Stars and dates are taken from search snippets and were not checked against the GitHub API.
