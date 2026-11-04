# «С днём рождения, Маша» — анимационный клип «Ясный свет» (Google Flow)

> **Песня:** `Masha - S dnem Rozdenija.mp3`, 3:07 (187 с), 48 kHz, стерео
> **Жанр:** тёплая поп-баллада с народной интонацией: фортепиано, хоровые подпевки «О-о, Маша», форма «гимн».
> **Формат:** анимационный клип. Героиня — мультяшная Маша, похожая на реальную (по фото). **В кадре только она**, других людей нет. Вместо «гостей» её поздравляет сам мир: ветер, цветы, птицы, огоньки.
> **Скиллы:** `script-writer` (структура «Story/Narrative», хук, пейсинг), `storyboard-manager` (трёхактная структура, арка, непрерывность), `character-design-sheet` (карта героини и предметов), `google-flow` (Veo 3.1, cost guard, правила промптов). Порядок производства — по `ПРАВИЛА_КЛИПА.md`.

---

## 1. Анализ песни

### Текст и смысл
- Это песня-поздравление, а не любовная история. Конфликта нет, есть **нарастание радости**: утро → ветер несёт песню → всё цветёт → мир готовит ей праздник → кульминация → тихий шёпот.
- Главные образы из текста (они задают визуальный ряд):
  - «Утро светит за окном» — рассвет, окно;
  - «Ветер песню нам несёт» — ветер, лепестки, ленты;
  - «Ясный свет» — Маша как источник света;
  - «Берёзка над рекой» — берёза, река;
  - «Счастье ласковой волной» — вода, волна;
  - «Ты как солнышко для всех» — всё вокруг оживает, когда она проходит мимо;
  - «Весенняя сирень» — сирень;
  - «Пусть в душе цветёт весна» — вечная весна.
- **Мотив клипа:** солнечный зайчик (пятно тёплого света). В интро он превращает фото Маши в мультяшную героиню, ведёт её через день, а в финале становится огоньком свечи на торте.

### Динамика (громкость по EBU R128, шаг 2 с)

| Время | Громкость (LUFS) | Раздел (по тегу текста) | Энергия |
|---|---|---|---|
| 0:00–0:10 | −41…−24 | Intro, фортепиано, «Оо-о» | тихо |
| 0:10–0:20 | −26…−20 | Куплет 1, интимно | низкая, растёт |
| 0:20–0:38 | −16…−14 | Предприпев 1 + Припев 1 | высокая |
| 0:38–0:52 | −26/−18, «качели» | Куплет 2, есть стопы | средняя, пульсирующая |
| 0:52–1:18 | −17…−13 | Предприпев 2 + Припев 2, «взрывной» | высокая |
| 1:18–1:32 | −18/−15, «качели» | Куплет 3 | средняя |
| 1:32–2:00 | −15…−12 | Подхват припева / проигрыш с хором «О-о» | высокая |
| 2:00–2:24 | −28…−17 | Бридж, фальцет, тихая аранжировка | тихо, провал |
| 2:24–2:58 | −13…−11 (максимум) | Финальный припев, кульминация | пик |
| 2:58–3:07 | −23…−41 | Outro, шёпот «С днём рождения, Маша…» | затухание |

> ⚠️ Границы разделов определены по огибающей громкости, точность ±2 с. Перед монтажом сверьте их на слух. Отрезок 1:32–2:00 в тексте не подписан: скорее всего, это повтор припева или проигрыш на «О-о».

### Драматургия (3 акта, `storyboard-manager`)
- **Пролог — «Превращение» (0:00–0:08).** На столе лежит настоящее фото Маши. Солнечный зайчик касается его, и фото оживает: Маша становится мультяшной героиней и «просыпается» в нарисованном мире.
- **Акт I — «Утро» (0:08–0:38).** Она открывает окно, ветер зовёт её на улицу. Первый припев — она выбегает в цветущий сад.
- **Акт II — «Мир готовит праздник» (0:38–2:00).** Берёза у реки, ветер. Скатерть сама расстилается, птицы несут ленты, цветы распускаются там, где она проходит. Свет идёт от неё: «солнышко для всех».
- **Провал — «Бридж» (2:00–2:24).** Сумерки, Маша одна под сиренью, загадывает желание. Тишина и фальцет.
- **Акт III — «Праздник» (2:24–3:07).** Гирлянды зажигаются, весь сад «поёт» с ней припев. Финал: торт, свеча, шёпот, затемнение.

