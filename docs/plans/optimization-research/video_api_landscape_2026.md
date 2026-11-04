# R8: Video-API-Landschaft 2026 & Optimierungsvorschläge für die Video-Provider-Pipeline

> **Archiviert am:** 2026-10-05 · **Anlass:** Nutzeranfrage „Recherche nach preiswerter und qualitativ hochwertiger Video-Generierung und Pipeline-Bau — neueste Möglichkeiten und Methoden, Skills, APIs, MCPs — mit Bezug auf unser Projekt verbessern und optimieren".
> **Methode:** Perplexity-Websuche (Stand: Oktober 2026, Preisquellen datiert Jan–Sep 2026) + direkte Code-Sichtung des Ist-Zustands.
> **Status:** Recherche abgeschlossen; **P0 + P1 + Rest von P1.5b/P2 am 2026-10-05 umgesetzt (siehe §五a)**. P1.5 entfällt (durch v7.1.2 `AGNES_SCENE_FRAME_CHAINING` abgedeckt); P3 (fal-MCP-Doku) offen.

---

## 一、Ist-Zustand (direkt aus dem Code, Stand v7.1)

### 1.1 Provider-Abstraktion — `core/api/video_providers.py`

- **`VideoProviderBase`** (ABC): bewusst identische Oberfläche zu `AgnesVideoAPI` — `submit_video(...)`, `wait_for_video(...)`, `resolve_image_ref(...)`, `shutdown_event`. Alle 5 Pipelines (manuscript / poetry / simple / anchor / creative) gehen über die Fabrik `create_video_provider()` (Zeile 288), gesteuert per Env `AGNES_VIDEO_PROVIDER` (`"agnes"` = Default, `"fal"` → `FalVideoProvider`).
- **`FalVideoProvider`**: Default-Modell `fal-ai/kling-video/v1.5/pro/image-to-video` (Kling v1.5 Pro I2V); T2V wird per String-Ersetzung abgeleitet. Dokumentierte MVP-Einschränkungen: nur 1 Referenzbild, `progress_callback` No-op, kein serverseitiger Cancel, Dauer-Snapping auf {5, 10} s, Seed ignoriert, Restart-Resume für T2V defekt (Endpoint-Map nur im RAM).
- **Konfiguration:** `agnes_video_provider` + `fal_video_model` in `core/config.py`; `.env.example` Z. 118–122. `fal-client` bewusst NICHT in `requirements.txt` (optional).

### 1.2 Experimentelle Clip-Pipelines (Projektstamm, nicht integriert)

- **`fal_clip_pipeline.py`** (759 Zeilen): bezahlter Prototyp für ein komplettes Musikvideo (~173 s, 6 Szenen). Stages: Character-Sheet via **Nano Banana 2 edit** ($0.16) → Keyframes pro Szene mit **gratis Agnes-Vision-QC-Gate + 1 Auto-Regenerierung** ($0.08/Bild) → Videos via **MiniMax H3 Max reference-to-video** (3-Bild-Referenzstapel + vorheriger Clip als Bewegungsreferenz, First→Last-Frame-Verkettung zwischen Szenen, Veo 3.1 First-Last optional; $0.30/Clip) mit Video-QC-Gate + Retry → Wan-Animate-Repair → ffmpeg-Stitch. **Hardcoded private Pfade** (Song in `C:\Users\Valeri\Downloads`, Fotos in `D:\FotosVideos`).
- **`agnes_clip_pipeline.py`** (661 Zeilen): Gratis-Gegenstück (10 Szenen × 17 s): Style-Anker-Bild → i2i-Keyframes mit QC + 1 Regen → i2v pro Keyframe (3 Versuche, Konkurrenz 6) → Stitch. Umgeht KeyRing/Rate-Limiter der App (liest `AGNES_API_KEY` direkt).
- **`agnes_clip_qc.py`**: Nachlauf-QC — 9 QA-Frames pro Szene an Agnes multimodal Chat mit Checkliste (Identität, Stil, Palette, kein Text/Flaggen, geschlossene Münder); schreibt `agnes_out/qc_report.txt`. **Nur manuelle Nachsicht, keine Auto-Regenerierung.**

