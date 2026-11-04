# Analyse: „Video Auto“ (10 YouTube-Anleitungen) → Was wir für VideoGenerator übernehmen

> Quelle: `D:\Projects\watch\Anleitungen nach YouTube Videos\Video Auto` (10 Videos, je transcript + video_analysis.md + Frames)
> Datum: 2026-10-22 · Status: Recherche, noch nichts implementiert

## 0. Was in den 10 Videos drinsteckt

| # | Video | Kern | Relevanz für uns |
|---|---|---|---|
| 1 | **I Fully Automated Google Flow Using Claude Code** | „Flow Studio“ – MCP + Panel für Google Flow: Charakter → Keyframes → Video → Voice → FFmpeg-Schnitt | ⭐⭐⭐ direkt (unser `tools/google-flow-browser-mcp`) |
| 2 | Google Flow: Kurzfilm gratis („The Last Signal“) | Charakter als Asset, Timeline-Fortsetzung, Video- vs. Charakter-Referenz, Bestätigung vor Generierung | ⭐⭐⭐ |
| 3 | Google Flow: EIN Charakter in allen Szenen, Lipsync | Ingredients-to-video, Frames-to-video, Extend, Objekt einfügen, natives Audio | ⭐⭐⭐ |
| 4 | Claude Code: eigener KI-Cutter in 7 Schritten | Claude = Regisseur; FFmpeg=Hände, Whisper=Ohren, Frames=Augen; Freigabe-Gates, Kosten-Kalkulation, Skills | ⭐⭐ Prozess |
| 5 | Claude Code änderte Schnitt für immer (15 Repos) | VideoUse, OpenMontage, Diffusion Studio, HyperFrames/Remotion, Awesome Claude Video Skills | ⭐⭐ Tools |
| 6 | Wie man Erstellung+Schnitt automatisiert (Opus 5.5) | 4 Automatisierungsstufen, TZ-Struktur, Aggregator-API, Avatar | ⭐ |
| 7 | Komplettschnitt in Claude Opus 5.5 | Motion-Design, AE-Projekt, Referenzen als Hebel | ⭐ |
| 8 | Dieses Video schnitt eine KI (DaVinci MCP) | HTML/SVG-Grafik → headless Chrome, SFX-Synthese, S-Log → FFmpeg + 3D-LUT, Musik nach Waveform | ⭐⭐ (LUT, Grafik) |
| 9 | GPT-6 Astra / Codex | Ordner-Prinzip, präzise Kritik, HyperFrames | ⭐ |
| 10 | „Wahnsinns-Schnitt gratis“ (OpenMontage) | Brandbook laden, 3 Feedback-Runden | ⭐ |

**Wichtig:** 6 von 10 Videos behandeln *Talking-Head-/YouTube-Schnitt* (Pausen/Versprecher schneiden). Das ist nicht unser Kerngeschäft (KI-Musikclips + Agnes-Pipelines). Wirklich wertvoll für uns sind **Flow-Automatisierung (1–3)** und einige **Prozess- und Post-Production-Muster (4, 5, 8)**.

---

## 1. Top-Empfehlungen (nach Nutzen / Aufwand)

### A. Start-/End-Frame-Kettung im Flow-MCP (hoch / mittel)
Flow Studio: Clip 1 = Start Bild 1 → Ende Bild 2; Clip 2 = **letzter echter Frame von Clip 1** → Ende Bild 3.
- Unser `flow_generate_video` (`tools/google-flow-browser-mcp/src/index.js:94`) hat nur `reference_images`, **keine `start_frame` / `end_frame`-Parameter**.
- Regel aus Video 1, deckt sich mit unserem Canon-Problem:
  - **Direkte Fortsetzung (gleicher Ort) → letzter Frame** als Start (Charakter-Lock verändert sonst die Umgebung).
  - **Ortswechsel → Charakter-Referenz/Character-Sheet** (Video 2 bestätigt: Video-Ref „lässt Location schwimmen“).
  - Letzter Frame muss das **Gesicht groß und klar** zeigen, sonst „rät“ der nächste Clip.
