# DESIGN.md — Neumorphic Soft-Touch Studio Design System

> **Style Identity**: Tactile Neumorphism / Soft UI (Web UI Control Elements)  
> **Source Reference**: `WEB UI SET CONTROL ELEMENTS` reference sheet  
> **Target Framework**: Vue 3 + Tailwind CSS  
> **Version**: 1.0.0  
> **Status**: Active Constitution for GUI/UI/UX

---

## 1. Core Visual Philosophy

The design system translates the physical aesthetics of high-end tactile hardware control consoles into a digital web interface:
1. **Material Continuity (One Seamless Sheet)**: Elements are not layered on separate disconnected planes; instead, they emerge *extruded* (convex) from the background surface or are *carved/recessed* (concave/debossed) into it.
2. **Dual-Vector Physics of Light**:
   - Primary Light Source: Top-Left (135° angle / -45° azimuth).
   - High-Light (Specular): Pure soft white/light glow falling on the top-left edge.
   - Low-Shadow (Ambient Occlusion): Soft, diffuse shadow cast toward the bottom-right.
3. **Organic & Capsule Geometry**:
   - Generous border radiuses (pills, capsules, squircles, circular dials).
   - Soft beveled transitions avoiding razor-sharp 1px dividers where possible.
   - Smooth tactile feedback: Hover gently lifts or deepens bevel; Active/Click sinks into the surface (`inset` shadow).

---

## 2. Color Palette & Physics Tokens

### 2.1 Light Mode (Porcelain Titanium — Reference Direct)

Matches the exact soft matte off-white / light slate of the reference sheet:

| Token | Hex / Value | Role |
| :--- | :--- | :--- |
| `--neu-bg` | `#E0E5EC` | Master canvas surface |
| `--neu-surface-raised` | `#E2E7EE` | Convex button / card surface |
| `--neu-surface-sunken` | `#D9DFE7` | Inset field / track well surface |
| `--neu-shadow-light` | `#FFFFFF` | Specular highlight (top-left) |
| `--neu-shadow-dark` | `rgba(163, 177, 198, 0.7)` | Ambient drop shadow (bottom-right) |
| `--neu-shadow-dark-deep` | `rgba(163, 177, 198, 0.9)` | Deep shadow for elevated buttons |
| `--neu-ink-primary` | `#2D3748` | Primary text and icons |
| `--neu-ink-secondary` | `#4A5568` | Secondary labels and descriptions |
| `--neu-ink-muted` | `#718096` | Hints, placeholders, disabled states |
| `--neu-accent` | `#3182CE` / `#4C51BF` | Active LED indicator & focus glow |

### 2.2 Dark Mode (Obsidian Matte Slate — Dark Neumorphism)

Preserves the exact dual-light physical elevation in dark mode:

| Token | Hex / Value | Role |
| :--- | :--- | :--- |
| `--neu-bg` | `#181B20` | Dark slate canvas surface |
| `--neu-surface-raised` | `#1C2026` | Dark convex card / button surface |
| `--neu-surface-sunken` | `#14171B` | Dark recessed input well |
| `--neu-shadow-light` | `rgba(255, 255, 255, 0.06)` | Subtle specular rim (top-left) |
| `--neu-shadow-dark` | `rgba(0, 0, 0, 0.65)` | Deep ambient shadow (bottom-right) |
| `--neu-shadow-dark-deep` | `rgba(0, 0, 0, 0.85)` | Elevated button drop shadow |
| `--neu-ink-primary` | `#F7FAFC` | Primary light text and icons |
| `--neu-ink-secondary` | `#CBD5E0` | Secondary labels |
| `--neu-ink-muted` | `#718096` | Subtle text |
| `--neu-accent` | `#6366F1` | Luminous accent |

---

## 3. Elevation & Surface Physics

### 3.1 Raised / Convex (`.neu-raised`)
Simulates elements extruded upward toward the user:
```css
/* Standard Card & Idle Button */
box-shadow: 
  6px 6px 14px var(--neu-shadow-dark),
  -6px -6px 14px var(--neu-shadow-light);

/* Deep / Floating Elevated (Hero buttons, Dials) */
box-shadow: 
  9px 9px 20px var(--neu-shadow-dark-deep),
  -9px -9px 20px var(--neu-shadow-light);
```

### 3.2 Sunken / Concave (`.neu-sunken`)
Simulates wells, text inputs, depressed tracks, and active toggles:
```css
/* Input fields, Recessed tracks, Active toggles */
box-shadow: 
  inset 4px 4px 8px var(--neu-shadow-dark),
  inset -4px -4px 8px var(--neu-shadow-light);
```

