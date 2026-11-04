# «Пока бьётся» — Карта персонажа, ключевых предметов и матрица референсов (17 сцен)

> **Статус документа**: Производственный эталон (Production Bible) для сборки клипа «Пока бьётся».  
> **Главное правило**: Ни одно видео не генерируется без предварительно созданного кейнфрейма и без прикрепления карты персонажа / референсов предметов к задаче.

---

## 1. Карта персонажа (Character Bible: Путник)

### 1.1. Визуальный канон героя
- **Имя / Роль:** Путник (The Solitary Traveler / Wanderer).
- **Возраст / Внешность:** Мужчина 40–45 лет, обветренное, благородное лицо с глубокими спокойными глазами, перенёсшими большую боль, но сохранившими доброту и сострадание (никакой злобы, агрессии или оскала). Короткая аккуратная тёмная борода с лёгкой проседью.
- **Одежда:** 
  - Длинный дорожный плащ-пальто из грубой шерсти цвета глубокого индиго (`dark indigo wool`).
  - Глубокий капюшон, который в первых сценах скрывает верхнюю часть лица, а в финале откинут назад на рассвете.
  - Подол плаща с лёгкой естественной бахромой от долгих странствий (`subtle raw frayed hem`).
  - Тёмная льняная туника под плащом, кожаный пояс с латунной пряжкой, высокие тёмные кожаные сапоги.
  - На правом запястье — простая льняная повязка (старая рана).
- **Шрамы (Кинцуги):** На груди и предплечьях — следы старых ударов, которые не кровоточат, а затянуты светящимися золотыми прожилками в технике кинцуги (`molten gold kintsugi veins`).

### 1.2. Каноническая строка описания (Character Canon Line)
> Используется **дословно без изменений** во всех промптах, где присутствует герой:
```text
a weathered solitary traveler wearing a dark indigo hooded wool traveler coat with subtle raw frayed hem, gentle empathetic facial expression, calm dignified stance
```

### 1.3. Character Turnaround Sheet (5 ракурсов для эталонного листа)
Файл в проекте: `poka_beatsya_frames/character_ref.png` (и полный лист `character_sheet.png`).

1. **Front Face Close-Up (Анфас, крупный план):**
   ```text
   Character design reference, front face close-up, a 42-year-old weathered solitary traveler, kind tired eyes, subtle salt-and-pepper beard, deep indigo wool hood framing the face, natural skin texture, dramatic chiaroscuro lighting, neutral gentle expression, clean concept art background --ar 1:1
   ```
2. **Three-Quarter View (Три четверти):**
   ```text
   Character design reference, three-quarter view, a weathered solitary traveler wearing a dark indigo hooded wool traveler coat, three-quarter head turn, noble resilient jawline, soft golden rim light on cheek, clean background --ar 1:1
   ```
3. **Side Profile (Строгий профиль):**
   ```text
   Character design reference, side profile portrait, a weathered solitary traveler, hood draped gracefully, sharp distinguished profile, calm resolute gaze toward the horizon, volumetric lighting --ar 1:1
   ```
4. **Back View (Вид со спины):**
   ```text
   Character design reference, full back view, a solitary traveler seen from behind wearing a heavy dark indigo hooded wool coat reaching the calves, raw frayed hem, worn leather belt, standing upright against clean background --ar 1:1
   ```
5. **Full Body Neutral Pose (Полный рост):**
   ```text
   Character design reference, full body turnaround, a weathered solitary traveler standing in neutral dignified posture, dark indigo hooded wool coat, worn dark trousers, rugged leather boots, holding an antique brass lantern at his side, 8k concept art, clean background --ar 9:16
   ```

---

## 2. Карта ключевых предметов клипа (Recurring Props Map)

В клипе «Пока бьётся» есть 4 сквозных предмета-символа, которые обязаны сохранять 100% идентичность формы, материала и деталей во всех 17 сценах.

### Предмет A: Латунный фонарь (The Antique Brass Lantern)
- **Файл-референс:** `poka_beatsya_frames/prop_lantern_ref.png`
- **Материал и форма:** Старинный цилиндрический фонарь из кованой латуни с бронзовой патиной и тёмными заклёпками. Толстое гранёное стекло со следами дождевых капель. Внутри — восковая свеча, пламя которой пульсирует в ритме 90 BPM (сердцебиение).
- **Смысл:** Внешний огонёк надежды, который в финале путник задувает, потому что зажёг огонь внутри себя.
- **Prop Canon Line:**
  ```text
  an antique cylindrical brass lantern with aged bronze patina and thick glass cylinder, holding a warm glowing amber candlelight pulsating rhythmically at 90 BPM
  ```