- Umsetzung: `ffmpeg -sseof -0.05 -i clip.mp4 -frames:v 1 last.png` + neue MCP-Parameter.

### B. Kosten-Guard vor jeder Videogenerierung (hoch / klein)
Flow Studio liest **vor** jedem Clip den Preis aus und bricht ab, wenn das Budget überschritten wird; Video 4: „Claude schickt erst eine Kalkulation und wartet auf Freigabe“.
- Wir haben `auto_confirm` (Bild default false, **Video default true!** → `index.js:103`). Vorschlag: Video-Default auf `false` + Preis/Guthaben aus der UI lesen + `max_credits` Parameter + `flow_credit_balance` Tool.
- Passt zur Regel „Einzelsegment-Freigabe“ im AGENTS.md.

### C. „Bilder zuerst, gratis iterieren“ formalisieren (hoch / klein, nur Doku/Skill)
Nano Banana / Standard-Bildmodell in Flow kostet 0 Credits (Autor: ~200 Bilder gratis), Video kostet. → Alle Fehler (Komposition, Gesicht, Stil) auf Keyframe-Ebene beheben. Unser Reference-Pipeline-Gesetz macht das schon fast — ergänzen um: **„Erst Plan der Keyframes beschreiben lassen → freigeben → generieren“** (Video 1, Prompt „Beschreibe jedes Bild, bevor du es erstellst“).

### D. Batch-Modus & Library-Re-Download (mittel / mittel)
Flow Studio: bis zu 50 Bild-Szenen in einem Rutsch (20 Bilder in ~30 s); Library durchsuchen und **ohne Neugenerierung** erneut herunterladen. Wir haben dutzende `scratch_dl_*.py`-Skripte genau dafür → ein sauberes `flow_library_list` / `flow_library_download` Tool würde sie ersetzen.

### E. Songtext-Alignment mit Whisper/WhisperX für Musikclips (hoch / mittel)
WhisperX wurde in `docs/plans/v5.0/whisperx_alignment_evaluation_DONE.md` verworfen, **weil es keine externen Stimmen gibt** — das gilt für die Agnes-TTS-Pipelines. **Für unsere Songs (`*.mp3` mit echtem Gesang) gilt es nicht.** Wort-Zeitstempel des Gesangs liefern:
- Szenenschnitte an Zeilen-/Phrasenwechseln (zusätzlich zur BPM-Sicherung),
- optionale Lyric-Untertitel / Karaoke-Overlay,
- Prüfung „Bild passt zur gesungenen Zeile“ im QC.
Lokal `faster-whisper` (gratis) reicht; Vocals vorher ggf. mit Demucs trennen.

### F. Einheitliches Color-Grading per 3D-LUT über alle Clips (mittel / klein)
Video 8: Farbe per FFmpeg + 3D-LUT. Veo-Clips schwanken zwischen Szenen farblich. `core/compositor/processor.py:168` kann `lut3d` bereits → für MV-Assemble-Skripte (`assemble_final_clip.py`, `scripts/assemble_begi_clip.py`) einen **Clip-LUT pro Song** als Pflichtschritt aufnehmen.

### G. 9:16-Version mit Gesichtsverfolgung (mittel / mittel)
Video 4: OpenCV/MediaPipe findet das Gesicht, Crop-Fenster folgt. OpenCV ist im Projekt vorhanden (insightface ebenfalls) → aus jedem 16:9-Clip automatisch eine Shorts/Reels-Version. Der Agent soll das nach jedem fertigen Clip **anbieten** (Trick aus Video 4).

### H. Retro-Loop: „Dialog analysieren → in Skill schreiben“ (hoch / klein)
Alle Autoren: Nach Freigabe eines Videos
`„Analysiere den ganzen Dialog zu diesem Clip und schreib in den Skill: Regeln, die funktioniert haben, und Fehler, die wir behoben haben.“`
Wir haben die Regel (Playbook §8), aber keinen festen Schritt. → Als letzten Punkt der Checkliste in Playbook §6 aufnehmen.