**Хук (`script-writer`):** первые секунды — превращение настоящего фото в мультяшную героиню. Это сразу «присваивает» клип Маше и объясняет, почему дальше она нарисована.

---

## 2. Стиль

- **Look:** стилизованная 3D-анимация уровня полнометражного мультфильма: мягкие формы, большие выразительные глаза, тёплый свет золотого часа, лёгкий bloom. Палитра: белый, нежно-зелёный (берёза), сиреневый, тёплое золото, акцент — её голубая рубашка. Кульминация — гирлянды-лампочки.
- **Глобальный стиль-блок (добавлять в КАЖДЫЙ промпт картинки и видео):**
  `Stylized 3D animated feature film look, soft rounded shapes, expressive large eyes, warm golden hour light, soft bloom, pastel spring palette of white birch, fresh green and lilac, consistent character design, high detail, no text, no watermark.`
- **Только одна героиня:** в каждый промпт добавлять `only one character in the scene, no other people`.
- **Негатив / чего избегать:** `other people, crowd, text, letters, watermark, extra fingers, hands touching face, face distortion, morphing, fast camera spin, photorealistic skin`.
- **Формат:** 16:9, 1920×1080 (Flow отдаёт 720p → апскейл не обязателен). Модель — `Veo 3.1 - Fast` для всех планов, `Veo 3.1 - Quality` только для 4 ключевых (S01, S12, S20, S23).

---

## 3. Героиня и предметы (ЭТАП 1 — `character-design-sheet`)

> ✅ Маша — реальный человек. Её фото лежат в `masha_frames/ref/` и служат референсами для мультяшной версии:
>
> | Файл | Что даёт |
> |---|---|
> | `masha_01_blue_shirt_crop.jpg` | лицо в 3/4, улыбка, голубая рубашка (водяной знак обрезан, оригинал **не использовать**) |
> | `masha_02_steps.jpg` | анфас при дневном свете, тёмные волосы ниже плеч; **стартовый кадр S01** |
> | `masha_03_portrait.jpg` | анфас крупно, мягкая улыбка |
> | `masha_04_river_close.jpg` | улыбка с зубами, волосы на солнце, тонкая цепочка |
> | `masha_05_river_half.jpg` | поясной план у реки, пропорции фигуры, ветер в волосах |

### Мультяшная Маша → `masha_frames/masha_toon_turnaround.png`
**Что переносим с фото (по этим чертам её узнают):**
- **Волосы:** длинные, прямые, ниже плеч, тёмно-каштановые, пробор по центру.
- **Глаза:** карие, тёмные ресницы.
- **Лицо:** светлая кожа, мягкий овал, тёплая широкая улыбка, при улыбке глаза «смеются».
- **Украшения:** тонкая золотая цепочка на шее, кольцо на левой руке.

**Костюм:** светло-голубая рубашка с подвёрнутыми рукавами, светлые джинсы, белые кеды. Вечером (S19–S27) — та же рубашка.

**Промпт карты:**
```
Turn the woman from the attached reference photos into a stylized 3D animated feature film
character. Keep her recognizable: same face shape, warm brown eyes, warm wide smile, long straight
dark chestnut-brown hair below the shoulders with a center part, fair skin, thin gold chain
necklace. Wearing a light sky-blue button-up shirt with rolled sleeves, light blue jeans, white
sneakers. Character turnaround sheet: front, three-quarter, side profile and back view, full body,
plain light background, clean even lighting. Only one character. + STYLE BLOCK
```
Также сделать **лист эмоций** (`masha_toon_expressions.png`), с теми же референсами: спит, удивлена, смеётся, растрогана, закрыла глаза (желание), шепчет.

