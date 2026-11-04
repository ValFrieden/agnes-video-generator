# SYNTX Cinematic Directing Standard (Режиссерский стандарт SYNTX AI)

> **Статус**: 🟢 Обязательный стандарт режиссуры и операторской работы в VideoGenerator.  
> **Инспирировано**: Разборами, гайдами и видеоуроками портала и сообщества [SYNTX FAMILY](https://t.me/syntxfamily) (`@syntxfamily`) и LTX Studio.  
> **Связанный код**: `core/screenwriter/scenario_director.py`, `core/screenwriter/camera_presets.py`, `core/screenwriter/scenes.py`.

---

## 1. Главный тезис: «Красиво ≠ Кино» (Beautiful ≠ Cinema)

ИИ-генераторы способны выдавать гипердетализированные изображения (8K, photorealistic), но видео выдаёт себя за 3 секунды, если:
1. Камера бесцельно «плавает» как дрон без физической массы и операторской мотивации.
2. Персонаж начинает спонтанно двигать ртом (галлюцинации липсинка) или расплываться в морфинге.
3. В 5-секундном отрезке смешаны конфликтующие действия или эмоции.

---

## 2. Посекундный Temporal Prompting (Таймлайн-промптинг)

Вместо сплошного абзаца текста для видеомоделей (Kling, Veo, Seedance, Agnes Video) применяется детерминированная 3-фазная временная структура:

```text
[0.0-1.0s]: Establishing frame in Medium Shot. Continuity locks: short matte brown hair; grey-green eyes; indigo wool overcoat. Setting: Rainy city street at dusk. Lighting & Palette: Edward Hopper indigo rain and warm amber neon. Atmospheric micro-motion, gentle breathing, mouth firmly closed, no speaking.
[1.0-3.5s]: Dynamic narrative progression: Walks through puddle reflections towards illuminated telephone booth. Camera execution: Slow deliberate dolly push-in camera movement towards the subject, mounting emotional intensity and focal intimacy. Consistent physical momentum, natural foreground-to-background parallax, cinematic motion blur.
[3.5-5.0s]: Emotional resolution: Melancholic resolve. Actor micro-expression: intense focused gaze, subtle breath, motionless lips. Framing stabilizes cleanly, preparing seamless cut for transition: Whip Pan.
```

### Фазы таймлайна:
* **Фаза 1 `[0.0 - t1 s]` (Экспозиция)**: Фиксация плановости (Shot Size), окружения, света и **дословных замков непрерывности (Continuity Locks)**. Строгое правило: *mouth firmly closed, no speaking* (предотвращает паразитный липсинк).
* **Фаза 2 `[t1 - t2 s]` (Действие и камера)**: Единственное главное динамическое действие + конкретный пресет из каталога 20 движений камеры.
* **Фаза 3 `[t2 - dur s]` (Эмоция и стабилизация)**: Фиксация доминирующей эмоции (1 Shot = 1 Emotion), микромимика взгляда и дыхания, стабилизация кадра перед монтажным переходом (Cut, Match Cut, Whip Pan).

---

## 3. Каталог 20 кинематографических движений камеры

Каждое движение имеет точное профессиональное название и жесткий модификатор для промпта (в модуле `core/screenwriter/camera_presets.py`):

| ID | Название | Категория | Модификатор промпта (Prompt Modifier) |
|---|---|---|---|
| `dolly_in` | Dolly In (Плавный наезд) | Драматические | *Slow, deliberate dolly push-in camera movement towards the subject, mounting emotional intensity and focal intimacy.* |
| `dolly_out` | Dolly Out (Плавный отъезд) | Драматические | *Slow continuous dolly pull-back revealing surrounding environment, creating emotional solitude and narrative scale.* |
| `vertigo_zoom` | Vertigo (Долли-зум) | Драматические | *Vertigo contra-zoom (dolly zoom), background perspective warps and stretches dramatically while subject size remains rock-solid in frame.* |
| `snorricam` | Snorricam (Крепление к телу) | Драматические | *Snorricam chest-rig mounted to the actor, background twists and shifts frantically around the motionless face, conveying extreme anxiety.* |
| `crash_zoom` | Crash Zoom (Ударный наезд) | Драматические | *Rapid aggressive crash zoom snapping instantly from wide view onto the subject's eyes, dramatic sudden reveal.* |
| `orbital_pan_cw` | Orbital Pan (По часовой) | Динамические | *Smooth 360-degree orbital arc shot circling clockwise around the subject at eye level with rich dynamic parallax.* |
| `orbital_pan_ccw` | Orbital Pan (Против часовой) | Динамические | *Smooth orbital arc shot sweeping counter-clockwise around the subject, keeping face centered in cinematic frame.* |
| `tracking_shot` | Tracking Shot (Боковое слежение)| Динамические | *Lateral tracking dolly shot moving parallel alongside the moving subject, strong foreground-to-background parallax.* |
| `follow_cam` | Follow Cam (Следование со спины)| Динамические | *Steadicam tracking shot smoothly following behind the protagonist, maintaining fluid forward momentum and depth.* |
| `whip_pan` | Whip Pan (Хлыстовая панорама) | Динамические | *Fast kinetic whip pan transition with high motion blur snapping rapidly across the scene, seamless visual cut.* |
| `crane_up` | Crane Up (Подъем краном) | Ракурсные | *Sweeping crane jib arm ascending vertically from ground level up to high-angle vantage point, revealing cinematic grandeur.* |
| `crane_down` | Crane Down (Спуск краном) | Ракурсные | *Majestic crane jib descent gliding smoothly from high sky down to intimate character eye level.* |
| `dutch_angle` | Dutch Angle (Голландский угол)| Ракурсные | *Dutch angle tilted camera roll 25 degrees off the horizon, conveying disorientation, psychological tension, and unease.* |
| `low_angle_hero`| Low Angle (Героический снизу) | Ракурсные | *Low-angle upward-looking tilt framing the subject from below, conveying power, dominance, and monumental presence.* |
| `overhead_god_view`| Top-Down (Вид строго сверху)| Ракурсные | *High-angle top-down 90-degree zenith bird's-eye view looking directly down from above onto the geometry of the scene.* |
| `pedestal_up` | Pedestal Up (Лифт вверх) | Ракурсные | *Smooth vertical pedestal camera elevation straight up without tilting, revealing vertical architectural scale.* |
| `tilt_down` | Tilt Down (Наклон сверху вниз)| Атмосферные | *Slow vertical tilt-down camera movement starting from sky/ceiling, smoothly settling onto the character's eye line.* |
| `slow_pan` | Slow Pan (Широкая панорама) | Атмосферные | *Slow, lyrical horizontal panoramic pan sweeping smoothly across the environment, establishing rich atmospheric depth.* |
| `handheld_documentary`| Handheld (Живая ручная камера)| Атмосферные | *Organic handheld camera motion with subtle natural micro-shakes and human breathing rhythm, documentary realism.* |
| `static_locked` | Static (Фиксированный штатив)| Атмосферные | *Static locked-off shot on heavy tripod, absolute stability, no camera drift, allowing pure character motion within frame.* |

---

## 4. Двухфазный режим Draft Mode («5 видео по цене одного»)

1. **Фаза предпросмотра (Draft)**:
   - Создаются черновые сцены с быстрой/легковесной генерацией и пониженным разрешением.
   - Автоматически строится контактный лист 25/50/75% (`qa_trio.png`).
   - Пайплайн встает на паузу (`CHECKPOINT_VIDEOS`) для утверждения режиссером.
2. **Фаза финализации (Full)**:
   - Только одобренные кадры отправляются на чистовой рендер в высоком разрешении и полную склейку с субтитрами и TTS.

---

## 5. Audio-First: Синхронизация с ритмом и музыкой (Music Video)

* **Первичность аудио**: Структура сцен задается ритмической сеткой трека (BPM, 4/4 такт, куплеты, дропы).
* **Смена динамики**: 
  * Спокойные куплеты → статичные планы (`static_locked`), медленные наезды (`dolly_in`) или панорамы (`slow_pan`).
  * Кульминации и дропы → динамические облеты (`orbital_pan_cw`), резкие хлысты (`whip_pan`), ударные зумы (`crash_zoom`).
* **Монтажные переходы**: На стыках быстрых сцен применяются `Whip Pan` и `Zoom Blur` склейки вместо стандартного растворения (Crossfade).

---

## 6. Сториборд-сборка (Continuous Storyboard Grid 2×2)

* **Принцип квадранта**: Вместо независимой генерации 4 разрозненных планов создается единый коллаж 2×2 (Top-Left, Top-Right, Bottom-Left, Bottom-Right) с последовательными ракурсами.
* **Трансформация в видео**: Коллаж подается в видеомодель (Kling 4.0 / Seedance) для непрерывной сборки в единый план с перетеканием фокуса внимания без разорванного монтажа.
* **Генерация промпта**: Функция `build_storyboard_grid_prompt(scenes, style)` в `core/screenwriter/camera_presets.py`.

---

## 7. Физика движения и анти-сброс инерции (Motion Inertia)

* **Проблема**: Видеомодели при смене фаз промпта имеют свойство обнулять скорость персонажа, создавая «рваную» анимацию или замирание.
* **Решение SYNTX**: Обязательный модификатор постоянной линейной скорости во 2-й фазе:
  ```text
  "Maintain steady linear velocity and constant speed throughout the shot with zero sudden acceleration drops."
  ```
* **Стоп-слова (Stop-words)**: В промптах запрещены слова `suddenly`, `abruptly`, `instantly`, `jerky motion`, провоцирующие артефакты морфинга.

---

## 8. Унифицированный блок стабилизации лица (Likeness & Bone Structure Stabilizer)

* **Проблема**: Генераторы склонны применять бьюти-фильтры или деформировать геометрию лица во время движения или смены освещения.
* **Решение SYNTX**: Обязательный хвостовой блок фиксации костной структуры:
  ```text
  "Preserve exact facial bone structure, geometry, and identity throughout. Zero facial morphing, no plastic smoothing, no beautification filters. Stable photorealistic skin microtexture."
  ```
* **Хелпер**: `build_stabilizer_clause()` в `core/screenwriter/camera_presets.py`.