### I. Freigabe-Gates & konkrete Korrekturen (Prozess, klein)
- Rohschnitt **komplett mit Ton** ansehen (×2), erst dann Grafik/Overlays.
- Korrekturen nur mit Timecode + messbarer Aktion („bei 0:21 Titel größer, 0,5 s früher“), nie „mach schöner“.
- Finaler Render erst nach „Freigeben“. → Passt zu Manual-Mode/Checkpoints im Frontend.

### J. Gratis-TTS mit Stilanweisung via Google AI Studio (niedrig–mittel / mittel)
Flow Studio spricht über AI-Studio-API-Key (Gemini TTS) kostenlos, mit Regieanweisung („warm und ruhig wie ein Gute-Nacht-Erzähler, kleine Pausen“). Kandidat als zusätzlicher Provider neben `edge_tts` in `core/audio/tts.py` — Achtung: verliert die edge_tts-WordBoundary-Cues, also Untertitel-Alignment klären.

---

## 2. Google-Flow-Fakten zum Festhalten (Playbook §3 ergänzen)
- Credits (laut Videos, Stand Herbst 2026, Schwankungen zwischen Videos): ~50/Tag gratis; 10 s 720p-Clip ≈ 15 Credits (Video 1) bzw. 10–20 je nach Modell; **Style-Edit eines fertigen Clips = 40 Credits** (teurer als neu generieren!).
- Veo 3.1 Quality vs. Fast: „Unterschied für die meisten Aufgaben minimal“ → Fast bleibt Standard (bestätigt unsere 720p-/Kostenpolitik).
- **Extend** setzt Audio nur von der letzten Sekunde fort → leises Ende = leise Verlängerung.
- Timeline-„Plus“ (Fortsetzungsmodus) schlägt manchmal fehl und hat ein Szenenlimit → Plan B: vorheriges Video als Referenz.
- Einstellung „Bestätigung vor Generierung“ in Flow aktivieren.
- Natives Audio/Lipsync ist Beta; bei Fehlschlag werden Credits erstattet. Für uns bleibt: Song-Audio extern, Mund geschlossen (AGENTS.md-Regel).

## 3. Tools — Bewertung
| Tool | Urteil |
|---|---|
| **Flow Studio** = `github.com/GTAI-1/flow-mcp` (per Perplexity gefunden; Node 22+, Chrome, FFmpeg; Panel auf `127.0.0.1:8787`, Tabs Cast/Frames/Shots/Voice/Restyle/Cut; Ausgabe `~/flow-mcp-out`) | Code lesen und Ideen (Preis-Check, Presets, Library, Kettung) in unseren MCP übernehmen, **nicht** blind installieren (fremder Code steuert eingeloggtes Google-Konto) |
| faster-whisper / WhisperX | ✅ für Songtext-Alignment (E) |
| HyperFrames (HeyGen) / Remotion | 🟡 nur falls Titel/Lyric-Typografie gewünscht; Grafik als Code mit Alpha. Sonst Overkill |
| OpenMontage, VideoUse, Diffusion Studio, ShortKit, auto-editor | ❌ auf Talking-Head-Schnitt ausgerichtet; Ideen schon übernommen (Ducking, Freigabe-Gates) |
| Awesome Claude Video Skills, GSAP-Skills | 🟡 Katalog zum Stöbern, kein Bedarf jetzt |
| OpenCV / MediaPipe | ✅ für 9:16-Reframe (G) |
| Pexels / Mixkit | 🟡 Stock/SFX, für MV selten nötig |
| Higgsfield, ElevenLabs, Polza AI, OpenRouter | ❌ kostenpflichtig, widerspricht „Gratis-Modelle“-Ausrichtung |
| DaVinci-MCP | ❌ inoffiziell, erfordert installiertes Programm |

## 4. Bewusst NICHT übernehmen
- Pausen-/Versprecher-Schnitt, Kamera+Screencast-Wechsel, Klatsch-Synchronisation — kein Anwendungsfall.
- Nicht verifizierte Behauptungen der Videos („18 Stunden autonom“, „95 % der Cutter ersetzt“), Werbeblöcke, VPN/Zahlungstricks.
- Video 1 nennt das Videomodell „Omni Flash“ — Name aus Transkript, nicht verifiziert.