### Предмет B: Золотое сердце и швы Кинцуги (Kintsugi Heart & Veins)
- **Файл-референс:** `poka_beatsya_frames/heart_sprite.png` / `prop_kintsugi_ref.png`
- **Материал и форма:** Анатомически-поэтический символ сердца и ветвящиеся прожилки жидкого золота (кинцуги), заполняющие разломы на одежде, теле и камне. Золото имеет тёплое, солнечное свечение с искрами.
- **Смысл:** «В каждом шраме жизнь и любовь» — боль, превращённая в искусство и силу духа.
- **Prop Canon Line:**
  ```text
  sacred glowing molten gold kintsugi veins branching across fractures, emitting a warm incandescent golden glow like liquid sunlight
  ```

### Предмет C: Окаменевшие обидчики и нож (Petrified Statues & Obsidian Dagger)
- **Файл-референс:** `poka_beatsya_frames/prop_statue_knife_ref.png`
- **Материал и форма:** Статуи людей из шероховатого сланцево-серого камня с застывшими лживыми улыбками. В руке одной из статуй — полированный тёмный кинжал с холодным лезвием. При касании путника камень не разбивается, а исцеляется золотой нитью.
- **Смысл:** «Кто был рядом, стал врагом, улыбался, бил ножом» — преодоление обиды через прощение.
- **Prop Canon Line:**
  ```text
  a weathered slate-grey stone statue with a treacherous frozen smile holding a cold sharp dark dagger, slate texture with fine moss
  ```

### Предмет D: Маяк на скале (The Coastal Lighthouse)
- **Файл-референс:** `poka_beatsya_frames/prop_lighthouse_ref.png`
- **Материал и форма:** Монументальный белый каменный маяк цилиндрической формы с узкими окнами и тёмно-синим куполом на вершине отвесной морской скалы. Линза Френеля излучает устойчивый, прямой луч света в ночное море.
- **Смысл:** «Я иду на свой маяк» — путеводная звезда и финальная цель путешествия.
- **Prop Canon Line:**
  ```text
  an ancient solitary white and indigo cylindrical stone lighthouse standing on a dramatic coastal cliff over a dark stormy ocean, emitting a piercing volumetric beam of light
  ```

---

## 3. Матрица привязки референсов для всех 17 сцен (Reference Conditioning Matrix)

Перед запуском генерации видео (i2v) для каждого фрагмента строго проверяется привязка:
1. `Primary Video Reference` = кейнфрейм сцены (`scene_XX.png`).
2. `Identity & Prop References` = эталоны персонажа и предметов.

