> **УСТАРЕЛО (27.10.2026).** Актуальный статус в `docs/knowledge/production-log.md` и `python -m core.flow_pipeline status`.

# Übergabe: Masha-Musikvideo in Google Flow (Stand 27.10.2026, ~22:00)

Lies das zuerst. Danach mit **S03** weitermachen (siehe „Nächster Schritt“).

## Auftrag und Regeln des Nutzers
- Animiertes Musikvideo zu „Masha - S dnem Rozdenija.mp3“ (3:07). Nur Masha im Bild (stilisierte 3D-Figur, nach echten Fotos, hellblaues Hemd). Drehbuch: `С днём рождения, Маша — сценарий клипа (Google Flow).md` (27 Shots), Regeln: `ПРАВИЛА_КЛИПА.md` (Abschnitt 6 = Flow-Grenzen).
- Nutzer schreibt Russisch (manchmal Deutsch). Antworten auf Russisch, knapp, Ergebnis immer zeigen (`SendUserFile`).
- **Nach jedem Schritt Ergebnis zeigen und Freigabe abwarten** (Keyframe, Video). Der Nutzer hat gesagt: **nicht mehr nach dem Preis fragen**. Das gilt nur innerhalb der Budget-Policy (Limit 20 pro Clip). Immer nur einmalig „Genehmigen“, **nie** „Immer genehmigen“.
- Nutzer ist genervt von Zugriffsabfragen: Sitzung lief in Bypass-Modus. In `.claude/settings.local.json` stehen Allow-/Deny-Regeln (Deny u. a. `rm -rf`, `git reset --hard`, `git push --force`). Kein `rm -rf` verwenden.

## Konto / Projekt
- Flow-Projekt: `https://flow.google.com/u/0/project/0559cf6d-d69a-4ba0-a214-0b4c5d6c0c81` (Konto „second“, `flow_accounts.json`, index 0).
- Guthaben: **990** Credits nach S02 (Veo 3.1 Fast = 20 Credits; Bilder kosten nichts). Erstes Konto ist fast leer (~80).
- Chrome mit Debug-Port 9222 muss laufen: `powershell -File tools/google-flow-browser-mcp/launch_chrome.ps1` (schließt sich, wenn die App beendet wird).

## Stand der Shots (`python -m core.flow_pipeline status`)
- **S01 fertig**: Verwandlung Foto → 3D-Figur als EIN Kader per ffmpeg-Morphing (nicht Veo): `masha_frames/morph/morph_s01.mp4` aus `masha_frames/wide_16x9/wide_01.jpg` + `masha_frames/morph/toon_aligned.jpg` (Kompositionsübereinstimmung 0.90). Veo zwischen zwei verschiedenen Kadern gab „Phasen“ und wurde verworfen.
- **S02 vom Nutzer freigegeben**: `masha_frames/clips/clip_02.mp4` (8 s, 20 Credits). Keyframe `masha_frames/s02/s02_keyframe.jpg`. Letzter Kader des Clips: `masha_frames/s03/s02_last_frame.png` (Fenster ist dort schon angelehnt, Blüten im Raum).
- Zustandsdateien: `flow_state/shots.json`, `flow_state/credits.jsonl` (S01 + S02 nachgetragen, 80 Credits).

## Nächster Schritt: S03 (Drehbuch: Maria öffnet das Fenster, Kamera hinter der Schulter, sanfter Push-in)
Der Nutzer wünscht: Referenz für den Raum = **letzter Kader des S02-Videos**, nicht der S02-Keyframe. Charakterreferenz bleibt `masha_frames/old_project/01_turnaround.jpg`. Perplexity bestätigte: Kader nicht mehrfach hochskalieren oder neu kodieren, Charakter-Referenz sauber halten.

1. Keyframe erzeugen (Bild, kostenlos). Prompt anpassen: im S02-Letztkader ist das Fenster schon halb offen, also „drückt das Fenster ganz auf“:
```bash
.venv/Scripts/python.exe -m core.flow_pipeline image --prompt "Camera behind her left shoulder: the same character as in the first attached image (character sheet: long straight dark chestnut-brown hair with center part, light sky-blue button-up shirt with rolled sleeves) seen from behind and slightly from the side, standing at the old wooden window of the same bedroom as in the second attached image (same room, curtains, light), both hands on the open window sash about to push it fully open. Outside: blooming apple trees in warm morning sunlight, a few blossom petals in the air." --ref masha_frames/old_project/01_turnaround.jpg --ref masha_frames/s03/s02_last_frame.png --out masha_frames/s03/s03_keyframe.jpg
```
   Keyframe selbst ansehen (Read), bei schlechtem Ergebnis neu erzeugen (kostenlos).
