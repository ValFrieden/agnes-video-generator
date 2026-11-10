# System Design — ConfigPanel Aufteilung (v7.1)

## 1. Architektur

```
ConfigPanel.vue (Orchestrator, ~150 Zeilen)
├── ProviderManager.vue      (Provider-Liste + Add/Edit-Modal + API-Key)
├── ModelSelector.vue        (Modell-Auswahl + Capability-Tabelle)
├── WorkspaceManager.vue     (Arbeitsverzeichnis-Verwaltung)
└── PrivacySettings.vue      (GA-Opt-Out + Transparenz)
```

Jede Sub-Komponente:
- Ruft `useConfig()` selbst auf (Composable ist multi-instanz-fähig)
- Erhält `collapsed: boolean` als Prop
- Emittiert `toggle` Event für Collapse/Expand
- Nutzt `t()` aus i18n direkt

## 2. Collapsed-State-Flow

```
ConfigPanel.vue
  collapsed = getCollapsePrefs()  (localStorage)
  toggleConfigPanel(section) → setCollapsePref(section, val)

  <ProviderManager :collapsed="collapsed.apikey" @toggle="toggleConfigPanel('apikey')" />
```

## 3. Schritt 1: ProviderManager.vue

### Props
- `collapsed: boolean` — ob die Sektion eingeklappt ist

### Events
- `toggle` — Collapse/Expand umschalten

### Template-Struktur
- Collapsed-Header (Button mit Icon + Titel + Provider-Anzahl)
- Expanded-Content:
  - Provider-Intro (bereits als `shared/ProviderIntro.vue` extrahiert)
  - Provider-Liste (v-for manageProviders)
  - Add/Edit-Modal (Teleport to body, role=dialog)

### Script
- Import: useConfig, useModalA11y, useToast, t, ProviderIntro
- Destructure aus useConfig: apiKeyStatus, keyCount, keySource, keyList, saveMultiKeys, loadKeyInfo, removeKey, saveKeyDomain, detectKeyDomains, detectingKeys, clearApiKey, providerName, providerApi, providerBaseUrl, providerApiKey, providerTestBusy, providerSaveStatus, providerErrorMsg, loadTextProviders, saveTextProvider, deleteTextProvider, testTextProvider, domainSaveStatus, domainErrorMsg, saveDomain, manageProviders, editingProvider, showProviderModal, modelItems, modelInput, addModelItem, onAddModel, removeModelItem, resetProviderForm, openAddProvider, openEditProvider, onKeyDomainChange, domainEntry, displayDomain, keyDomainUrl, agnesApiKeyText, providerDisplayName, providerApiLabel, modalTitle, isEditCustom, textProviderComposite, textModelOptions, onFetchProviderModels, slugifyProvider, onSaveProvider, onDeleteProvider
- useModalA11y für providerModalRef
- computed: collapsed (prop), toggle emit

## 4. Migrationsplan

### Schritt 1: ProviderManager.vue erstellen
1. Neue Datei `frontend/src/components/ProviderManager.vue`
2. Template: Zeilen 373-670 aus ConfigPanel.vue (Provider-Sektion + Modal)
3. Script: useConfig-Destructure + Provider-Funktionen kopieren
4. Props: `collapsed`, Events: `toggle`

### Schritt 2: ConfigPanel.vue aktualisieren
1. Import ProviderManager
2. Zeilen 373-670 durch `<ProviderManager :collapsed="collapsed.apikey" @toggle="toggleConfigPanel('apikey')" />` ersetzen
3. Entferne jetzt ungenutzte useConfig-Destructures und Funktionen

### Schritt 3: Verifikation
- `npm run build` + `npm test`
- GUI-Test: Einstellungen-Modal → Anbieter-Sektion öffnen/schließen, Provider hinzufügen/bearbeiten/löschen

## 5. Risiken & Mitigation

| Risiko | Mitigation |
|---|---|
| useConfig-State-Duplikation | Composable ist multi-instanz-fähig; State liegt in appState/store |
| Modal-Teleport | Modal bleibt in ProviderManager mit eigenem Teleport |
| Collapsed-State | Bleibt in ConfigPanel, wird als Prop übergeben |