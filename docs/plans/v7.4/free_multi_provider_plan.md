# Plan — Kostenlose Multi-Provider-Videogenerierung (Analyse · Systementwurf · Umsetzung)

> **Status:** 🟡 Entwurf — Nutzerentscheide vom 2026-10-10 eingearbeitet; **P0 ohne Token ausgeführt** (§八), Token-Quota-Test ausstehend. Wartungsmodus: Produktionscode unverändert (ergänzt wurde nur `scripts/modelscope_p0_check.py`)
> **Datum:** 2026-10-10 · **Anlass:** Nutzeranfrage „tiefe Analyse und Erarbeitung eines Systems mit einem Plan, um kostenlose Videos bei mehreren Anbietern zu generieren"
> **Versionslinie:** v7.4 (Vorschlag — finale Einordnung beim Release-Entscheid gemäß `docs/dev/release_process.md`)
> **Grundlagen:**
> - Frische Anbieter-Recherche: `docs/dev/free_video_generation_research.md` (2026-10-10)
> - Markt-Landschaft + bereits umgesetzte Batches: `docs/plans/optimization-research/video_api_landscape_2026.md` (§2.3 Gratis-Lage, §五a Umsetzungsstand)
> - Existierende Provider-Abstraktion: `docs/plans/v7.1/video_provider_PRD.md` (🟢 implementiert)
> **Umfang:** Analyse + Systementwurf + Phasenplan. Umsetzung erst nach Freigabe, dann phasenweise (§五).

---

## 一、Ist-Analyse (aus dem Code gelesen, nicht rekonstruiert)

### 1.1 Das System ist zu ~70 % bereits gebaut

Die Anfrage „Videos kostenlos bei mehreren Anbietern generieren" trifft auf eine **fertige Provider-Infrastruktur**:

| Baustein | Stand | Beleg |
|---|---|---|
| `VideoProviderBase`-Vertrag (`submit_video` / `wait_for_video` / `resolve_image_ref` / `shutdown_event` / `capabilities`) | 🟢 v7.1 | `core/api/video_providers.py:212` |
| `VideoProviderCapabilities` (Referenzbilder, Seed, Negative-Prompt, Dauer-/Auflösungs-Snapping, First/Last-Frame, Preis) | 🟢 v7.2 R8 | `core/api/video_providers.py:192` |
| Fabrik `create_video_provider()` — Routing nach Modell-ID-Präfix („Modell wählen = Provider wechseln") oder `AGNES_VIDEO_PROVIDER` | 🟢 v7.1/v7.3 | `core/api/video_providers.py:540` |
| **agnes** (kostenlos, Default) mit U1–U8-Härtung: Queue-Full-Eigenbahn, Key-Rotation, adaptives Polling, 404-Intermediate-State | 🟢 v7.0 | `core/api/agnes_video.py:872` (Submit), `:1014` (Poll), `:132` (`AgnesQueueFullError`) |
| **fal.ai** (bezahlt): MiniMax H3 Max / Kling, Kostenabschätzung + Budget-Gate `AGNES_VIDEO_BUDGET_USD` | 🟢 v7.2 R8 | `core/api/video_providers.py:252`, `:314` |
| Alle 5 Pipelines über die Fabrik verdrahtet (keine direkte `AgnesVideoAPI`-Instantiierung mehr) | 🟢 v7.1 | `simple_video.py:55`, `manuscript_video.py:159`, `poetry_video.py:89`, `anchor_video.py:90`, `creative/pipeline.py:91`; Aufrufstellen `multi_scene.py:336/:576/:697` |
| Kostenankündigung pipeline-seitig (`_announce_video_cost`) + `estimate_clip_cost_usd`-Hook | 🟢 v7.2 R8 | `multi_scene.py:415` |
| VLM-QC-Gate (läuft Provider-unabhängig über den **gratisen** Agnes-Chat) | 🟢 v7.2 Batch 2 | `core/quality/qc.py`, Phase 3.5 in `MultiScenePipeline.run()` |
| KeyRing (Multi-Key, 429-Rotation) + Doppel-Token-Bucket (shared + Video-Submit), Skalierung mit Key-Anzahl | 🟢 v5.0 | `core/api/key_manager.py:26`, `core/api/rate_limiter.py:225/:239` |
| Mock-Regression über Klassen-Symbol-Patching (Lazy-Import-Punkt in der Fabrik absichtlich erhalten) | 🟢 | `tests/mock_regression/conftest.py:56-67`, `video_providers.py:571` |

### 1.2 Was für „kostenlos + mehrere Anbieter" fehlt

1. **Nur zwei Provider existieren** — agnes (gratis) und fal (bezahlt). Der Katalog (`get_video_provider_catalog()`, `video_providers.py:601`) kennt nur `["agnes", "fal"]`.
2. **Keine Failover-/Fallback-Kette:** Ein Lauf nutzt genau einen Provider. Schluss das agnes-Queue-Sättigungsszenario (U1: `video_queue_full` kann > 12 min dauern) gibt es keinen automatischen Ausweich-Provider — die Landschaftsrecherche hat das schon als „konsequente nächsten Schritt" benannt (Landscape §2.3).
3. **Keine gratisen Zusatz-Provider:** ModelScope (Wan i2v) und lokales ComfyUI (Wan 2.2 / LTX) aus der frischen Recherche sind nicht angebunden.
4. **Kein Quoten-/Health-Bewusstsein pro Provider** (nur agnes hat dedizierte Limiter-Buckets).

---

## 二、Ziele & Nicht-Ziele

**Ziele**

- G1: Kostenlose Videogenerierung über **mehrere** Anbieter, automatisiert aus den bestehenden 6 Task-Typen heraus.
- G2: Ausfallsicherheit: wenn der Default-Provider (agnes) drosselt/ausfällt, weicht das System automatisch aus — ohne dass ein Clip doppelt bezahlt (Quota) oder ein Task bricht.
- G3: Minimal-invasiv: Pipeline-Aufrufstellen **null** Änderungen (Vertrag bleibt identisch); agnes bleibt Default; Mock-Regression bleibt unverändert grün.
- G4: Konsistenz erhalten: Keyframe-first + Character-Ref + QC-Gate (MV-Standard, `docs/dev/mv_style_consistency.md`) funktionieren provider-unabhängig.
- G5: Testbar: neue Provider über denselben Lazy-Import-Patch-Punkt mockbar wie agnes.

**Nicht-Ziele (bewusst ausgeschlossen)**

- N1: **Keine Automatisierung der Web-Gratisdienste** (Kling/Hailuo/Pixverse/Pika): keine offizielle Gratis-API, Automatisierung würde ToS verletzen → nur „manueller Hybrid" (Tier C, §三.3).
- N2: R6/R7-Beschlüsse gelten weiter: HF-Spaces-ZeroGPU/Kaggle sind **kein** Generierungspfad (nur Re-Eval, wenn sich Quotenlage ändert).
- N3: Keine Erweiterung der bezahlten fal-Funktionen (r2v-Multi-Reference etc.) — separates Thema.
- N4: Kein UI-Pflichtumfang: Konfiguration env-first; Frontend-Auswahl ist optionaler Phase P4.
- N5: TTS/Untertitel-Pipeline bleibt unangetastet (Wortzeitstempel sind Source of Truth, AGENTS.md §6.9).

---

## 三、Anbieter-Analyse (Tiefe: kostenlos realistisch available)

### 3.1 Harter Marktfakt zuerst

**Kein großer Anbieter hat 2026 noch einen API-Gratis-Tier** (Google, xAI, MiniMax, Kling, Pika, Runway, Luma: „not available", Stand 30.09.2026, Landscape §2.3). Gratis-Reste (Kling-2.6-Monatscredits, Google Flow 50 Credits/Tag, Runway 125 einmalig) sind **web-only, nicht per API**. Die Gratis-Agnes-API ist das Alleinstellungsmerkmal des Projekts und bleibt Default.

„Kostenlos bei mehreren Anbietern" bedeutet daher realistisch: **agnes + ModelScope (Wan)** als automatisierte Kette — lokales ComfyUI entfällt (keine GPU, Nutzerentscheid 2026-10-10) —, plus **manueller Hybrid** über Web-Credits für Hero-Shots.

### 3.2 Bewertungsmatrix

Kriterien: Kosten · offizielle API/Automatisierbarkeit · i2v/Referenzbilder · Stabilität · Wasserzeichen · ToS-Risiko · Integrationsaufwand · Projektvorbeschluss.

| Anbieter | Kosten | API | i2v/Ref | Stabilität/Queue | Wasserzeichen | Urteil |
|---|---|---|---|---|---|---|
| **agnes** (ist) | gratis | ✅ eigenes Protokoll | 1 Ref / Keyframes→Ref-Fallback (2.5) | Queue-Sättigung zu Spitzenzeiten (U1) | nein | **Default, bleibt** |
| **ModelScope API-Inference** (Wan i2v/t2v) | gratis Token; berichtet ~2000 API-Calls/Tag pauschal, **pro Modell deutlich weniger**, Video-Quota nicht offiziell publiziert | ✅ **P0 empirisch**: `POST /v1/videos/generations` + Poll `GET /v1/tasks/{id}` vorhanden (§八) | Wan i2v = First-Frame (mit Token zu bestätigen) | ✅ Latenz gemessen: ~1,4–2 s/Request — sehr gut erreichbar | nein | **Tier A — erster neuer Provider**; ⚠️ Video-Modelle fehlen im öffentlichen Katalog → Token-Test entscheidet |
| **Lokales ComfyUI** (Wan 2.2 5B ≈ 8–12 GB VRAM quantisiert; LTX-Video ≈ 12 GB) | gratis (eigene GPU, Strom) | ✅ stabile lokale HTTP-API (`/prompt`, `/history/{id}`, `/upload/image`, `/view`) | First-Frame ✅; IP-Adapter/LoRA für Identität | keine fremde Queue; Renderzeit lokal (Minuten statt Sekunden) | nein | ⛔ **gestrichen** (keine GPU ≥ 12 GB, Nutzerentscheid) — Design bleibt als Beobachtungsposten dokumentiert (§4.2) |
| BotHub-API (RU-Aggregator: Kling/Veo/Seedance) | Tageslimit gratis + „kopische" Preise | ✅ | ✅ | Aggregator-Qualität schwankt | je Modell | Tier B (optional, P4+) |
| Google AI Studio (Veo) | limitiert gratis, **konto-/regionsabhängig** | ✅ | ✅ | ToS-Risiko für Pipeline-Nutzung unklar | ja (Seed) | Tier B, zurückgestellt |
| HF-Spaces ZeroGPU (gradio_client) | Demo-Quota | halb (Gradio-Scraping-Niveau) | je Space | R6/R7: verworfen | — | **bleibt verworfen** (N2) |
| Kling/Hailuo/Pixverse Web | Tagescredits (~10–20 Clips/Tag kumuliert) | ❌ web-only | manuell: Keyframe als First Frame hochladen | langsame Peaks | **ja (Free-Tier)** | **Tier C — manuell**, kein Code |

### 3.3 Konsequenz für das System

Die Kette ist eine **Notfall-/Kapazitätsleiter**, kein Round-Robin: `agnes` → `modelscope` → `fal` (letztes Glied gegen Budget-Freigabe; das ComfyUI-Glied entfällt — keine GPU ≥ 12 GB, Nutzerentscheid 2026-10-10). Pro Task gilt **Stickiness** (§四.4): wer einmal ausgewichen ist, bleibt für den ganzen Task auf dem Ausweich-Provider — das schützt den MV-Konsistenzstandard (ein Stil/Look pro Video, kein Provider-Mix innerhalb eines Films).

---

## 四、Systementwurf

### 4.1 Architekturübersicht

```
Pipelines (5×, unverändert: self.video_api / self.video_generator)
        │
        ▼
create_video_provider(api_key, default_model, shutdown_event)     [video_providers.py:540, erweitert]
        │
        ├─ Modell-Präfix "fal-ai/*" | "minimax/*"  → FalVideoProvider            (bezahlt, Budget-Gate, unverändert)
        │
        └─ sonst: AGNES_VIDEO_PROVIDER_CHAIN (neu; Default "agnes" = exakt heutiges Verhalten)
                 │
                 ▼
           FailoverVideoProvider([AgnesVideoAPI, ModelScopeWanProvider, FalVideoProvider(Budget-Gate)])
                 — implementiert denselben VideoProviderBase-Vertrag
                 — delegiert submit/wait; weicht nur an Submit-Grenzen aus (§4.4)
```

Neue Provider implementieren `VideoProviderBase` (`video_providers.py:212`) — kein neues Interface, keine Pipeline-Änderung.

### 4.2 Neue Provider im Einzelnen

**`ModelScopeWanProvider`** (gratis Hosted-API, Drop-in-nächster Kandidat laut Recherche)

- Konfiguration: `MODELSCOPE_API_TOKEN` (env-first, analog `FAL_KEY`-Muster — Bezahlt-/Fremdschlüssel nicht in config.json, PRD-Konvention v7.1 §二) oder maskiert in `config.json`.
- Ablauf (P0-empirisch bestätigt, §八): `POST {BASE}/v1/videos/generations` (Bearer-Token; Body: `model` + `prompt`, i2v zusätzlich Bild-Referenz — exakter Feldname mit Token verifizieren) → `task_id` → Poll `GET {BASE}/v1/tasks/{task_id}` bis `SUCCEEDED`/`FAILED` → Video-URL → `VideoOutput(fmt="url")`.
- **Fehler-Quirk (P0, wichtig für die Implementierung):** Auth-/Quota-Fehler kommen als **HTTP 500 mit Body-Code 401** zurück (`{"errors":{"code":401,…},"request_id":…,"status":"FAILED"}`). Klassifikation daher **immer über den Body-Code**, nie über den HTTP-Status allein (gleiches Prinzip wie `_upstream_error`, `agnes_video.py:66`).
- `resolve_image_ref()`: lokale Bilder hochladen bzw. bereits vorhandene öffentliche URL wiederverwenden (agnes-URL-Cache `ref + ".url"`, `agnes_video.py:332-364`, ist bewusst kompatibel: eine einmal hochgeladene öffentliche URL kann der Folge-Provider direkt referenzieren, solange sie < 1 h alt ist).
- Eigenes Limiter-Bucket (§4.5); `capabilities` mit `price_usd_per_second = 0.0` (gratis) und i2v-only-Flag, falls t2v-Quote zu knapp ist. ⚠️ **P0-Vorbehalt:** Im öffentlichen `/v1/models`-Katalog (Stand 2026-10-10) tauchen **keine Video-Modelle** auf — ob Wan i2v via API-Inference frei verfügbar ist, entscheidet der Token-Test (`scripts/modelscope_p0_check.py --submit`); die Rate-Limit-Header (`modelscope-ratelimit-*-remaining`) fließen in den Tageszähler ein.

**`ComfyUIProvider`** (lokale GPU, volle Unabhängigkeit) — ⛔ **durch Nutzerentscheid 2026-10-10 gestrichen (keine GPU)**; Entwurf bleibt archiviert für den Fall, dass sich die Hardware-Lage ändert:

- Konfiguration: `COMFYUI_API_URL` (z. B. `http://127.0.0.1:8188`), `COMFYUI_WORKFLOW` (Template-Key, Default `wan22_i2v`), optional `COMFYUI_MIN_FREE_VRAM_MB`.
- Ablauf: Workflow-Template (JSON pro Modellfamilie: Wan 2.2 5B / LTX) + Prompt/First-Frame/num_frames injizieren → `POST /prompt` → `prompt_id` → Poll `GET /history/{prompt_id}` → Output via `GET /view` → `VideoOutput(fmt="file")` (lokal, kein Download).
- `resolve_image_ref()`: `POST /upload/image` (funktioniert auch bei Docker-Deploy per HTTP, kein Pfad-Mapping nötig).
- Health-Gate: `GET /system_stats` beim Fabrik-Bau; VRAM zu klein → Provider wird in der Kette als *nicht wählbar* markiert (kein Harter Fehler, agnes läuft weiter).
- Wiederverwendung der bestehenden Frame-Logik (`_get_frame_config`, `agnes_video.py:444`) für Dauer→num_frames/FPS-Snapping.

### 4.3 FailoverVideoProvider (das eigentliche neue Systemstück)

- Baut die Kette aus `AGNES_VIDEO_PROVIDER_CHAIN` (Reihenfolge = Priorität); einzelner Eintrag `agnes` → Verhalten **identisch heute** (kein Wrapper-Overhead).
- **Failover nur an Submit-Grenzen** — auslösende Bedingungen:
  - `AgnesQueueFullError` (Queue-Budget `AGNES_VIDEO_QUEUE_RETRY_SECONDS` erschöpft, `agnes_video.py:709`),
  - Submit-`RetriesExhausted` / harter Submit-Fehler,
  - Provider-spezifische Quota-/Auth-Fehler (z. B. ModelScope-Tageslimit erreicht).
- **Kein Failover mitten im Polling.** Begründung: `is_remote_video_failure`-Semantik (`agnes_video.py:162`) — bei Timeout/Netzabbruch läuft der Remote-Job evtl. weiter; ein Zweit-Submit würde Quota verschwenden. Gilt unverändert für alle Provider der Kette.
- **Nicht auslösend:** `VideoTaskCancelled` (User-Stop) durchreicht die Kette sofort.
- **Task-Stickiness:** Nach dem ersten Failover bleibt der Task auf dem neuen Provider (Konsistenz, §3.3); Stickiness-State im Task-Prozess-RAM + Log. Restart-Resume läuft über die bestehenden task.json-Mechaniken (video_id bleibt provider-lokal gültig).
- **UX:** neuer `progress_callback`-Event `"provider_failover"` (gleiche Callback-Kultur wie `"queue_full"`, `agnes_video.py:736`) → Frontend kann „agnes-Queue voll → weiche auf ModelScope aus" anzeigen; i18n-Schlüssel in 22 Sprachen (AGENTS.md §九).
- **Beobachtbarkeit:** `error_collector` bekommt ein `provider`-Feld; Logs `[VideoProvider:modelscope]` etc.; Diagnose-Endpoint zeigt die aktive Kette + letzten Failover-Grund.

### 4.4 Referenzbild-Behandlung über Provider-Grenzen

Die Kette hält **immer die Original-Lokalpfade** und lässt jeden Provider frisch `resolve_image_ref()` laufen. Optional-Optimierung (nicht P1-Pflicht): eine bereits von agnes hochgeladene, < 1 h alte öffentliche URL (`.url`-Sidecar-Cache) wird an den Folge-Provider durchgereicht, statt neu hochzuladen — spart einen Upload, koppelt aber an agnes-Verfügbarkeit.

### 4.5 Konfiguration (env + config.json)

| Variable | Default | Bedeutung |
|---|---|---|
| `AGNES_VIDEO_PROVIDER_CHAIN` | `agnes` | Kommaliste, z. B. `agnes,modelscope,fal`; ein Eintrag = heutiges Verhalten; fal-Glied nur wirksam bei `AGNES_VIDEO_BUDGET_USD` > 0 |
| `AGNES_VIDEO_PROVIDER` | `agnes` | bleibt (Legacy-Einzelschalter, wie heute) |
| `MODELSCOPE_API_TOKEN` | — | Gratis-Token (env-first; alternativ maskiert in config.json) |
| `MODELSCOPE_VIDEO_MODEL` | P0 | Wan-i2v-Modell-Id laut P0-Verifikation |
| `MODELSCOPE_DAILY_BUDGET` | P0 | optionaler lokaler Tageszähler, schützt die unbekannte Server-Quota |
| ~~`COMFYUI_API_URL` / `COMFYUI_WORKFLOW` / `COMFYUI_MIN_FREE_VRAM_MB`~~ | — | ⛔ **entfallen** (P2 gestrichen — keine GPU ≥ 12 GB, Nutzerentscheid 2026-10-10) |

Rate-Limiting: neue Provider-fabrik-Funktion `get_provider_limiter(provider_id, rate)` in `core/api/rate_limiter.py` (gleiches Token-Bucket-Muster, `rate_limiter.py:96`) — ModelScope und ComfyUI bekommen eigene Buckets, konfigurierbar, konservativ vorbelegt.

### 4.6 Katalog & UI

`get_video_provider_catalog()` (`video_providers.py:601`) erweitern: `choices` + Einträge mit `"free": true/false` und Kurzhinweis zur Quota. Das Frontend-Dropdown (P4, optional) rendert das Gratis-Badge server-seitig mitgeliefert — keine Preis-/Modellpflege im UI (gleiches Muster wie fal-Katalog).

### 4.7 Konsistenz & Qualität (MV-Standard)

- Keyframes/Character-Sheets entstehen **weiterhin über die gratis agnes-Bild-API** (i2i + Character-Ref) — unabhängig davon, welcher Video-Provider den Clip rendert. First-Frame-i2v ist bei Wan und ComfyUI-Workflows gegeben ⇒ Storyboard-Kompatibilität laut Recherche („nimmt Keyframe als First Frame") direkt erfüllt.
- QC-Gate (`core/quality/qc.py`, gratis Agnes-Chat) läuft Provider-unabhängig und fängt Stildrift des Ausweich-Providers ab; bei QC-Fail gilt der bestehende Regen-Pfad (gleicher Provider, ≤ 1 Auto-Regenerierung).
- Negative-Prompt „i2v 统一" nur dort durchreichen, wo `capabilities.supports_negative_prompt` = true (Flag existiert bereits).

### 4.8 Testbarkeit (Regressionssicherheit)

- Fabrik-Behaltung: neue Provider werden wie der agnes-Zweig **zum Aufrufzeitpunkt** importiert (`video_providers.py:571`-Muster) ⇒ `monkeypatch`-Punkte bleiben.
- `tests/test_video_providers.py` erweitern (Stub-Injection via `sys.modules`, kein Netz — fal-Präzedenz): ModelScope Submit/Poll/Snap/Quota-Failover, ComfyUI `/prompt`→`/history`→`/view` (Fake-HTTP), Kette: Reihenfolge, Stickiness, „kein Failover bei Poll-Timeout", Cancel-Durchreichung, Budget.
- `tests/mock_regression/conftest.py` (`:56-67`) um Mock-Symbole der neuen Provider erweitern; bestehende 14-Szenen-Regression bleibt unverändert grün (Default-Kette = `agnes`).

---

## 五、Umsetzungsplan (Phasen, je unabhängig freigebbar)

| Phase | Inhalt | Akzeptanzkriterien | Aufwand |
|---|---|---|---|
| **P0 — Validierung (Go/No-Go)** | ✅ Erreichbarkeit, Routen, Auth-Mechanik **gemessen** (§八, `scripts/modelscope_p0_check.py`); ausstehend: Token anlegen + authentifizierter Katalog-Check + EIN T2V/I2V-Task zur Quota-/Schema-Messung | Messprotokoll §八 (teils gefüllt); Go/No-Go je Provider schriftlich | Rest: ~0,5 Tag |
| **P1 — ModelScopeWanProvider** | Klasse + Capabilities + Fabrik-Anschluss + Limiter-Bucket + Konfiguration | Unit-Tests hermetisch grün; manueller 1-Clip-Lauf über `/api/tasks/simple` mit `provider_chain=modelscope`; Mock-Regression unverändert grün | 2–3 Tage |
| ~~**P2 — ComfyUIProvider**~~ | ⛔ **entfallen** (Nutzerentscheid 2026-10-10: keine GPU ≥ 12 GB); Beobachtungsposten, falls sich die Hardware-Lage ändert | — | — |
| **P3 — FailoverVideoProvider** | Kette, Submit-Grenzen-Failover, Stickiness, `provider_failover`-Event + i18n (22 Sprachen), error_collector/Diagnostics | Simulationstest: agnes-Queue-Full-Injection → Clip entsteht über ModelScope; Cancel bricht nicht auf alten Provider zurück; Frontend-Build + `scripts/i18n_check.py` grün | 2–3 Tage |
| **P4 — bestätigt** | Katalog/Badge, Frontend-Provider-Auswahl pro Task; Keyframe-Export-Paket für manuelle Tier-C-Dienste (ZIP je Szene: Keyframe + Prompt + Empfehlung) | UI-Roundtrip; Export manuell nachvollziehbar | 1–2 Tage |

**Gesamt: ~5–9 Personentage** (ohne das gestrichene P2). P0 entscheidet, ob P1 gebaut wird — der Plan bricht hier bewusst früh, statt auf unbestätigte Quoten hin zu implementieren.

---

## 六、Risiken & Gegenmaßnahmen

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| ModelScope-Video-Quota intransparent / änderbar | Kette fällt häufiger durch als erhofft | P0-Messung vor Bau; lokaler Tageszähler; agnes bleibt Default — Kette ist Nur-Gewinn |
| CN-Netzroute/Latenz | Langsame Submits/Polls | Eigene Timeout-/Retry-Knobs; Provider optional; Abwahl per env |
| Lokale Renderzeit (17-s-720p-Clip in Minuten statt Sekunden) | Pipeline wirkt „hängend" | `progress_callback` mit lokalen Render-Fortschritt füttern; ComfyUI eher für Batch/Offline |
| Stildrift bei Provider-Wechsel innerhalb eines Films | MV-Konsistenz leidet | Task-Stickiness (§3.3/§4.3) + QC-Gate + gleiche Keyframes als First Frame |
| Quoten-/ToS-Fallen (Veo-Regionallock, Webdienst-Automatisierung) | Rechtliches/funktionales Risiko | Tier B zurückgestellt; Tier C strikt manuell (N1) |
| Wartungsmodus-Scope-Creep | Zu großes Inkrement | Phasen einzeln freigebbar; P4 optional; kein Contract-Break (G3) |

---

## 七、Entscheidungen (Nutzer, 2026-10-10) & Rest-Offenpunkte

| # | Punkt | Entscheidung / Stand |
|---|---|---|
| 1 | GPU ≥ 12 GB (ComfyUI-Phase P2) | **Nein** → P2 gestrichen, bleibt Beobachtungsposten |
| 2 | ModelScope-Zugang praktikabel? | **„Probiere es aus”** → P0 mit Token ausgeführt: Erreichbarkeit sehr gut (auch auf dem .ai-Host: 0,7–2 s/Request), Video-Submit + Task-Polling auf **beiden Portal-Hosts** verifiziert (§八). **Blocker erkannt:** Token stammt vom internationalen Portal (modelscope.ai) und verlangt die **Alibaba-Cloud-Account-Bindung** — ein kontoseitiger Schritt, danach Rerun des Skripts |
| 3 | fal als letztes Kettenglied gegen Budget + P4 Frontend-Auswahl | **Ja zu beidem** → Kette `agnes,modelscope,fal`; P4 bestätigt |
| 4 | Versionslinie v7.4 | bleibt Vorschlag, finale Einordnung beim Release-Entscheid |

---

## 八、Quellen & Messprotokoll (P0 trägt hier nach)

- Frische Recherche: `docs/dev/free_video_generation_research.md` (2026-10-10) — Anbieterliste, ModelScope/ComfyUI-Einschätzung, manueller Hybrid.
- Markt + Gratis-Lage: `docs/plans/optimization-research/video_api_landscape_2026.md` §2.3 (keine API-Gratis-Tiers mehr), §2.4 (Self-Hosting-Beschluss), §五a (umgesetzte Batches).
- Provider-Vertrag/PRD: `docs/plans/v7.1/video_provider_PRD.md`; Upstream-Verhalten: `docs/dev/agnes_video_upstream_behavior.md`; MV-Standard: `docs/dev/mv_style_consistency.md`.
- Web-Verifikation 2026-10-10: [modelscope.ai](https://www.modelscope.ai) (Gratis-Tier, „API-Inference Usage Limits“, berichtet ~2000 Calls/Tag pauschal) · Async-Muster Wan-Video (Submit→task_id→Poll): [Alibaba Cloud Model Studio](https://www.alibabacloud.com/help/model-studio) · Client-Beispiel `POST /v1/videos/generations` + `GET /tasks/{task_id}`: [CSDN — MiniMax-H3-Batchgenerierung](https://blog.csdn.net) · Rate-Limit-Header: [GitHub LAVARONG/ImageForge](https://github.com/LAVARONG/ImageForge) · Zhihu-Tutorial „Wan3.0-Video“ (zhihu.com, Async-Modus mit task_id)

### P0-Messprotokoll (2026-10-10, Betreiber-Maschine, ohne Token)

**Erreichbarkeit/Latenz:**

| Ziel | HTTP | DNS | TCP | TLS | gesamt |
|---|---|---|---|---|---|
| `www.modelscope.cn` | 302 | 46 ms | 78 ms | 673 ms | 1,87 s |
| `api-inference.modelscope.cn/v1/models` | 200 | 46 ms | 370 ms | 1,72 s | 2,05 s |

Skript-Lauf (Stdlib, 2× `GET /v1/models`): 1,36 s / 1,97 s. **Die CN-Route ist von dieser Maschine aus unkritisch.**

**Routen-Probe (401/400/500-auth = Route existiert, 404 = fehlt):**

| Route | Ergebnis | Befund |
|---|---|---|
| `GET /v1/models` | 200 | öffentlicher Katalog — **keine Video-Modelle** (nur LLMs + Qwen-Image-Edit) |
| `POST /v1/chat/completions` | 400 | existiert |
| `POST /v1/images/generations` | 401 | existiert (Bildgenerierung über API-Inference bestätigt) |
| `POST /v1/videos/generations` | **500\*** | **existiert** — \*Body: `{"errors":{"code":401,"message":"Authentication failed, please make sure that a valid ModelScope token is supplied."},"request_id":"…","status":"FAILED"}` |
| `GET /v1/tasks/{task_id}` | **401** | **existiert** → das ist der Polling-Endpoint |
| `POST /v1/videos`, `GET /v1/tasks`, `/v1/asynctasks`, `/v1/video/generations` | 404 | existieren nicht |

**Fehler-Quirk (wichtig für P1):** Auth-/Quota-Fehler kommen als **HTTP 500 mit Body-Code 401** zurück — Klassifikation immer über den Body-Code, nie über den HTTP-Status allein.

**Go/No-Go-Stand:**

- **ModelScope: bedingt Go.** Erreichbarkeit ✓, Video-Endpoints ✓, Auth-Mechanik ✓. **No-Go-Kriterium:** der Token-Test zeigt keine frei nutzbaren Video-Modelle/Quote → dann entfällt P1 (und damit der einzige neue Gratis-Hosted-Provider; die Kette reduziert sich auf `agnes,fal`).
- **ComfyUI: No** (keine GPU, Nutzerentscheid 2026-10-10).
- **fal: Go** (bereits implementiert — übernimmt nur die neue Rolle als letztes Kettenglied).

**Token-Phase (2026-10-10, Token lag vor):**

- **Portal-Split entdeckt:** Der Token ist auf dem **internationalen Portal modelscope.ai** erstellt — der China-Host `api-inference.modelscope.cn` lehnt ihn überall mit schlichtem „Authentication failed" ab (auch Chat/Bild). International existiert ein eigener Host: **`api-inference.modelscope.ai`** (Katalog: 33 Modelle; Erreichbarkeit schneller als .cn: 0,7–1,1 s/Request).
- **Identische API-Oberfläche auf .ai:** `POST /v1/videos/generations` (gleicher 500+401-Body-Quirk) und `GET /v1/tasks/{id}` (401) existieren — die komplette Video-Kette ist auch international vorhanden.
- **Einziger Blocker (kontoseitig):** Der .ai-Host antwortet überall mit `{"code":401,"message":"Please bind your Alibaba Cloud account before use. You can bind it at: https://modelscope.ai/my/settings/account"}` — der Token wird **erkannt**, aber API-Inference verlangt die **Alibaba-Cloud-Account-Bindung**. Deckt sich mit der Recherche („nach Konto-Bindung und Verifizierung").
- **Video-Modelle in keinem Katalog sichtbar** (.cn authentifiziert: 35 Modelle; .ai: 33) — möglicherweise erst nach der Bindung freigeschaltet; finale Antwort nach dem Rerun.

**Go/No-Go bleibt: bedingt Go.** Infrastruktur ✅ (Hosts, Routes, Quirks dokumentiert); der Blocker ist ein einziger kontoseitiger Schritt, kein Architekturrisiko.

**Rest-Schritt (nach der Bindung):**

```
# 1) https://modelscope.ai/my/settings/account → Alibaba-Cloud-Account binden
set MODELSCOPE_API_TOKEN=ms-...
python scripts/modelscope_p0_check.py --submit                            # 1 T2V-Task + Polling + Quota-Header (Host-Default jetzt .ai)
python scripts/modelscope_p0_check.py --submit-i2v --image-url <öffentliche PNG-URL>
# CN-Portal-Token stattdessen: --base https://api-inference.modelscope.cn
```

Ergebnisse (Katalog-Video-Modelle nach Bindung, tatsächliche Video-Quote, i2v-Feldschema) hier nachtragen. Rohdaten: `docs/plans/v7.4/p0_modelscope_logs/`.