### 1.3 v7.1-Stand & Lücken

- `docs/plans/v7.1/`: zwei PRDs (🟢 implementiert): **I2V-Keyframe-Modus** (statisch/Bewegungs-Dual-Prompts, Keyframe-Checkpoint, Default aus) und **Provider-PRD**. **Offen:** Regressionsszenarien M5/P2 „später nachzuholen".
- **Lücken:** ① QC-Gate existiert nur im Root-Experiment, nicht in `core/`; ② `FalVideoProvider` abstrahiert nur einen Bruchteil der im Experiment genutzten fal-Fähigkeiten (Multi-Reference r2v, First/Last-Frame, Repairs); ③ Provider-Wahl global per Env, nicht pro Task, nicht im Web-UI; `/api/models`-Dropdown ignoriert `provider=fal` (PRD-Limitierung Nr. 5); ④ keine Kostenverbuchung; ⑤ Kling **v1.5** Pro als Default ist zwei Modellgenerationen alt.

---

## 二、Marktlandschaft (Stand September/Oktober 2026)

### 2.1 Preise pro ausgeben­der Sekunde (Listpreise)

| Modell | $/s | Auflösung | Dauer | Audio | Bemerkung |
|---|---|---|---|---|---|
| **MiniMax H3 Max Turbo** (fal) | **0,025** | 480p/768p | 5–15 s | ja | schnellste Route, T2V/I2V |
| **MiniMax H3 Max** (fal) | 0,05 (480p) / 0,08 (768p) / 0,16 (1080p) | s. links | 5–15 s | ja (Stereo) | + **r2v-Variante**: bis 12 Referenzdateien (Bilder/Videos/Audio), 4096 Ref-Tokens gratis, danach $0,02/1k; 5-s-Clip in < 3 s generiert |
| **Veo 3.1 Lite** (Google direkt) | 0,05 (720p m. Audio) / 0,08 (1080p); ohne Audio 0,03 (Vertex) | 720p/1080p | 8 s | ja | günstigster Marken-Audio-Clip; kein 4K |
| Runway Gen-4 Turbo | 0,05 | 720p | — | nein | — |
| **Kling v2.5 Turbo Pro** (fal) | 0,07 | 1080p | 10 s | nein | solider Mittelbaustein |
| Seedance 2.0 **Fast** | ~0,09 (1080p) | bis 4K | — | nein | „günstigster Produktionsqualitäts-Baustein" (Atlas, Juni 2026) |
| Seedance 2.0 **Mini** (Promo Kie.ai bis 7. Okt. 2026) | 0,019 (480p) / 0,041 (720p) | — | — | nein | Promo läuft in 2 Tagen ab |
| Seedance 2.0 (fal, Token) | 0,014/1k Tokens | — | — | nein | r2v + i2v |
| Wan 3.0 | 0,10 (720p, −30 % Promo) | — | — | nein | — |
| Kling v3 Pro (fal) | 0,112 (o. Audio) / 0,168 (m. Audio) | 1080p | 10 s | ja | ~halb so teuer wie bei Replicate; „Structured Storytelling"-SOTA |
| Veo 3.1 Fast | 0,10–0,12 (4K: 0,30) | bis 4K | — | ja | — |
| Sora 2 | API **abgeschaltet** (laut laozhang.ai zum 24. Sep. 2026) | — | — | — | Argument für Provider-Diversifikation |
| Veo 3.1 Standard / Seedance 2.5 | 0,40–0,60 / ~0,23–0,30 | — | — | ja | Premium-Liga, für uns uninteressant |

