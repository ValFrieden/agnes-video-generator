# 🚀 Master-Prompts für professionelle Webseiten-Erstellung & UI-Design

> **Dokument-Status**: Standard für Web-Frontend, Dashboards und Landingpages im Agnes Video Generator Projekt.
> **Herkunft**: Kuratierte Best-Practice-Sammlung aus `D:\Projects\watch\Prompts für Webseiten\Webseiten_Erstellung_Master_Prompts.md`.
> **Ziel**: Verhinderung von "AI-Slop", Sicherstellung hochwertiger Bento-Grids, Typografie und konsistentem Glassmorphism im Web-UI.

---

## 📑 Inhaltsübersicht
1. [Anti-Slop Master-Prompt (Editorial & Premium Design)](#1-anti-slop-master-prompt-editorial--premium-design)
2. [Master-Prompt für interaktive 3D & WebGL / Three.js Websites](#2-master-prompt-für-interaktive-3d--webgl--threejs-websites)
3. [Design-System & Referenz-Dekonstruktion (aus Screenshots)](#3-design-system--referenz-dekonstruktion-aus-screenshots)
4. [Master-Prompt für moderne SaaS & Web-App Interfaces](#4-master-prompt-für-moderne-saas--web-app-interfaces)
5. [Scroll-Storytelling & GSAP ScrollTrigger Animationen](#5-scroll-storytelling--gsap-scrolltrigger-animationen)
6. [Live-Customizer / Tweaks Panel Prompt (CSS Variables)](#6-live-customizer--tweaks-panel-prompt-css-variables)
7. [Feinschliff & Performance Audit Prompt (CSS / SEO / Accessibility)](#7-feinschliff--performance-audit-prompt)

---

## 1. Anti-Slop Master-Prompt (Editorial & Premium Design)
> **Zweck:** Verhindert das typische, billig wirkende Standard-KI-Design (monotone Abstände, überall abgerundete Karten) und erzwingt asymmetrische Grids, edle Typografie und echten Weißraum.

```markdown
Erstelle eine moderne, preisgekrönte Landingpage (Awwwards-Niveau) für [PRODUKT / MARKE / THEMA].

VISUELLE REGELN & ÄSTHETIK (KEIN KI-SLOP):
- Vermeide typische KI-Muster: Packe NICHT jedes Element in abgerundete weiße Standard-Karten mit Schatten.
- Asymmetrie & Bento-Grid: Nutze ein dynamisches Bento-Grid mit unterschiedlichen Kachelgrößen und asymmetrischer Anordnung.
- Typografie: Nutze ausdrucksstarke Google Fonts (z. B. "Syne", "Outfit" oder "Playfair Display" für Headlines; "Plus Jakarta Sans" oder "Inter" für Fließtext). Setze auf starken Größenkontrast (fluid typography mit clamp).
- Weißraum (Negative Space): Gib den Elementen viel Raum zum Atmen (großzügige paddings/margins).
- Farbpalette: Verwende moderne, harmonische HSL/OKLCH-Farben. Dunkler, samtiger Hintergrund (z. B. #0a0a0c), edle Akzentfarben (z. B. Champagner-Gold / Emerald / Electric Indigo), keine 100% reinen Schwarz/Weiß-Werte.

SEKTIONEN:
1. Hero-Sektion: Asymmetrischer, kraftvoller Headline-Text, subtiler Hintergrund-Glow, dynamische CTA-Taste mit Glassmorphism-Hover-Effekt.
2. Bento-Showcase: 4–5 interaktive Kacheln mit Feature-Highlights und Micro-Badges.
3. Social Proof / Zahlen: Große typografische Statistiken ohne starre Tabellenrahmen.
4. Interaktive Leistungsübersicht / Akkordeon mit flüssigen CSS-Transitions.
5. Footer: Minimalistisch, elegant mit Status-Badge („Available for Q3 projects“).

TECHNISCHER STACK:
- Sauberes semantisches HTML5, Vanilla CSS (oder Tailwind v4) und modulares JavaScript.
- Mobile-First & voll responsiv für alle Bildschirmgrößen.
```

---

## 2. Master-Prompt für interaktive 3D & WebGL / Three.js Websites
> **Zweck:** Einbindung von echten 3D-Modellen (.glb/.obj) oder interaktiven WebGL-Shadern, die auf Mausbewegungen und Scrollen reagieren.

```markdown
Erstelle eine immersive, interaktive 3D-Website für [PROJEKTNAME / THEMA].

3D & INTERAKTION:
- Binde Three.js ein und erstelle eine interaktive Szene im Hero-Bereich (oder lade das 3D-Modell assets/model.glb).
- Die 3D-Szene / das Objekt soll dynamisch auf die Mauszeigerkoordinaten (clientX, clientY) reagieren (sanfte Parallax-Neigung und Beleuchtungswechsel).
- Beim Scrollen soll sich die Kamera-Perspektive und Skalierung des 3D-Objekts flüssig verändern.
- Licht & Schatten: 3-Punkt-Beleuchtung (Key, Fill, Rim Light) mit weichem Ambient Occlusion Schatten.
- Mobile Fallback: Auf Smartphones keine schwere Gyro/Touch-Berechnung, sondern automatische sanfte 360°-Rotation.

ATMOSPHÄRE & STIL:
- Dark Cinematic: Tiefes Anthrazit (#0b0c10), Akzente in Neon-Mint (#66fcf1) oder Warmamber.
- Typografie im Editorial-Stil mit animiertem Text-Reveal beim Laden.
- Performance: Halte stabile 60 FPS durch optimierte Render-Loops und Resize-Observer.
```

---

## 3. Design-System & Referenz-Dekonstruktion (aus Screenshots)
> **Zweck:** Wenn du Screenshots von guten Websites hast und möchtest, dass die KI denselben visuellen „Geschmack“ adaptiert.

```markdown
Analysiere die Screenshots im Ordner /references (oder die angehängten Bilder).

Dekonstruiere die visuelle Sprache:
1. Grid & Layout: Welche Spaltenbreiten, Weißraum-Verhältnisse und Asymmetrien werden genutzt?
2. Typografie: Welche Schriftarten, Größenverhältnisse (Headlines vs. Body) und Zeilenabstände fallen auf?
3. Farbpalette: Extrahiere die genauen Primär-, Sekundär- und Akzentfarben sowie Hintergrundnuancen in Hex/OKLCH.
4. Micro-Interactions: Welche visuellen Cues (Badges, Linien, sanfte Border-Gradients) machen das Design hochwertig?

Erstelle aus dieser Analyse eine vollständige Datei `DESIGN_SYSTEM.md` und definiere darin alle CSS-Variablen, Typografie-Regeln und Layout-Tokens für unser Projekt.
```

---

## 4. Master-Prompt für moderne SaaS & Web-App Interfaces
> **Zweck:** Saubere Dashboards, Web-Tools und SaaS-Plattformen mit Dark/Light-Mode, Daten-Visualisierung und flüssigen Zustandswechseln.

```markdown
Erstelle das Frontend für eine SaaS-Web-Applikation im Bereich [Z. B. AI Video Generator Dashboard].

FEATURES & KOMPONENTEN:
1. Sidebar Navigation: Einklappbar, mit aktiven Indikatoren, Benutzerprofil und Dark/Light-Toggle.
2. Dashboard Overview:
   - 4 Metrik-Karten mit Sparkline-Trends und Prozentveränderung.
   - Interaktives Hauptdiagramm mit Zeitfilter.
   - Datentabelle mit Sortierung, Filterung nach Status und Pagination.
3. Detailansicht / Modal: Öffnet sich beim Klick auf eine Tabellenzeile mit flüssiger Blur-Animation.

UI/UX ANFORDERUNGEN:
- Glassmorphism & Subtle Borders: Zarte 1px Borders mit 10% Opacity statt schwerer Schatten.
- State Handling: Implementiere visuelle Feedback-Zustände für Hover, Active, Loading (Skeleton-Screen) und Empty States.
- Keyboard Navigation: Escape schließt Modale, Pfeiltasten steuern Menüs.
```

---

## 5. Scroll-Storytelling & GSAP ScrollTrigger Animationen
> **Zweck:** Für narrative Websites, bei denen Elemente und Videos beim Scrollen synchron gesteuert werden (Scrubbing / Pinning).

```markdown
Implementiere für diese Landingpage ein cineastisches Scroll-Storytelling mit GSAP und ScrollTrigger:

1. Hero Pinning: Fixiere die Hero-Sektion für 150vh Scroll-Distanz. Während des Scrollens vergrößert sich das zentrale Produktbild und der Hintergrund dunkelt sanft ab.
2. Staggered Text Reveal: Wenn neue Sektionen in den Viewport scrollen, blenden Überschriften und Absätze wortweise mit einer leichten Y-Verschiebung und Fade-In ein.
3. Card Stacking / Overlap: In der Feature-Sektion sollen 3 Karten beim Herunterscrollen übereinander gleiten und einrasten (Stacking Effect).
4. Parallax Floating Elements: Hintergrund-Orbs und geometrische Formen bewegen sich mit unterschiedlichen Geschwindigkeiten (0.2x bis 0.8x Scroll-Speed).

Sorge dafür, dass alle Animationen auf mobilen Geräten flüssig mit `will-change: transform` laufen und keine Layout-Shifts (CLS) verursachen.
```

---

## 6. Live-Customizer / Tweaks Panel Prompt (CSS Variables)
> **Zweck:** Einbindung einer visuellen Steuerungsleiste direkt auf der Website, um Schriftgrößen, Abstände und Farbthemen live im Browser zu testen.

```markdown
Füge der Website ein einklappbares Einstellungs-Panel (Tweaks/Customizer) in der rechten unteren Ecke hinzu:

FUNKTIONEN:
- Farb-Themes Switcher: Umschalten zwischen 4 Paletten (z. B. "Dark Onyx", "Deep Forest", "Midnight Blue", "Warm Terracotta").
- Font Size Slider: Regelt die CSS-Variable `--font-scale` von 0.9x bis 1.2x.
- Border Radius Slider: Passt `--border-radius` live von 0px (brutalistisch) bis 24px (weich) an.
- Spacing Density: Umschalter zwischen "Compact", "Comfortable" und "Spacious".

Verbinde alle Bedienelemente direkt mit den CSS-Variablen im `:root`-Element und speichere die Auswahl im `localStorage`, damit sie beim Neuladen erhalten bleibt.
```

---

## 7. Feinschliff & Performance Audit Prompt
> **Zweck:** Für den Abschluss des Projekts – Prüfung auf Barrierefreiheit, SEO, Bildoptimierung und saubere CSS-Struktur.

```markdown
Führe ein vollständiges Code- und Design-Audit für die Website durch:

1. Barrierefreiheit (a11y):
   - Prüfe alle Kontrastverhältnisse nach WCAG AA.
   - Stelle sicher, dass alle interaktiven Elemente mit der Tastatur bedienbar sind (:focus-visible).
   - Ergänze fehlende `aria-label` und `alt`-Attribute.

2. Performance & SEO:
   - Optimiere alle Bildformate (WebP / lazy loading).
   - Validiere die H1-H6 Hierarchie und OpenGraph Meta-Tags.
   - Minimiere unnötige DOM-Reflows in Animationen.

3. Clean Code:
   - Entferne redundante CSS-Klassen und sorge für konsistente Naming Conventions.
   - Führe alle Variablen in der globalen `tokens.css` zusammen.
```