## 4b. Ergänzungen aus Perplexity-Recherche (2026-10-22, Quellen unten — vor Umsetzung gegenprüfen)

1. **Offizielle Veo-3.1-API statt Browser-Automatisierung.** Gemini API und Vertex AI unterstützen Veo 3.1 mit **Startbild + `lastFrame`** und **bis zu 3 Referenzbildern** (ai.google.dev/gemini-api/docs/veo, Vertex-Doku „first and last frames“). Das würde die fragilen CDP-/`scratch_*`-Skripte ersetzen. Haken: API wird **pro Sekunde bezahlt** (nicht über Flow-Abo-Credits) → widerspricht der Gratis-/Minimalkosten-Politik; als optionaler Provider in `core/api/video_providers.py` sinnvoll. Hinweis aus der Recherche: Gemini-API-*Preview*-Modell-IDs von Veo 3.1 sollen am 22.10.2026 abgeschaltet worden sein; Vertex listet stabile `*-001`-IDs → aktuelle Modell-ID prüfen.
2. **Flow-Credits (Drittquelle, nicht offiziell):** Veo 3.1 Lite 10 (Ultra 5), Fast 20 (Ultra 10), Quality 100 pro Generierung. **Ingredients/References gibt es in Flow nur für Lite und Fast, nicht für Quality** (support.google.com/flow/answer/16352836) → für referenzgetriebene Konsistenz nie Quality wählen. Lite als günstigste Option für Entwürfe testen.
3. **Konsistenz-Regel bestätigt:** Ingredients/Charakter für getrennte Shots, First/Last-Frame für geplante Übergänge, Extend nur innerhalb einer Szene — deckt sich mit Punkt A.
4. **Songtext-Alignment konkret:** Da wir die Texte haben (`Мои стихи/`, Szenarien), **Forced Alignment mit bekanntem Text** statt Transkription: `stable-ts` (`model.align(audio, text)`) oder WhisperX mit korrigiertem Transkript; optional Demucs-Vocal-Stem vorher — beides vergleichen, Separation kann Konsonanten verwischen. Melismen/Ad-libs manuell prüfen.
5. **Beat/Downbeat:** `CPJKU/beat_this` als moderner Tracker (optional madmom-DBN, madmom von GitHub installieren); auf **Downbeats** (Taktanfänge) schneiden, nicht nur Beats; Halb-/Doppeltempo-Fehler prüfen. Ergänzt die BPM-Rechnung im `ScenarioDirector`.
6. **Color-Matching:** erst Belichtung/Farbraum normalisieren, dann gemeinsamer Look per `.cube`/`lut3d` oder `haldclut`; `color-matcher` (Python) für Referenz→Clip-Transfer testen, aber Flackern vermeiden (einmal pro Clip, nicht pro Frame).
7. **9:16-Reframe:** Crop-Mittelpunkt glätten, Tracking an Schnitten zurücksetzen, Ränder für Hände/Objekte (roter Ballon!) lassen.

Quellen: ai.google.dev/gemini-api/docs/veo · docs.cloud.google.com (Veo 3.1, first/last frames) · support.google.com/flow/answer/16352836 · lazykiwi.ai/blog/google-flow-veo-tutorial · github.com/GTAI-1/flow-mcp · github.com/m-bain/whisperX · github.com/jianfch/stable-ts · github.com/CPJKU/beat_this

## 5. Vorgeschlagene Reihenfolge
1. **B** Kosten-Guard + Video-Default `auto_confirm=false` (klein, schützt Credits)
2. **A** Start/End-Frame-Parameter + Last-Frame-Extraktion
3. **C + H + I** Playbook/Checkliste ergänzen (nur Doku)
4. **E** Songtext-Forced-Alignment (stable-ts/WhisperX) + Downbeats (beat_this)
5. **F** LUT-Schritt im Assemble, **G** 9:16-Reframe
6. **D** Library-Tools (räumt `scratch_dl_*` auf), Code von `GTAI-1/flow-mcp` als Vorlage sichten
7. Optional: offizielle Veo-3.1-API als bezahlter Fallback-Provider, **J** Gemini-TTS
