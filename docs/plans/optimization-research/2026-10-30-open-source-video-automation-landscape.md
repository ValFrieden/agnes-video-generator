# Open-Source-Landschaft: Automatisierung der Videoproduktion

**Stand:** 2026-10-30 · **Methode:** GitHub-Suche (Themen + Sterne), skills.sh,
offizielle MCP-Registry; Sterne und Lizenzen jeweils über die GitHub-API nachgeprüft
(`repos/{owner}/{repo}` bzw. `/license`), nicht aus den Beschreibungen übernommen.

**Zweck:** Entscheidungsgrundlage, ob wir Storyboard-Board, Charakter-Karten und
QC-Gate selbst bauen oder übernehmen. Ergebnis: übernehmen als *Methodik*, nicht als Code.

---

## 1. Was tatsächlich verwendbar ist (MIT / Apache)

| Repo | ★ | Lizenz | Umfang | Urteil |
|---|---|---|---|---|
| `zenstory-ai/drama-skills` | 3,6k | MIT | 11 Skills: `write` → `novel-analyze` → `assets` → `storyboard` → `image-prompts` → `video-prompts` → `produce` → `edit` → `review` | **übernommen** nach `.agents/skills/short-drama*` |
| `HBAI-Ltd/Toonflow-app` | 19,9k | MIT | Roman → animierte Serie, Infinite Canvas, 3-Layer-Agenten | Referenz für Agenten-Zerlegung |
| `HITsz-TMG/VideoClaw` | 1,9k | MIT | Konzept → Script → Assets → Storyboard → Referenzen → Video → Schnitt; Mehr-Episoden-Fortsetzung | **nächster Treffer** zum geplanten P1-Objektmodell |
| `ChrisChen667788/wind-comic` | 704 | MIT | Ein Satz/Novel → fertige Serie, Timeline, MP4-Export | Aufbau-Referenz |
| `Agions/kineo` | 133 | MIT | Multi-Agent, explizite „consistency anchors" | deckungsgleich mit unseren Continuity Locks |
| `dav-niu474/huobao-drama-ai` | 108 | MIT | Script → Charaktere → Storyboard → Bild/Video/TTS | Vergleichsmaßstab |
| `ZC89757/story-claw` | 31 | MIT | wie oben **plus VLM-Clip-Checks** | Vorbild für QC-Stufe 2 |
| `OpenX-Inc/flow` | 33 | MIT | Self-hosted Google-Flow-Alternative (Wan 2.2), „character bank", Last-Frame-Chaining | Vergleich zu `core/api/google_flow_engine.py` |
| `harry0703/MoneyPrinterTurbo` | 136k | MIT | Thema → Kurzvideo | dessen Audio-Methode nutzen wir bereits (AGENTS.md §6.6) |

## 2. Ausgeschlossen — Lizenz

| Repo | ★ | Lizenz | Grund |
|---|---|---|---|
| `ArcReel/ArcReel` | 5,9k | AGPL-3.0 | Copyleft würde unser MIT-Projekt infizieren |
| `waooAI/waoowaoo` | ~14k | CC BY-NC-SA / Elastic | nicht kommerziell bzw. Hosting eingeschränkt |
| `dramaclaw/dramaclaw` | 6,9k | Elastic 2.0 | Hosting-/Branding-Auflagen |
| `xhongc/ai_story` | 987 | CC BY-NC-SA | nicht kommerziell |
| `seme-org/open-director` | 121 | LGPL-3.0 | nur Muster; Linking-Frage vor jeder Übernahme klären |
| `liangdabiao/Seedance2-Storyboard-Generator` | 2,7k | keine | ohne Lizenz keine Übernahme |

## 3. MCP und skills.sh — Fehlanzeige

- **MCP-Registry** (`registry.modelcontextprotocol.io`): nur SaaS-Videogeneratoren
  (`MakeAIVideo` u. a.) gegen Bezahl-API. Kein Server zu Charakter-Konsistenz oder
  Storyboard-Orchestrierung. Eigener `tools/google-flow-browser-mcp/` bleibt der Weg.
- **skills.sh**: bester Treffer `ailabs-393/…@storyboard-manager` (1,4k Installationen),
  lokal bereits vorhanden. Alles weitere unter 100 Installationen, also unter der
  Empfehlungsschwelle.

## 4. Was wir daraus ziehen (und was nicht)

**Ziehen:**
1. `drama-skills` als Autoren-Methodik — importiert, siehe `.agents/skills/THIRD_PARTY_NOTICES.md`.
2. Deren drei Kerngedanken als erste Implementierung (unser eigener Code):
   *Identität vs. Variante*, *Continuity Lock* (minimale Nominalphrase, wortgleich im
   Prompt, maschinell prüfbar), *Review mit Blocker-IDs*. → `core/screenwriter/scenario_director.py`.
3. `VideoClaw`s Objektkette (Concept → Assets → Storyboard → Reference → Shot) als
   Vorlage für den Charakter-Karten-Schritt.
4. `story-claw`s VLM-Clip-Check als zweite QC-Stufe über dem 25/50/75-Kontaktbogen.

**Nicht ziehen:** ganze Plattformen (eigene UI + eigenes Datenmodell → dupliziert unsere
App statt sie zu erweitern), sowie alles unter AGPL/Elastic/NC (siehe §2).

## 5. Offene Punkte

- VLM-Clip-Check setzt ein Vision-Modell mit Bild-Input voraus; unser Chat-Client kann
  multimodal, ist aber im Betrieb nicht auf Bild-QC erprobt → erst messen, dann Gate.
- Lizenzprüfung gilt für den Stand 2026-10-30; vor jeder künftigen Code-Übernahme erneut
  prüfen (Lizenzen ändern sich).