**Kernsatz der Branche:** „The route decides the bill" (teamday.ai, Jan 2026) — gleiches Modell, unterschiedliche Storefronts:
- **Kling → fal** kaufen (halb so teuer wie Replicate), **Seedance → BytePlus / Replicate / Kinovi**, **Veo → Google direkt** (fal/Replicate gleich teuer).
- Audio Adds 50–100 % auf den Preis.

### 2.2 Aggregatoren / Storefronts

| Plattform | Profil | Relevanz für uns |
|---|---|---|
| **fal.ai** | beste Dev-Tooling (dauerhafte Queue, signierte Webhooks, SDK); neue Accounts starten mit 2 Concurrent-Requests | bereits integriert (v7.1) — bleiben |
| **Kie.ai** | 30–80 % unter Listenpreis, 80 Gratis-Credits, Credits verfallen nie; **variabilität/Zuverlässigkeit schwankt je nach Modell** | nur bei akutem Kostendruck; Vorteil bei Veo ist durch Veo 3.1 Lite direkt ($0,05/s) weitgehend entfallen |
| **Replicate** (gehört zu Cloudflare) | unveränderliche Modell-Versionierung (Reproduzierbarkeit!), Outputs nach 1 h gelöscht, Credits laufen nach 12 Mon. ab | Alternative für Seedance 720p ($0,18/s) |
| Kinovi / APIMart | aktuell günstigste Seedance-Listenpreise | Beobachtungsposten, kein Handlungsbedarf |

### 2.3 Gratis-Lage (kritisch für unsere „komplett kostenlos"-Positionierung)