| Сцена | Тайминг | Длит. | Текст / Музыка | Кейнфрейм (Primary) | Референс героя | Референс предмета | Что оживает в видео (i2v) |
|---|---|---|---|---|---|---|---|
| **01** | 0:00–0:02 | 2.0s | Удар-вспышка | `scene_01.png` | `character_ref.png` (силуэт) | `prop_lantern_ref.png` | Вспышка молнии 0.5s, капли дождя |
| **02** | 0:02–0:16 | 14.0s | Интро (тихое) | `scene_02.png` | `character_ref.png` (полный рост) | `prop_lantern_ref.png` | Пульс свечи в фонаре 90 BPM, дрейф тумана |
| **03** | 0:16–0:26 | 10.0s | V1: «Кровь течёт…» | `scene_03.png` | `character_ref.png` (спина/3/4) | `prop_statue_knife_ref.png` | Косой дождь, отблеск капель на камне |
| **04** | 0:26–0:35 | 9.0s | CH1: «Я хочу жить!» | `scene_04.png` | `character_ref.png` (вдали) | `prop_lighthouse_ref.png` | Прорыв луча сквозь тучи к горизонту |
| **05** | 0:35–0:45 | 10.0s | V2: «Улыбался, бил ножом» | `scene_05.png` | `character_ref.png` (рука) | `prop_statue_knife_ref.png` + `prop_kintsugi_ref.png` | Медленное разгорание золотого шва на камне |
| **06** | 0:45–0:56 | 11.0s | CH2: «Пока бьётся…» | `scene_06.png` | `character_ref.png` (спина) | `prop_lantern_ref.png` + `heart_sprite.png` | Мерцание углей под ногами, тёплый дым |
| **07** | 0:56–1:00 | 4.0s | Интерлюдия (пауза) | `scene_07.png` | — (космос/небо) | `prop_lantern_ref.png` (точка) | Едва заметное мерцание звёзд и точки света |
| **08** | 1:00–1:11 | 11.0s | V3: «Свой маяк…» | `scene_08.png` | `character_ref.png` (силуэт) | `prop_lighthouse_ref.png` | Падающие снежинки в луче фонаря |
| **09** | 1:11–1:22 | 11.0s | V4: «В каждом шраме…» | `scene_09.png` | `character_ref.png` (грудь крупно) | `prop_kintsugi_ref.png` + `heart_sprite.png` | Пульсирующее свечение золотых швов на ветру |
| **10** | 1:22–1:31 | 9.0s | Final: «Я ранен, но иду» | `scene_10.png` | `character_ref.png` (лицо анфас) | `prop_lantern_ref.png` | Первые лучи зари на щеке, трепетание волос |
| **11** | 1:31–1:45 | 14.0s | Соло гитары | `scene_11.png` | — (макро стекла) | `prop_lantern_ref.png` + `prop_lighthouse_ref.png` | Капли медленно стекают по стеклу, блики огня |
| **12** | 1:45–2:04 | 19.0s | Припев I: «Я хочу жить!» | `scene_12.png` | `character_ref.png` (на скале) | `prop_lighthouse_ref.png` | Всплески волн о скалы, водяная пыль в золоте |
| **13** | 2:04–2:19 | 15.0s | Припев II | `scene_13.png` | `character_ref.png` (на пирсе) | `prop_lantern_ref.png` | Золотые блики на мокрых плитах пирса |
| **14** | 2:19–2:25 | 6.0s | Брейкдаун: «Ещё чуть-чуть»| `scene_14.png` | — (два огня) | `prop_lantern_ref.png` + `prop_lighthouse_ref.png` | Синхронный пульс фонаря и маяка в темноте |
| **15** | 2:25–2:51 | 26.0s | Последний припев | `scene_15.png` | `character_ref.png` (во весь рост) | `prop_kintsugi_ref.png` | Золотые лучи солнца, искры золотой пыли в воздухе |
| **16** | 2:51–3:01 | 10.0s | «Я не сдамся, я дойду!» | `scene_16.png` | `character_ref.png` (профиль/рука) | `prop_lantern_ref.png` + `heart_sprite.png` | Дымок от задутой свечи, сияние из груди |
| **17** | 3:01–3:07 | 6.4s | Кода (затухание) | `scene_17.png` | — (пейзаж горизонта) | `prop_lighthouse_ref.png` | Плавное угасание в мягкий белый утренний свет |

---

## 4. Единый протокол запуска генераций

### 4.1. Генерация кейнфреймов (Image API)
```bash
# Пример вызова для сцены с героем:
curl -X POST http://localhost:8765/api/image/generate \
  -F "prompt=${STYLE_BLOCK} | ${CHARACTER_CANON} ... ${SCENE_PROMPT}" \
  -F "reference_image=@poka_beatsya_frames/character_ref.png" \
  -F "width=1280" -F "height=720"
```

### 4.2. Генерация видеофрагментов (Video i2v API)
```bash
# Обязательное прикрепление кейнфрейма сцены как базового референса:
curl -X POST http://localhost:8765/api/video/submit \
  -F "reference_image=@poka_beatsya_frames/scene_02.png" \
  -F "mode=i2v" \
  -F "prompt=Static locked camera. Solitary traveler motionless. Only amber candlelight inside the brass lantern pulsing at 90 BPM, gentle misty fog drifting across the ground." \
  -F "negative_prompt=walking, running, gait, limb movement, head turn, camera pan, camera zoom, morphing, face distortion, changing clothes" \
  -F "duration=14"
```

---

## 5. Итог: Что этот стандарт даёт проекту

1. **Никаких "случайных" лиц:** Путник в сцене 02, сцене 05, сцене 10 и сцене 16 — это один и тот же человек с одинаковым плащом, бородой и глазами.
2. **Никаких "прыгающих" предметов:** Латунный фонарь, кинжал, маяк и золотые швы имеют одну геометрию и фактуру.
3. **Безопасность от брака:** Прежде чем потратить ресурсы на рендер видео, режиссёр видит полную раскладку 17 статичных картин на контакт-листе и утверждает их.
