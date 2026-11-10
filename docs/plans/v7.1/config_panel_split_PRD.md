# PRD — ConfigPanel Aufteilung (v7.1)

## 1. Problem

`frontend/src/components/ConfigPanel.vue` ist ein monolithisches 938-Zeilen-Template mit
vier logisch getrennten Sektionen (Anbieter-Verwaltung, Modell-Auswahl, Arbeitsverzeichnis,
Datenschutz). Folgen:

- Schwer wartbar: eine Änderung an der Provider-Logik erfordert das Lesen der gesamten Datei.
- Regressionsrisiko: Tests decken nur das Gesamtkomponent ab, nicht einzelne Sektionen.
- Kollisionsgefahr bei paralleler Entwicklung (mehrere Agenten/PRs).

## 2. Ziel

Aufteilung in vier Sub-Komponenten, je < 250 Zeilen, gleiche Funktionalität, keine
Verhaltensänderung. Schrittweise Migration, jeder Schritt einzeln buildbar und testbar.

## 3. Scope

### In Scope
- Extraktion von 4 Sub-Komponenten aus `ConfigPanel.vue`
- Beibehaltung der bestehenden `useConfig()`-Composable-Nutzung
- Collapsed-State bleibt in `ConfigPanel.vue` (Orchestrator)
- Keine API- oder Datenmodell-Änderungen

### Out of Scope
- Refactoring der `useConfig()`-Composable (bleibt wie ist)
- Neue Features oder UI-Änderungen
- Änderung der i18n-Keys

## 4. Sub-Komponenten

| # | Komponente | Quell-Zeilen (aktuell) | Verantwortung |
|---|---|---|---|
| 1 | `ProviderManager.vue` | 373–670 (~300 Zeilen) | Provider-Liste, Add/Edit-Modal, API-Key-Verwaltung, Domain-Mapping |
| 2 | `ModelSelector.vue` | 671–833 (~160 Zeilen) | Text/Image/Video-Modell-Auswahl, Capability-Tabelle |
| 3 | `WorkspaceManager.vue` | 834–911 (~80 Zeilen) | Arbeitsverzeichnis hinzufügen/aktivieren/entfernen |
| 4 | `PrivacySettings.vue` | 912–972 (~60 Zeilen) | GA-Opt-Out, Transparenz-Text |

`ConfigPanel.vue` wird zum Orchestrator (~150 Zeilen): Collapse-State, Composable-Init, Sub-Komponenten-Einbindung.

## 5. Migrationsreihenfolge

1. **ProviderManager.vue** (größter, eigenständigster Block) — zuerst
2. **ModelSelector.vue**
3. **WorkspaceManager.vue**
4. **PrivacySettings.vue**

Jeder Schritt:
- Sub-Komponente erstellen (Template + Script aus ConfigPanel kopieren)
- `useConfig()` in der Sub-Komponente aufrufen (Composable ist wiederverwendbar)
- Collapsed-State als Prop + `toggle`-Event
- ConfigPanel: alten Block durch `<SubComponent />` ersetzen
- `npm run build` + `npm test` + manueller GUI-Test (Einstellungen-Modal)

## 6. Verifikation

- [ ] `npm run build` erfolgreich
- [ ] `npm test` (42+ Tests) grün
- [ ] GUI-Test: Einstellungen-Modal öffnet alle 4 Sektionen, Collapse/Expand funktioniert
- [ ] Keine Regression bei Provider-Wechsel, Modell-Auswahl, Workspace-Aktivierung, GA-Toggle
- [ ] ConfigPanel.vue < 200 Zeilen nach Abschluss

## 7. Risiken

| Risiko | Mitigation |
|---|---|
| useConfig-State wird in mehreren Komponenten dupliziert | Composable ist designed für Multi-Instanz; State liegt im appState/store, nicht im Composable |
| Collapsed-State-Synchronisation | Bleibt in ConfigPanel (Orchestrator), wird als Prop übergeben |
| Modal-Teleport (Provider-Modal) | Modal bleibt in ProviderManager mit eigenem Teleport |

## 8. Aufwand

- Schritt 1 (ProviderManager): M (2-3h)
- Schritt 2 (ModelSelector): S (1h)
- Schritt 3 (WorkspaceManager): S (1h)
- Schritt 4 (PrivacySettings): S (30min)
- Gesamt: M (~5h)