# Veo über die offizielle API statt über die Flow-Oberfläche

Stand: 27.10.2026. **Nicht umgesetzt**: Es gibt weder einen API-Schlüssel noch eine
Abrechnung für die API in diesem Projekt, daher kann Code dafür nicht geprüft
werden. Dies ist die Bewertung, ob sich der Aufwand lohnt.

## Was laut Googles Dokumentation (über Perplexity abgefragt) feststeht

| Punkt | Wert | Quelle |
|---|---|---|
| Modelle in Vertex AI | `veo-3.1-generate-001` (Standard), `veo-3.1-fast-generate-001` (Fast) | Vertex-AI-Doku |
| Seitenverhältnisse | 16:9 und 9:16 | Gemini-API- und Vertex-Doku |
| Dauer | 4, 6 oder 8 s; mit Referenzbildern nur 8 s | beide |
| Erster und letzter Kader | in Vertex AI unterstützt | Vertex-Doku |
| Referenzbilder | bis zu 3 (Gemini API) | Gemini-API-Doku |
| Ton | synchron erzeugt | beide |
| Preis Vertex AI | Fast 0,15 USD/s mit Ton (8 s = 1,20 USD); Standard 0,40 USD/s mit Ton, 0,20 USD/s ohne | Vertex-Preisseite |
| Flow-Credits | Veo 3.1 Fast = 20 Credits pro Clip (Pro), 10 (Ultra); Pro bekommt 1000 Credits im Monat | Flow-Hilfe |

Die älteren `*-preview`-IDs wurden laut Doku am 22.10.2026 abgeschaltet.

## Was **nicht** feststeht

- Ein Gemini-API-eigener Preis pro Sekunde und öffentliche Ratenlimits (nicht in den Quellen).
- Wert eines Flow-Credits in Euro. Ein Preisvergleich Flow ↔ API ist deshalb nicht belegt.
- Ob die Dauer 6 s in 16:9 über die API buchbar ist, obwohl der Tarif in Flow nur 8 s zulässt.

## Bewertung

- **Dafür:** keine Oberflächen-Automatisierung (kein Menü, das schließt, keine Chips,
  kein Rendern abwarten über die Seite), Preis vor dem Aufruf bekannt, Wiederholbarkeit,
  Kader und Prompt als saubere Parameter, Erster-/Letzter-Kader nativ.
- **Dagegen:** Nutzungspreis in Dollar zusätzlich zum bezahlten Flow-Abo (1,20 USD pro
  8-s-Clip in Fast; bei 27 Clips etwa 32 USD), Konto-/Abrechnungs-Einrichtung, die
  Flow-Charaktere und die Flow-Szenenmontage fallen weg.
- **Empfehlung:** Beim aktuellen Stand (Guthaben im zweiten Konto reicht für die Planung)
  bei Flow bleiben. Die API lohnt sich, wenn die Oberfläche wieder bricht oder die
  Credits ausgehen. Dann zuerst einen einzelnen Probeclip über die API erzeugen und
  Preis sowie Ergebnis gegen Flow vergleichen, bevor ein Adapter gebaut wird.

## Wenn die API genutzt werden soll

Ein Adapter bräuchte dieselbe Schnittstelle wie `GoogleFlowEngine.generate_scene`
(Prompt, Startkader, Zielpfad), dazu `BudgetPolicy` und `CreditLedger` aus
`core/flow_budget.py` (Preis in Dollar statt Credits) und die Zustandsdatei
`core/flow_shot_state.py`. Alles Übrige (Kader prüfen, Morphing, Kontaktbogen) ist
unabhängig von Flow und bleibt unverändert.