2. Video über den Konvergenzbefehl (Veo 3.1 Fast, 8 s, 20 Credits, Policy/Zustand/Journal laufen automatisch):
```bash
.venv/Scripts/python.exe -m core.flow_pipeline video --shot S03 --frame masha_frames/s03/s03_keyframe.jpg --motion "Camera behind her shoulder, gentle push-in. She pushes the old wooden window fully open with both hands, warm sunlight floods the room, blossom petals drift inside." --out masha_frames/clips/clip_03.mp4
```
3. Kontaktbogen: `python -m core.flow_pipeline sheet --video masha_frames/clips/clip_03.mp4 --out masha_frames/clips/s03_sheet.jpg --times 0.3,2,4,6,7.7`, Clip und Bogen dem Nutzer zeigen, Freigabe abwarten, dann S04.

## Wichtige Erkenntnisse (alle live bestätigt)
- **Zuletzt behoben (27.10.)**: `submit_prompt` klickte die erste von mehreren „Generierung starten“-Schaltflächen und meldete trotzdem Erfolg (deshalb „hängt, nichts passiert“). Jetzt wird die letzte sichtbare, aktive geklickt und geprüft, dass das Eingabefeld danach leer ist. Danach waren die Flow-Tests grün; die Pipeline ist seither **noch nicht** gegen echtes Flow durchgelaufen: S03 ist der erste Live-Test des Fixes.
- Veo 3.1 Fast liefert in 16:9 nur 8 s (Tarif). Lange Eingaben ohne „Generate a video…“-Anfang führen zu Rückfragen des Agenten.
- Ausgaben nicht mit `| tail` filtern, wenn der Befehl lange läuft: Fortschritt bleibt unsichtbar und wirkt wie ein Hänger. Lange Läufe im Hintergrund starten, `run_in_background`, dann Dateien/Logs lesen.
- Der alte Chrome-Port 9222 geht verloren, wenn die App schließt; erst `curl http://127.0.0.1:9222/json/version` prüfen.
- Tests schnell laufen lassen (≈4 s): `.venv/Scripts/python.exe -m pytest tests/test_flow_*.py tests/test_google_flow.py -q --basetemp=C:/Users/Valeri/AppData/Local/Temp/claude/D--Projects-VideoGenerator/b35bf077-4455-46eb-b04a-3924ddfb1400/scratchpad/pt -p no:cacheprovider` (`--basetemp` nötig wegen Rechten im Standard-Temp).
- Gesamt-Testlauf: 4 Fehler außerhalb von Flow (`test_config_settings` ×2, `test_ffmpeg_tool`, `test_gallery_routes`), nicht von uns.

## Neu in dieser Sitzung (alles ungenehmigt/uncommittet)
`core/flow_shot_state.py`, `core/flow_budget.py`, `core/flow_frames.py`, `core/flow_transitions.py`, `core/flow_prompts.py`, `core/flow_pipeline.py`, Änderungen in `core/api/google_flow_engine.py` und `core/api/google_flow_ui.py`, `flow_accounts.json`, `flow_state/`, `docs/flow_api_alternative.md`, Tests `tests/test_flow_*.py` und `tests/test_google_flow.py` (schnelle Schlafzeiten), Abschnitt 6 in `ПРАВИЛА_КЛИПА.md`. Nichts ist committet; Commit nur auf Wunsch des Nutzers.

## Offen
- API-Adapter für Veo (nur Bewertung in `docs/flow_api_alternative.md`, nicht gebaut).
- Wasserzeichen erkennt nichts automatisch (Sichtprüfung).
- Restliche Shots S04–S27 laut Drehbuch.

## База знаний
Актуальные факты и решения собраны в `docs/knowledge/README.md`; после этой передачи обновлять её, а не только этот файл.