### Карта предметов → `masha_frames/props_map.png`
- **Солнечный зайчик:** круглое пятно тёплого света с радужным краем.
- **Торт:** белый, с веточками сирени и одной высокой свечой.
- **Гирлянда:** тёплые лампочки на тонком проводе.
- **Ленты:** белые и сиреневые атласные ленты на ветках берёзы.

---

## 4. Раскадровка (ЭТАПЫ 2 и 4)

**Обозначения:**
- **Длит.** — длительность клипа в Flow (`4s / 6s / 8s / 10s`); при монтаже клип подрезается до тайминга, ускорение не используется.
- **Связка:** `chain` = `chain_from_video` (та же локация, последний кадр предыдущего клипа — стартовый); `ref` = новый keyframe + `reference_images` (карта героини); `frames` = стартовый и конечный кадры.
- Промпт видео описывает **только движение** (камера, свет, ветер, естественные жесты), как требует `ПРАВИЛА_КЛИПА.md`.
- В кадре всегда **одна** Маша, других людей нет.

### Пролог и Акт I — «Превращение» и «Утро»

| # | Тайминг | Длит. | Связка | Кадр (keyframe) | Движение (prompt для Veo) |
|---|---|---|---|---|---|
| S01 | 0:00–0:08 | 8s | frames: старт `masha_02_steps.jpg` → конец мультяшная Маша в той же позе | Настоящее фото Маши; солнечный зайчик касается его, фото превращается в мультфильм | `Static camera. A warm sunspot glides onto the photo of the woman; where the light touches, the image transforms smoothly into a stylized 3D animated version of the same woman, same pose, colors bloom, sparkles, she blinks and smiles.` |
| S02 | 0:08–0:14 | 6s | ref | Мультяшная Маша просыпается в кровати, улыбается, садится; окно в цветущий сад | `Slow pull-back from close-up to medium shot. She opens her eyes, smiles softly and sits up; sheer white curtains breathe in the morning breeze.` |
| S03 | 0:14–0:20 | 6s | ref | Маша распахивает деревянное окно, за ним яблони в цвету («Утро светит за окном») | `Camera behind her shoulder, gentle push-in. She opens the old wooden window with both hands, warm sunlight floods the room, blossom petals drift inside.` |
| S04 | 0:20–0:26 | 6s | ref | Деревенская улица без людей, ветер несёт лепестки и белые ленты («Ветер песню нам несёт») | `Smooth tracking shot along a sunny empty village lane, wind carries apple blossom petals and white ribbons through the air, tall grass sways, light flickers through leaves.` |
| S05 | 0:26–0:32 | 6s | ref | Припев 1: Маша выбегает в сад, кружится среди цветущих деревьев | `Medium-wide shot, slow orbit of 30 degrees. She steps into the blooming garden and turns around once, shirt and hair flow in the wind, petals swirl around her.` |
| S06 | 0:32–0:38 | 6s | chain | Крупно: лицо Маши в контровом свете, смеётся («Краше тебя в мире нет») | `Slow push-in to close-up, golden backlight, lens flare blooms behind her head, she laughs naturally, strands of hair glow.` |

### Акт II — «Мир готовит праздник»