### 3.3 Soft Tactile Dial / Knob (`.neu-dial`)
Directly modeled after the circular dials and organic Play/Pause buttons in the reference image:
```css
border-radius: 9999px;
background: linear-gradient(145deg, var(--neu-surface-raised), var(--neu-surface-sunken));
box-shadow: 
  7px 7px 16px var(--neu-shadow-dark),
  -7px -7px 16px var(--neu-shadow-light);
```

---

## 4. Component Mapping (Reference Sheet to Agnes Studio)

| Reference Element from Image | Real-World Application in Studio | Implementation Class |
| :--- | :--- | :--- |
| **Capsule Pill (`< >`)** | Main Navigation Tabs (`Студия`, `Задачи`, `Галерея`) & Aspect Ratio Selector (9:16 / 16:9 / 1:1) | `.neu-pill`, `.neu-pill-active` |
| **Large Organic Play/Pause Blob** | Hero **Generate Video Button** (`✨ Сгенерировать видео`) with integrated status dot | `.neu-btn-hero` |
| **Recessed Capsule (`OFF / ON`)** | Pipeline Execution Switcher (`⚡ Авто` vs `🎯 Пошаговый`) & Checkpoint toggles | `.neu-toggle-track`, `.neu-knob` |
| **Directional Pad (D-Pad) with 'OK'** | Task Type Selector Grid (Creative, Simple, Manuscript, Anchor, Poetry) | `.neu-dpad-card` |
| **Vertical Stepper (`+ / -`)** | Scene Count & Duration Steppers | `.neu-stepper` |
| **Sunken Pill Container** | Textarea & Input Fields (Prompts, Task Name, Styles) | `.neu-input` |

---

## 5. CSS Utility Classes Specification

```css
/* ── Neumorphic Utility Classes ── */

.neu-bg {
  background-color: var(--neu-bg);
}

.neu-card {
  background-color: var(--neu-surface-raised);
  border-radius: 1.25rem;
  box-shadow: 6px 6px 14px var(--neu-shadow-dark), -6px -6px 14px var(--neu-shadow-light);
  border: 1px solid var(--neu-border-subtle);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.neu-input {
  background-color: var(--neu-surface-sunken);
  border-radius: 0.875rem;
  box-shadow: inset 3px 3px 7px var(--neu-shadow-dark), inset -3px -3px 7px var(--neu-shadow-light);
  border: 1px solid transparent;
  color: var(--neu-ink-primary);
  transition: all 0.2s ease;
}

.neu-input:focus {
  outline: none;
  border-color: color-mix(in oklab, var(--neu-accent) 40%, transparent);
  box-shadow: inset 3px 3px 7px var(--neu-shadow-dark), inset -3px -3px 7px var(--neu-shadow-light), 0 0 0 2px color-mix(in oklab, var(--neu-accent) 25%, transparent);
}

.neu-btn {
  background-color: var(--neu-surface-raised);
  border-radius: 0.75rem;
  box-shadow: 4px 4px 10px var(--neu-shadow-dark), -4px -4px 10px var(--neu-shadow-light);
  color: var(--neu-ink-primary);
  font-weight: 500;
  transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
}

.neu-btn:hover {
  transform: translateY(-1px);
  box-shadow: 6px 6px 14px var(--neu-shadow-dark), -6px -6px 14px var(--neu-shadow-light);
}

.neu-btn:active, .neu-btn-active {
  background-color: var(--neu-surface-sunken);
  box-shadow: inset 3px 3px 6px var(--neu-shadow-dark), inset -3px -3px 6px var(--neu-shadow-light);
  transform: translateY(0);
}

.neu-btn-hero {
  background: linear-gradient(145deg, var(--neu-surface-raised), var(--neu-surface-sunken));
  box-shadow: 8px 8px 18px var(--neu-shadow-dark-deep), -8px -8px 18px var(--neu-shadow-light);
  border-radius: 1rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.neu-btn-hero:hover:not(:disabled) {
  box-shadow: 10px 10px 22px var(--neu-shadow-dark-deep), -10px -10px 22px var(--neu-shadow-light);
  transform: translateY(-1.5px);
}

.neu-btn-hero:active:not(:disabled) {
  box-shadow: inset 4px 4px 8px var(--neu-shadow-dark-deep), inset -4px -4px 8px var(--neu-shadow-light);
  transform: translateY(0);
}
```

---

## 6. Accessibility & Contrast Safeguards

Neumorphism can historically suffer from low contrast if implemented carelessly. This design system strictly enforces:
1. **High Contrast Typography**: Text color maintains a minimum of `4.5:1` contrast ratio against `--neu-bg` (WCAG 2.2 AA compliant).
2. **Double-State Indicators**: Never rely solely on shadow depth to communicate state. Active buttons, tabs, and checkboxes ALWAYS incorporate:
   - Visible accent indicator dot or badge (`🟢` / solid accent color)
   - Distinct text weight / color shift
   - Clear focus ring (`outline: 2px solid var(--neu-accent)`) for keyboard navigation.