- **Kein großer Anbieter hat mehr einen API-Gratis-Tier** (Google, xAI, MiniMax, Kling, Pika, Runway, Luma: „Not available", Stand 30. Sep. 2026). Nur Magic Hour (Registrierungs-Credits) und Tavus (Avatar-Basic) geben Testguthaben.
- Web-only-Gratisreste: Kling 2.6 (Monatscredits), Google Flow (50 Credits/Tag), Runway (125 einmalig) — nicht per API nutzbar.
- **Folgerung: Die gratis Agnes-API ist das Alleinstellungsmerkmal des Projekts und MUSS Default bleiben.** Bezahlte Provider bleiben Opt-in-Upgrade. Gleichzeitig zeigt die Sora-API-Abschaltung, dass auch Bezahl-APIs fragil sind → unsere U1–U8-Härtung (v7.0) war richtig; eine **Provider-Fallback-Kette** (Agnes → fal) ist der konsequente nächste Schritt.

### 2.4 Open Source / Self-Hosting

- Wan 2.2 (24 GB+ VRAM), LTX-2 (stark für First/Last-Frame-Conditioning), HunyuanVideo — gratis nur beim Self-Hosting. **Kein neuer Weg** für uns: R6 (Kaggle) und R7 (HF Spaces) haben 2026-09-23 schon concluso „nicht als Generierungspfad". Bleibt als Beobachtung, falls自有 GPU vorhanden.

### 2.5 Konsistenz-Methodik 2026 (Best Practices, direkt auf unsere Pipelines mappbar)

1. **Character-Sheet zuerst** (Nano Banana 2/Pro bzw. Flux 2 Pro): Multiwinkel-Identitätsanker vor Szene 1 erzeugen und überall referenzieren — „Identity gehört in Referenzen, nicht in Prompts" (Worte driften, Referenzen nicht).
2. **Keyframe-first + QC-Gate:** Stills pro Szene, per VLM prüfen, **erst dann Videogeld ausgeben** — genau das macht unser fal-Experiment und seit v7.1 der I2V-Keyframe-Modus (Default aus).
3. **Last-Frame→First-Frame-Verkettung** („Temporal Bridge", arXiv 2512.16954): letzter Frame von Clip N = Start-/Endframe-Bedingung von Clip N+1 → kontinuierliche Bewegung über Schnitt. H3 Max I2V unterstützt End-Frame; Kling/LTX-2/Veo 3.1 unterstützen First+Last.
4. **Reference-to-Video mit Multi-Referenzen** (H3 Max r2v: ≤ 12 Dateien inkl. Bewegungs-/Audio-Referenz; Seedance 2.0 r2v): Identität/Style/Stimmen konsistent halten — im Prompt mit „Bild 1/2, Video 1" adressierbar.
5. **Style-Präambel-Templates:** fixer Stil-Block + szenenspezifische Mitte + fixer technischer Schluss — über alle Szenen identisch.
6. **Seed-Locking für Hero-Shots** (Solche mit gleichem Seed + leicht geändertem Prompt bleiben nah).
7. **I2V-Fallback-Kette über Provider** (Veo lehnt ab → Vidu → Seedance → Wan → Kling, Eingabebild bleibt identisch erhalten → Identität bleibt): passt exakt zur KeyRing/Retry-Architektur aus v7.0.
8. **Dasselbe Bildmodell für Start- UND Endframe** (Farbe/Licht konsistent).
9. **Lip-Sync als Postprozessor** wenn Figuren sprechen (HeyGen-Modelle jetzt auf fal; H3 Max nimmt Referenz-Audio) → **Relevanz für R1**: der dort definierte Re-Eval-Auslöser („Lip-Sync verfügbar?") ist ökosystemseitig teilweise erreicht — als Kommentar in R1-Rückschau würdigen, R1 selbst nicht ändern.
10. **VLM-QC-Gate mit harter Retry-Obergrenze (≤ 3) + Cost-Gate-Kopplung**: Schichtenmodell „technische Validierung (gratis) → Heuristik → VLM-Richter (teuer)"; bei Obergrenze laut scheitern/zum Menschen eskalieren. Akademische Rückendeckung: AIGVE-MACS (CVPR-2026-Workshop) berichtet +53,5 % Qualität durch Feedback-Loop-Regenerierung.

### 2.6 MCP-Server (für den Betreiber-Workflow, nicht als Produktfeature)

- **fal MCP:** `https://mcp.fal.ai/mcp-relay` (Streamable HTTP, OAuth — kein API-Key im Client nötig). Tools: `search_models`, `recommend_model`, `get_model_schema`, `get_pricing`, `run_model`, `submit_job`, `check_job`, `get_job_result`, `cancel_job`, `upload_file`. Abrechnung identisch zur Direkt-API.
- **Replicate MCP:** `https://mcp.replicate.com` (Browser-Auth oder Token, volle HTTP-API-Oberfläche, unveränderliche Versionierung).
- **Nutzen für uns:** Agent-getriebene Clip-Produktion direkt aus ZCode/Claude heraus (Modell-Suche + Preisprüfung vor Ausgabe, Queue-Handling) — dokumentiert in `docs/dev/`, keine Änderung am Produkt.

### 2.7 Bildmodelle auf fal (für Keyframe-Stage)

| Modell | Preis | Einsatz |
|---|---|---|
| Z Image Turbo | $0,005/Megapixel | extrem günstige Keyframe-Alternative |
| Nano Banana 2 (edit) | $0,08/Bild | Character-Sheets/Edits (im Experiment im Einsatz) |
| Nano Banana Pro | $0,15/Bild | höchste Identitätstreue |

---

## 三、Verbesserungsvorschläge (priorisiert)

| Prio | Maßnahme | Nutzen | Aufwand |
|---|---|---|---|
| **P0** | **`FalVideoProvider`-Default modernisieren:** `fal_video_model` → `minimax/h3-max/image-to-video` (oder Kling v2.5 Turbo Pro); Dauer-Snapping {5,10} → 5–15 s; `VideoProviderCapabilities` aktualisieren. Kling v1.5 Pro ist zwei Generationen alt — neuere Modelle sind schneller UND günstiger ($0,025–0,07/s) | hoch, geringes Risiko (Teststubs existieren: `tests/test_video_providers.py`) | 0,5–1 Tag |
| **P1** | **QC-Gate in `core/` generalisieren** (aus `agnes_clip_qc.py` + Experiment): pro Szene N Frames sampeln → Agnes-Chat-multimodal-Rubrik → Pass/Fail → 1 Auto-Regenerierung, harte Obergrenze 2–3, danach Human-Review-Flag (Artifacts + Task-State-Feld). QC läuft über den **gratis** Agnes-Chat → null Mehrkosten; Task-Level-Toggle (Default aus, wie I2V-Keyframes) | hoch — „Videogeld erst nach bestandenem Still-QC ausgeben" ist die größte Kosten-/Qualitätshebel-2026er-Methode | 2–3 Tage |
| **P1.5** | **First/Last-Frame-Verkettung in `MultiScenePipeline`** (opt-in): letzter Frame von Clip N als End-/Startframe-Bedingung von Clip N+1 (H3 Max I2V End-Frame; Kling First+Last) — natürliche Erweiterung der v7.1-Keyframe-Kette | sichtbare Bewegungskontinuität über Schnitte | 2–3 Tage |
| **P1.5b** | **Provider-Auswahl pro Task + UI:** Param in `task_creation_routes`, Dropdown im Frontend, Fix `/api/models` bei `provider=fal` (PRD-Limitierung Nr. 5); dabei MVP-Schulden abbauen: Endpoint-Map in Task-State persistieren (Restart-Resume), `progress_callback` implementieren, Multi-Referenzbilder (H3 Max r2v: 5 Bilder gratis-Tokens) | Bedienbarkeit + Robustheit | 2–3 Tage |
| **P2** | **Kostenverbuchung:** Preistabelle in `VideoProviderCapabilities`; geschätzte/tatsächliche Kosten pro Szene/Task in State + UI (Agnes = $0,00). Optional: **Provider-Fallback-Kette** Agnes→fal bei wiederholtem Scheitern (Eingabebild bleibt erhalten — Versely-Muster, passt zu U1–U8) | Transparenz, schützt vor Retry-Explosion | 0,5–1 Tag |
| **P3** | **fal MCP in den Betreiber-Workflow** aufnehmen (`docs/dev/`), Kie.ai nur bei nachgewiesenem Kostendruck prüfen | niedrig | < 0,5 Tag |

**Explizit nicht verfolgt:** Open-Source-Self-Hosting als Generierungspfad (R6/R7-Beschlüsse gelten weiter), TTS-Austausch (R2 bleibt), Native-Audio-Videomodelle als Ersatz für edge_tts+Untertitel (die Wortzeitstempel-Pipeline ist unsere „Source of Truth", §6.9 AGENTS.md). Lip-Sync (R1) neu bewerten, wenn ein konkreter Anwendungsfall da ist — Ökosystem (HeyGen auf fal, H3-Max-Referenz-Audio) ist inzwischen bereit.

---

## 四、Erwarteter Nutzen & Kostenbeispiel

Beispiel 10-Szenen-Clip à 10 s bei 768p (H3 Max r2v): 100 s × $0,08 ≈ **$8,00** — mit Keyframe-QC-Gate (gratis über Agnes-Chat) und nur 1 Regenerierungs-Slot bleibt das der Obergrenze nahe; ohne Gate multipliziert sich der Preis mit der Versuchszahl („retries set the real cost" — laozhang.ai). Mit P0 (H3 Max statt Kling v1.5) sinken Preis UND Latenz gleichzeitig (5-s-Clip in < 3 s).

Gesamtaufwand P0–P2: ca. 7–11 Personen­tage, verteilt auf unabhängige Inkremente; Regression: `tests/test_video_providers.py` erweitern, offene M5/P2 aus v7.1 einplanen.

---

## 五、Grund für Zurückstellung (nicht implementiert)

- Projekt ist im 🟢 Wartungsmodus; Änderung des bezahlten Provider-Defaults (P0) und neue Pipeline-Verhalten (P1/P1.5) sind Produktentscheide.
- Diese Recherche folgt dem Archiv-Flow: **ausreichend recherchiert, Umsetzung wartet auf Priorisierung** durch den Nutzer; bei Freigabe wandern P0/P1 als Batches in `../v6.0/optimization_roadmap.md`.

---

## 五a、Umsetzungsstand (2026-10-05, Batches 1–3)

Die Nutzerfreigabe („mache es") ist erfolgt; umgesetzt in drei Batches:

**Batch 1 — H3-Max-Default + Kostenverbuchung (P0 + P2-Teil):**
- `fal_video_model`-Default → `minimax/h3-max/image-to-video`; neue Modellprofile `_FAL_MODEL_PROFILES` (H3 Max i2v/t2v, Kling v1.5/v2.5/v3 als Legacy) mit `duration_range` 5–15 s (int-Snap bzw. str-Snap auf {5, 10}), Auflösungsstufen 480P/768P, `supports_first_last_frame`, `price_usd_per_second`, Seed-/Negative-Prompt-/Aspect-Ratio-Flags.
- Kostenabschätzung: `estimate_clip_cost_usd` / `spent_usd` in `FalVideoProvider`; `MultiScenePipeline._announce_video_cost` schätzt vor der Video-Phase und persistiert `estimated_video_cost_usd` im Task-State; Budget-Gate `AGNES_VIDEO_BUDGET_USD` (0 = unbegrenzt) bricht **vor** Ausgabe ab.
- Restart-Resume-Selbstheilung: `wait_for_video` merkt sich den Endpoint und wechselt bei Statusfehler einmalig auf das Geschwister-Endpoint (i2v ↔ t2v); `progress_callback` pro Poll implementiert (ehemalige No-op-Schulde abgebaut); `/api/models` liefert den `video_provider`-Katalog (`get_video_provider_catalog`).

**Batch 2 — VLM-QC-Gate in `core/` generalisiert (P1):**
- Neu `core/quality/qc.py` (`ClipQCGate`): N Frames pro Clip sampeln (ffmpeg/ffprobe, MoviePy-Fallback), Rubrik-Judging über den **gratis** Agnes-Chat-multimodal (u. a. Erkennung gedrehter Bilder = dokumentierter v2.5-Portrait-Defekt), vollständig fail-open.
- Verdrahtung als opt-in Phase 3.5 in `MultiScenePipeline.run()` (Task-Feld `qc_enabled`, Default aus, analog I2V-Keyframes): 1 Auto-Regenerierung (`_QC_MAX_REGEN_ROUNDS`), Original-Clip bleibt erhalten, Ergebnis in `qc_report`. Per-Task-Details über überschreibbare Hooks (Manuscript: `para_{i}/video.mp4` + Keyframe/Ref-Map; Anchor: `clip/clip.mp4` + Ankerbild; Creative: Szenen-Ref/Character-Ref).
- Frontend: QC-Schalter im Manuscript-/Poetry-Formular + QC-Schritt in beiden Schrittlisten, i18n-Schlüssel in allen 22 Sprachen, `static/` neu gebaut.

**Batch 3 — Rest von P1.5b: entfallen bzw. abgedeckt:**
- Provider-Wahl pro Task + UI: **Descope** — der parallele v7.3-Zweig („Modell wählen = Provider wechseln") hat dies obsolet gemacht: `create_video_provider()` routet bereits nach Modell-ID-Präfix (`fal-ai/*`, `minimax/*`) je Task ohne Env-Umschalter. Die obigen Ergänzungen (Kosten, Selbstheilung, Katalog) wurden additiv mit diesem Zweig kompatibel gehalten.
- First/Last-Frame-Verkettung (P1.5): entfällt — bereits durch v7.1.2 `AGNES_SCENE_FRAME_CHAINING` abgedeckt.

**Tests:** `tests/test_video_providers.py` erweitert (H3-Max-Pfade, Dauer-Snap, Seed, End-Frame, Kosten/Budget-Gate, Selbstheilung, Kling-Legacy, Pipeline-Verdrahtung), neu `tests/test_qc_gate.py` (hermetisch, fake ffmpeg/VLM); Poll-Intervall in Tests dauerhaft auf 0 gehärtet (`_FAL_POLL_INTERVAL_SECONDS` monkeypatched). Offen: P3 (fal-MCP im Betreiber-Workflow dokumentieren); `fal-client` bleibt optionale Abhängigkeit.

---

## 六、Quellen (alle abgerufen 2026-10-05 via Perplexity)

- fal-Preisliste (29.09.2026): https://fal.ai/pricing — H3-Max-Familie, Kling v2.5/v3, Seedance 2.0, Nano Banana 2, Z Image Turbo
- fal Character-Consistency-Leitfaden (22.09.2026): https://fal.ai/learn/tools/ai-character-consistency — H3-Max-r2v-Details, 12-Dateien-Limit, Token-Abrechnung
- Seeddance-Preisvergleich (22.09.2026): https://www.seeddance.io/blog/ai-video-api-pricing-comparison — Veo-3.1-Familie, Wan 3.0, MiniMax-Pakete
- teamday.ai (29.01.2026): https://www.teamday.ai/blog/ai-api-pricing-comparison-2026 — „Route decides the bill", Kling→fal, Audio-Aufschlag
- Atlas Cloud (12.06.2026): https://www.atlascloud.ai/blog/tips/cheapest-ai-video-generation-api-2026 — Seedance-2.0-Fast-Kosten inkl. Retries
- laozhang.ai (März 2026, Stand Sep. 2026): https://blog.laozhang.ai/en/posts/how-much-does-ai-video-generator-cost — Sora-API-Abschaltung, Retry-Kosten; https://blog.laozhang.ai/en/posts/best-free-ai-video-api — keine Gratis-Tiers mehr
- Kie.ai-Review (21.07.2026): https://aiinsightsnews.net/kie-ai-review/ — Aggregator-Rabatte + Zuverlässigkeitsvorbehalt
- Kinovi-Vergleiche (14.08.2026): https://kinovi.ai/blogs/kie-ai-alternatives ; https://kinovi.ai/blogs/runway-api-alternatives — Seedance-Storefront-Preise, Replicate/fal-Details
- MiniMax-Plattform-Doku: https://platform.minimax.io/docs/guides/video-generation — H3/H3-Max-Modi (I2V First/Last, r2v ≤ 9 Bilder + 3 Videos)
- Versely-Workflows (2026): https://www.versely.studio/blog/versely-ai-movie-maker-multi-scene-storyboard-workflow-2026 — I2V-Fallback-Kette, Seed-Locking
- Luma Multi-Scene-Leitfaden: https://lumalabs.ai/news/multi-scene-ai-video — Last-Frame-Chaining, Referenz-Locking
- arXiv 2512.16954 „Lights, Camera, Consistency": https://arxiv.org/html/2512.16954v1 — Temporal-Bridge-Pipeline (LLM-Skript → Asset-First → I2I-Startframe → I2V)
- Forasoft Quality/Cost-Gates (01.06.2026): https://www.forasoft.com/learn/ai-for-video-engineering/articles-ai/quality-cost-c2pa-eu-ai-act-disclosure-engineering — QC-Schichten + Retry-Cap
- AIGVE-MACS (CVPR 2026 Workshop): https://openaccess.thecvf.com/content/CVPR2026W/VGBE/papers/Liu_AIGVE-MACS_Unified_Multi-Aspect_Commenting_and_Scoring_Model_for_AI-Generated_Video_CVPRW_2026_paper.pdf — +53,5 % durch Feedback-Regenerierung
- fal-MCP-Doku: https://fal.ai/docs/documentation/setting-up/mcp ; Wireflow-MCP-Überblick (02.08.2026): https://www.wireflow.ai/blog/best-ai-video-generation-mcp-tools-in-2026