| # | Тайминг | Длит. | Связка | Кадр (keyframe) | Движение (prompt для Veo) |
|---|---|---|---|---|---|
| S07 | 0:38–0:46 | 8s | ref | Берёза над рекой, на ветках ленты, Маша касается ствола («Как берёзка над рекой») | `Wide shot, slow crane down from birch branches to her standing by the river, ribbons on branches flutter, sunlight sparkles on the water.` |
| S08 | 0:46–0:52 | 6s | chain | Её отражение в воде, по реке бежит мягкая волна («Счастье ласковой волной») | `Top-down shot of the river surface, her reflection, a gentle wave ripples across, sun glitter dances on the water, slow and calm.` |
| S09 | 0:52–0:58 | 6s | ref | Предприпев 2: Маша бежит через луг, держа длинную сиреневую ленту, ветер поднимает её в воздух | `Tracking shot alongside her running across a flower meadow, a long lilac ribbon in her hand lifts and waves in the wind, grass ripples.` |
| S10 | 0:58–1:06 | 8s | ref | Пустой сад: белая скатерть сама расстилается по длинному столу, вазы с сиренью появляются из лепестков; Маша смотрит удивлённо | `Medium shot, slow dolly sideways. A white tablecloth floats through the air by itself and settles over a long garden table, swirling petals turn into vases of lilac, she watches in delight.` |
| S11 | 1:06–1:12 | 6s | ref | Птицы несут в клювах ленты и обвивают ими берёзы | `Low-angle shot, small songbirds fly between birch trees carrying white and lilac ribbons, wrapping them around branches, ribbons sway.` |
| S12 | 1:12–1:18 | 6s | ref | Конец припева 2: зайчик прыгает с её ладони на тропу, она идёт за ним | `Close-up on her open palm, a warm sunspot sits in it, then slides onto the path ahead; camera follows as she starts walking after it.` |
| S13 | 1:18–1:26 | 8s | ref | Куплет 3: Маша идёт по тропе, и там, где она проходит, распускаются цветы, поворачиваются подсолнухи, оживают бабочки («Ты как солнышко для всех») | `Slow lateral tracking shot following her walk, flowers bloom open as she passes, sunflowers turn toward her, butterflies lift off, warm glow around her.` |
| S14 | 1:26–1:32 | 6s | ref | Куст сирени в цвету, Маша вдыхает аромат («Как весенняя сирень») | `Macro shot of lilac blossoms swaying, rack focus to her face behind the flowers, eyes closed, calm breathing, petals tremble.` |
| S15 | 1:32–1:40 | 8s | ref | Проигрыш с «О-о»: детали — её руки завязывают сиреневый бант, свечи в банках зажигаются сами одна за другой | `Gentle detail shots, close-up of her hands tying a lilac ribbon bow, then candles in glass jars light up by themselves one after another, warm flicker, shallow depth of field.` |
| S16 | 1:40–1:48 | 8s | ref | Маша выходит из-за берёз и видит украшенный сад, зрители видят его через её плечо | `Over-the-shoulder shot, slow push forward between birch trunks revealing a decorated empty garden with lights and a long table, golden late afternoon sun.` |
| S17 | 1:48–1:54 | 6s | chain | Реакция: рука у груди, глаза блестят | `Close-up, static camera, she places one hand on her chest, eyes glisten, a slow surprised smile, warm light on her face.` |
| S18 | 1:54–2:00 | 6s | ref | Маша кружится, раскинув руки, вокруг вихрь лепестков | `Medium shot, camera slightly circles, she spins with arms open, a whirl of petals rises around her, joyful laugh.` |

### Бридж — «Желание»

| # | Тайминг | Длит. | Связка | Кадр (keyframe) | Движение (prompt для Veo) |
|---|---|---|---|---|---|
| S19 | 2:00–2:10 | 10s | ref | Сумерки, синий час. Маша одна под сиренью, первые светлячки, глаза закрыты («Пусть в душе цветёт весна») | `Very slow push-in, blue hour twilight, fireflies drift around her, she stands still with closed eyes making a wish, lilac branches sway softly.` |
| S20 | 2:10–2:18 | 8s | chain | Она открывает глаза, в ладонях загорается тёплый огонёк, зайчик возвращается | `Close-up on cupped hands, a tiny warm glow appears and brightens, lighting her face from below, she opens her eyes and smiles.` |
| S21 | 2:18–2:24 | 6s | ref | Широкий план: сад в сумерках, по проводу одна за другой загораются гирлянды | `Wide static shot of the twilight garden, string lights switch on one by one from left to right, building up to the chorus.` |

### Акт III — «Праздник»

| # | Тайминг | Длит. | Связка | Кадр (keyframe) | Движение (prompt для Veo) |
|---|---|---|---|---|---|
| S22 | 2:24–2:32 | 8s | ref | Финальный припев: Маша стоит в центре сада под гирляндами и поёт, цветы и ветви качаются в ритм | `Wide shot, slow crane up, she stands in the middle of the glowing garden singing joyfully, flowers and branches sway in rhythm, warm bulbs above.` |
| S23 | 2:32–2:40 | 8s | ref | Маша танцует одна, вокруг неё кружат светлячки, гирлянды размываются в боке | `Medium shot, camera orbits slowly around her dancing alone, fireflies circle her like partners, bokeh of string lights, natural dance steps.` |
| S24 | 2:40–2:46 | 6s | ref | Ветер срывает с сирени лепестки и осыпает её «дождём», она смеётся | `Low-angle shot, a gust of wind showers lilac petals over her in slow motion, she laughs looking up.` |
| S25 | 2:46–2:52 | 6s | ref | Тёплое сияние обнимает её, как объятие («Пусть любовь тебя хранит») | `Close-up, static camera, she hugs herself with closed eyes, a soft warm golden glow wraps around her shoulders like an embrace.` |
| S26 | 2:52–2:58 | 6s | ref | Сверху: сад — светящийся островок в тёмном поле, небо с первыми звёздами («удача вслед летит») | `Slow aerial rise above the garden, glowing string lights form a warm island in the dark fields, first stars appear.` |

### Outro — «Шёпот»

| # | Тайминг | Длит. | Связка | Кадр (keyframe) | Движение (prompt для Veo) |
|---|---|---|---|---|---|
| S27 | 2:58–3:07 | 10s | ref | Темнота, торт с сиренью и одной свечой. Маша загадывает желание и задувает свечу, дымок, затемнение («С днём рождения, Маша…») | `Close-up, static camera, candlelight on her face, she closes her eyes, gently blows out the single candle, a thin wisp of smoke rises, fade to darkness.` |

**Итого:** 27 планов, 187 с (сумма таймингов = длительности песни).
**Порядок длительностей:** 10s ×2, 8s ×9, 6s ×16.

---

## 5. Производство в Google Flow

1. **Пре-флайт:** Chrome запущен с портом 9222. В настройке «Vor dem Generieren bestätigen» должно стоять **Immer**; проверить через `flow_credit_balance`.
2. **ЭТАП 1:** сгенерировать `masha_toon_turnaround`, `masha_toon_expressions` и `props_map` с её фото как референсом → показать вам и дождаться утверждения. Утверждённая карта загружается во Flow как персонаж `Masha` (бесплатно) и дальше подставляется в промпты через `@Masha`.
3. **ЭТАП 2:** сгенерировать keyframes `masha_frames/scene_01..27.png` с привязкой карт (для планов `chain` keyframe не нужен).
4. **ЭТАП 3:** контроль сходства и одежды, проверка на артефакты и на лишних людей в кадре.
5. **ЭТАП 4:** `flow_generate_video` строго по одному плану:
   - сначала `auto_confirm=false`, вы видите цену;
   - после вашего «да» — `auto_confirm=true`, `max_credits=20`;
   - результат кладём в `masha_frames/clips/clip_NN.mp4`;
   - из клипа извлекаем кадры на 25 / 50 / 75 % и показываем вам.
6. **Сборка:** каждый клип подрезаем до тайминга, склеиваем без переходов (склейки в долю такта), накладываем MP3 (`-shortest`). Финальный файл: `С днём рождения, Маша — клип.mp4`.

**Бюджет кредитов:** точная цена — по карточке Flow (cost guard). Порядок: 27 клипов, из них 4 на Quality. Заложить около 30 % запаса на перегенерации.

---

## 6. Открытые вопросы
1. ~~Маша — реальный человек?~~ Да, фото в `masha_frames/ref/`. ~~Другие люди?~~ Нет, только она. Стиль — анимация.
2. Вид анимации: 3D, как в полнометражном мультфильме (сейчас), или рисованная 2D / гуашь, как в «Красном шаре»?
