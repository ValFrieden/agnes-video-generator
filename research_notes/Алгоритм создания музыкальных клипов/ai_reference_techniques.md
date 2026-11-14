# Референсы для AI-видео: как делать свой клип с помощью готовых клипов и картинок

Дата исследования: 2026-11-07. Проект: клипы с персонажем «Маша» (лист персонажа), Google Flow (Veo 3.1 / Gemini Omni Flash) и Kling через MCP.

**Происхождение данных.** WebSearch и WebFetch во время сессии не работали (ошибка модели), поэтому почти всё ниже найдено через **Perplexity** (`perplexity_research` x1, `perplexity_ask` x7, `perplexity_search` x6). Пометка **[P]** означает, что находка и её URL пришли из Perplexity. Пометка **[MCP]** означает, что это прочитано из локальных схем инструментов Kling MCP (не из веба). Всё, что относится к периоду до 2025 года, помечено **(возможно устарело)**.

Цены и лимиты меняются каждый месяц. Перед тем как запускать генерацию, сверяйте их с интерфейсом и с `who_am_i` / `query_membership_and_credits` в MCP.

---

## 0. Главные изменения конца 2026 года (влияют на пайплайн)

- **Kling 4.0** вышел 15.10.2026 [P]. Omni Reference: до **15 ассетов** за одну задачу (до 10 изображений, до 5 видео общей длиной ≤30 с, до 7 субъектов, из них до 3 видео-субъектов, плюс голос). До **10 ключевых кадров**, генерация 3–30 с, multi-shot включён по умолчанию, промпт до 8000 токенов, 4K и 21:9. В качестве референса принимаются **«white-model» (болванка) и видео карт глубины** [P]. Omni Reference и Keyframes **нельзя совмещать в одной задаче** [P]. Kling 4.0 подключён к Kling MCP и CLI [P].
  - Источники: https://ir.kuaishou.com/news-releases/news-release-details/kling-ai-officially-launches-next-generation-kling-40-raising · https://kling.ai/quickstart/kling-4-model-user-guide · https://kling.ai/blog/kling-4-vs-3
  - **Kling 4.0 Flash** (релиз 04.11.2026): 3–20 с, 720p, до 10 изображений и 5 видео, суммарно ≤20 с видео, в промпте ссылки `@image_1` / `@video_1` [P] https://docs.empiriolabs.ai/models/kling-4-0-flash
  - Тарифы API (Units/с) [P], https://kling.ai/document-api/pricing/base/video :

    | Модель | 720p | 1080p |
    |---|---|---|
    | 4.0 без видео | 1.0 | 1.5 |
    | 4.0 с видео | 0.6 | 0.9 |
    | Flash без видео | 0.6 | нет |
    | Flash с видео | 0.4 | нет |

    **Подвох:** при видео-входе тарифицируемая длительность равна **2 × output**, а если вход длиннее выхода, то **input + output**. Сколько это стоит в кредитах приложения, Perplexity не подтвердил.
  - **Отдельного Motion Control для 4.0 в прайсе нет.** Motion Control остаётся на 3.0 / 2.6 [P].
- **Google Flow, 05.11.2026: Veo Extend отключён.** Замена: **Omni Extend** на **Gemini Omni Flash 1.2**. Добавляет 3–10 с, до 3 референс-изображений, только для Plus/Pro/Ultra [P] https://support.google.com/flow/answer/16352836
- **Gemini Omni Flash 1.2 в Flow** принимает **видео как ингредиент/референс** (Google указывает, что видео-референс до ~3 с, это нужно проверить в интерфейсе) [P].
  - References-to-video: 3–10 с для всех, 3–15 с для подписчиков.
  - **Video Edit:** MOV/MP4/AVI/WMV до 60 с и 1 ГБ, ролик длиннее 30 с нужно обрезать до 30 с.
  - Кредиты: 1 кр/с при 360p, **3 кр/с при 720p** (секунды 11–15 стоят 2 и 6 кр/с) [P] https://support.google.com/flow/answer/16935718 · https://support.google.com/flow/answer/16526234
- **Sora 2 закрыта:** приложение и веб с апреля 2026, API с сентября 2026. Cameo и Remix больше недоступны [P] https://help.openai.com/en/articles/20001152-what-to-know-about-the-sora-discontinuation

---

## 1. Перенос движения (motion transfer / performance capture)

Все цифры ниже из [P] (perplexity_research + search), URL указаны в строках.

| Инструмент | Вход | Лимиты | Что сохраняет | Цена | Типичные сбои |
|---|---|---|---|---|---|
| **Kling 3.0 Motion Control** | 1 картинка персонажа + 1 driving-видео (или motionId из Motion Library) | 3–30 с при orientation=video, 3–10 с при orientation=image. mp4/mov ≤100 МБ, стороны 340–3850 px. Выход 720p/1080p, длина равна длине референса (параметра duration нет) | Тело, жесты, мимика, рот, тайминг; можно оставить исходный звук (`keep_original_sound`). При orientation=video также ракурс и камера исполнителя. **Element Binding (лицо) работает только при orientation=video**, допускается только 1 элемент | App: **9 кр/с Std, 12 кр/с Pro** (округление до целой секунды). fal $0.168/с, HiAPI $0.10/с (720p) | Склейки и движение камеры в референсе приводят к обрезке. Быстрые движения дают более короткий выход, **кредиты не возвращаются**. Берётся только самый крупный человек в кадре. Лицо «плывёт» (кости, тон кожи) |
| **Kling 2.6 Motion Control** | то же | то же | то же | 5 / 8 кр/с | то же |
| **Kling O1 / 3.0 Omni** (feature- или base-видео) | В 3.0 Omni: 1 видео 3–15.5 с (API) + до 4 изображений/элементов. Видео-элемент персонажа собирается из клипа 3–8 с | Выход до 15 с | Feature-видео ведёт действие и камеру, base-видео редактируется. Это **не** детерминированный mocap | 3.0 Omni с видео: 12 кр/с (720p), 16 кр/с (1080p) | Дрейф лица и движения. Конфликт референсов. В приложении старый гайд пишет лимит 10 с |
| **Runway Act-Two** | driving-видео + 1 изображение **или** видео персонажа | до 30 с, минимум 3 с | Лицо, мимика, речь, тайминг. С изображением ещё и жесты; с видео персонажа сохраняются его фон и камера | **5 кр/с**. По состоянию на ноябрь 2026 доступен [P] | Один персонаж. Несовпадение позы и кадрирования, стилизованная анатомия |
| **Runway Aleph 2.0** (edit) | видео + промпт + до 5 ключевых изображений с таймкодами | 2–30 с, 480p–1080p, 24–30 fps, ≤10 склеек | Локальная замена персонажа или объекта при сохранении движения, камеры и звука | **28 кр/с**, минимум 56 | Нежелательные правки расползаются. 11+ склеек дают ошибку. Gen-4 Aleph v1: куски по 5 с, 15 кр/с |
| **Luma Ray3 / Ray3.2 Modify** | видео + 1 изображение персонажа + старт/энд-кадры | Ray3.2: до 20 с при 24 fps (15 с при 30 fps). Ray2: 10 с | Режимы `adhere_1…reimagine_3`: adhere держит структуру, reimagine трансформирует | Ray3.2 V2V: 36/48/72/144 кр/с (360p–1080p) | Чем выше strength, тем сильнее теряются камера и поза. В Ray3 «end»-кадр для клипа длиннее 5 с берётся с отметки 0:05 |
| **Wan 2.2 Animate** (open, Apache-2.0) | картинка + driving-видео, ComfyUI сам извлекает позу и лицо | Около 77 кадров на сегмент (~4.8 с при 16 fps), сегменты цепляются, 720p | **Move**: анимировать картинку. **Mix/Replace**: заменить человека в исходном видео, сохранив сцену, камеру и свет | Бесплатно локально (нужен GPU) | Ошибки извлечения позы, швы между сегментами, VRAM. https://docs.comfy.org/tutorials/video/wan/wan2-2-animate · https://github.com/Wan-Video/Wan2.2 |
| **Seedance 2.0** (ByteDance) | до 9 изображений + 3 видео + 3 аудио (≤12 файлов), видео суммарно 2–15 с | выход 4–15 с | Ведёт персонажа, движение, камеру, стиль, голос. Есть multi-shot. Движение **интерпретируется**, а не копируется | fal: ~$0.18 за billable-секунду с видео (input+output) | Конфликт референсов. BytePlus ограничивает референсы с реальными лицами. https://fal.ai/models/bytedance/seedance-2.0/reference-to-video |
| **MiniMax H3** (ref-video) | до 9 изображений + 3 видео (каждое 2–15 с, суммарно ≤15 с) | 4–15 с, 768p/2K | Персонаж, движение, камера, ритм монтажа | $0.08/с выход + $0.08/с вход | https://platform.minimax.io/docs/guides/video-generation |
| **Hailuo S2V-01** (возможно устарело) | только 1 фото лица, видео на вход не принимает | 6 с, 720p | Только идентичность | ~$0.64 за 6 с (реселлер) | На официальном прайсе MiniMax уже не указан |
| **Viggle Mix/Animate** | картинка (API: до 5) + driving-видео 5–15 с (API) | Загрузка на сайте: 1 мин free / 10 мин paid | Перенос перформанса, альфа-маска | API $0.06–0.08 за секунду driving-видео | Окклюзия, несколько людей. https://viggle.ai/developers |
| **DomoAI Character-to-Video / V2V** | картинка ≤10 МБ + клип | до 30 с (20/30 с на старших планах) | Режим Subject Only оставляет фон. V2V рестайлит с сохранением звука | Relax-режим без кредитов на части планов. API 5 кр/с ($0.10/с) | https://www.domoai.app/create/move |
| **Higgsfield Recast** | исходное видео 5–15 с + целевой персонаж | — | Заменяет персонажа, камера, фон и тайминг остаются. Есть клон голоса | в интерфейсе | Резкие повороты головы, профиль. https://higgsfield.ai/blog/AI-Face-Character-Swap-in-Video-Photo-PRO-Guide |
| **Higgsfield Genjutsu** (Motion Transfer / Object Swap) | 1 видео 4–30 с + до 30 изображений | до 1080p. Light API берёт только первые 15 с | Движение, камера, тайминг, звук | 15 с 720p = 105 кр, 1080p = 300 кр | Пересобранная сцена меняет планировку. https://higgsfield.ai/blog/higgsfield-genjutsu |
| **Pikaswaps** | видео + 1 референс + маска или описание области | 5/10 с, 720p/1080p | Меняет объект или субъект, сцена остаётся | API $0.03 за запрос | Края маски, быстрые движения. https://dev.pika.art/models/pika/pikaswaps/video-to-video |

**Вывод для Маши.** Чтобы точно скопировать хореографию или жест одного исполнителя, берите Kling 3.0 Motion Control (orientation=video + Element Binding лица Маши). Чтобы взять у референса ритм, композицию и камеру, но придумать сцену заново, берите **Kling 4.0 Omni Reference** (видео + лист + элементы) или Seedance 2.0. Чтобы заменить человека в чужом кадре с сохранением камеры, подойдут Aleph 2.0, Wan Animate Replace или Higgsfield Recast.

---

## 2. Google Flow / Veo 3.1: что умеет с референсами [P]

- **Frames to Video** (первый и последний кадр): 4/6/8 с. Задаёт концы, середину и исполнение **не фиксирует**.
- **Ingredients / References to Video:** до **3** изображений, только 8 с. Lite/Fast: 10/20 кр (на Ultra вдвое дешевле), Quality: 100 кр. В API: `reference_images`, промпт до 1024 токенов. В Flow ингредиент добавляется через `@`.
- Veo **не умеет** перенос движения из driving-видео. Видео на вход в Flow теперь принимает **Gemini Omni Flash** (референс и Video Edit, см. раздел 0).
- Шаблон промпта от Google: «Using the provided images for [X], [Y] and the [setting], create a …». Ингредиенты должны быть 1–3 чистыми, хорошо освещёнными изображениями **одного** субъекта, иначе идентичность дрейфует. 1080p/4K и референсы требуют длительности 8 с, Extend ограничен 720p.
- Источники: https://support.google.com/flow/answer/16893917 · https://developers.googleblog.com/en/introducing-veo-3-1-and-new-creative-capabilities-in-the-gemini-api/ · https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1 · https://github.com/raphaelbgr/ai-video-prompting/blob/main/docs/google-flow-veo-playbook.md
- В Google Cloud есть отдельный Veo Extend (вход 1–30 с, прибавляет +7 с). Это **не Flow**.

---

## 3. Копирование камеры из референса

| Метод | Как работает | Ограничения |
|---|---|---|
| **Kling 4.0 Omni Reference** (видео как референс камеры и ритма, плюс depth/white-model) [P] | В промпте прямо: «@Video1: reference camera movement and pacing» | Это генеративная аппроксимация, а не точный повтор |
| **Kling 3.0 Motion Control, orientation=video** [P] | Повторяет ориентацию и камеру исполнителя | Официально рекомендует референс **без** движения камеры, иначе возможна обрезка |
| **Kling 3.0 advanced camera control / Motion Brush** (Pro) [P] | Пресеты, enum'ы, рисование траектории | Камеру из чужого видео не извлекает |
| **Higgsfield Cinema Studio**: 30+ пресетов камеры [P] | Направляет камеру в *новом* шоте | Камеру референса не копирует |
| **Uni3C** (Alibaba DAMO, Wan 2.1 I2V 14B) [P] | Извлекает 3D-камеру и сцену из исходного видео и кондиционирует I2V. 81 кадр, 16 fps | Ошибки оценки глубины и камеры на блюре и склейках, новые ракурсы приходится «додумывать». https://github.com/alibaba-damo-academy/Uni3C |
| **ReCamMaster** (KwaiVGI, Wan 2.1) [P] | Пересъёмка *исходного* видео по одной из 10 траекторий (pan, tilt, zoom, arc). Нужно ≥81 кадра | Не переносит камеру на другой контент. https://github.com/KwaiVGI/ReCamMaster |
| **Wan 2.2 Fun Camera** [P] | Пресеты через `WanCameraEmbedding`, 81 кадр. На 4090D при FP8 занимает ~84% VRAM | Только пресеты. https://docs.comfy.org/tutorials/video/wan/wan2-2-fun-camera |
| **Wan-Move / ATI** [P] | Траектории точек и объектов | Это не камера |
| **LTX-2.3 IC-LoRA Union** (canny + depth + pose), IC-LoRA motion-track [P] | Позиционно выровненное контрольное видео (depth референса) задаёт геометрию и камеру. Есть звук | Нужна GPU с 32 ГБ+ VRAM. https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Union-Control · https://github.com/Lightricks/ComfyUI-LTXVideo · https://docs.comfy.org/tutorials/video/ltx/ltx-2 |
| **Wan 2.1 VACE** (depth/pose/mask control) [P] | Контрольное видео плюс референс. 81 кадр ≈5 с. Нативная нода берёт только **первый** референс | https://docs.comfy.org/built-in-nodes/WanVaceToVideo · https://github.com/Wan-Video/Wan2.1 |

Все Wan-модели в ComfyUI собраны в одной обёртке kijai: **ComfyUI-WanVideoWrapper** (Uni3C, ReCamMaster, VACE, Animate, Fun Camera, Wan-Move, SCAIL) https://github.com/kijai/ComfyUI-WanVideoWrapper [P].
AnimateDiff и ControlNet для SD1.5 **(возможно устарело)**: в 2026 году их вытеснили VACE и LTX IC-LoRA.

---

## 4. Рестайл, video-to-video и цепочки кадров

- **V2V-рестайл чужого клипа:** Luma Modify (adhere/flex/reimagine), Aleph 2.0, Kling 4.0 edit (до 5 видео, суммарно ≤30 с; правит мимику, движение, персонажа, фон, камеру, стиль, погоду), DomoAI V2V, Gemini Omni Flash Video Edit в Flow [P].
- **Цепочка «последний кадр → первый кадр»:** следующий шот начинается с последнего кадра предыдущего. На Reddit предупреждают, что апскейл этого кадра может дать заметный шов [P] (https://www.reddit.com/r/KlingAI_Videos/comments/1seneno/). Extend в Flow достраивает от последней секунды клипа.
- **Стоп-кадр из референса как композиционный гид («first-frame swap»)** [P] https://aipicturesque.com/blog/motion-control-first-frame-workflow-picturesque :
  1. Через ffmpeg взять кадр 0 референса, на котором исполнитель целиком в кадре и движение ещё не разогналось.
  2. В Nano Banana Pro: reference 1 = этот кадр, reference 2 = Маша. Промпт: *«Replace the person in reference 1 with the character from reference 2. Keep exact pose, camera angle, background, lighting… Preserve hands, feet, and limb positions. Do not change the environment.»* Соотношение сторон как у референса.
  3. Проверить: нет «призрачных» конечностей, ступни совпадают с точками опоры.
  4. Kling Motion Control: композит + **исходный** референс, orientation в ту же сторону, что в композите.
  - Этот же приём показан в YouTube-уроке Akshay Bhatti (декабрь 2025) [P] https://www.youtube.com/watch?v=-iXJ0GwYS4w и в обзоре Curious Refuge, где сказано, что нужно 5–6 попыток [P] https://curiousrefuge.com/blog/kling-26-motion-control-review

---

## 5. Сохранение персонажа

**Лист персонажа** [P] (https://kling.ai/quickstart/ai-video-character-consistency · https://www.dreamdrive.ai/learn/kling/kling-elements-consistent-characters/):
- 3–4 **отдельных** файла: анфас, 3/4, профиль, при необходимости спина, плюс крупный план лица. Нейтральный фон, ровный свет, один и тот же костюм, без подписей и стрелок.
- Если подать сетку turnaround одним файлом, растёт риск, что раскладка листа проявится в кадре или **появятся несколько копий персонажа**. Kling 4.0 официально принимает three-view листы и сетки, но для Veo и 3.0 надёжнее отдельные файлы.
- В Kling 4.0 каждому ассету явно назначайте роль: «@Image1: preserve the character's appearance», «@Video1: reference the action pacing». Без этого модель угадывает роли сама [P].

**Kling Elements** [MCP]:
- Image-субъект: cover + 1–3 дополнительных изображения.
- Video-субъект: 3–60 с, fps > 23.8, короткая сторона ≥700 px, без HDR. Video-субъекты работают **только** с `kling-video-v3_0_omni` / `kling-video-v3_0` (image_to_video); с O1 и text-to-video не работают.
- В Omni-промпте элемент пишется как `<<<id>>>`, видео как `video_1..video_5`.
- Motion Library (`motion_library_list`) хранит готовые движения, их можно передавать в `motion_control` как `motionId`.

**LoRA персонажа** (для open-source: Wan 2.2 или LTX) [P]:
- 15–25 изображений (возможный диапазон 9–40), разнообразие поз, ракурсов и эмоций важнее разнообразия фонов. Без водяных знаков и текста, без почти одинаковых кадров.
- Для Wan 2.2 сначала тренировать **low-noise** модель: rank 16–32, LR ~5e-5, 1200–2000 шагов, разрешение 512, короткий триггер-токен.
- Инструменты: musubi-tuner, ostris AI Toolkit, DiffSynth-Studio. https://github.com/DavidJBarnes/wan22-character-lora/blob/main/GUIDELINES.md · https://github.com/kohya-ss/musubi-tuner · https://github.com/ostris/ai-toolkit
- Для облачных Kling/Veo LoRA не нужна: её роль выполняют лист и элементы.

**Типичные сбои и что с ними делать** [P]:
- *Дрейф лица в Motion Control* (кости, тон кожи, «превращение» посреди клипа). Совет с Reddit: использовать Element Binding, доводить исходную картинку (Magnific), либо брать Kling Omni 3/4 со стартовым кадром из Nano Banana [P] https://www.reddit.com/r/generativeAI/comments/1t2kajb/
- *Дрейф костюма.* Костюм должен быть одинаковым во всех референсах и описываться в промпте одними и теми же словами.
- *Новая «версия» персонажа в каждом шоте.* Держать **один эталонный референс** на персонажа и не менять у него свет и кроп [P] https://www.reddit.com/r/KlingAI_Videos/comments/1seneno/
- *Руки и мелкие детали.* Проверять каждый дубль, это не решено.
- *Персонаж «говорит», хотя не должен.* Motion Control переносит движения рта из референса, поэтому нужен референс с закрытым ртом или клип без пения. Veo, Kling 4.0 и Seedance генерируют звук и губы, поэтому в промпт добавлять «mouth closed, not speaking, lips still», а звук отключать или добавлять «no dialogue». Источника, где это прицельно тестировали бы, Perplexity не нашёл.

---

## 6. Пайплайн «от референса к шоту» для клипа

1. **Разбор референса.** Нарезка по склейкам, ключевые кадры (фазы позы), длительность каждого шота в битах (BPM трека), тип камеры (push-in, orbit, handheld), свет.
2. **Решение по каждому шоту:**
   - Нужна точная хореография или жест → путь A (Motion Control).
   - Нужны ритм, композиция и камера, сцена своя → путь B (Kling 4.0 Omni / Seedance 2.0 / Omni Flash с видео-референсом).
   - Пейзаж или камера без Маши → Veo Fast, frames-to-video.
3. **Стартовый кадр.** Nano Banana Pro: кадр референса + лист Маши (приём first-frame swap из раздела 4). Соотношение сторон как у финального клипа.
4. **Анимация.**
   - A: Kling 3.0 MC, orientation=video, Element Binding лица Маши, референс без склеек, обрезанный до нужной длины (тарификация посекундная).
   - B: Omni Reference, где @Image или Element — Маша, @Video — камера и ритм. Роли прописывать явно.
5. **Сшивка шотов.** Последний кадр становится первым следующего (без апскейла); Omni Extend в Flow.
6. **Монтаж по битам.** Каждый шот генерировать с запасом около 0.5–1 с по длительности.
7. **Пост.** Аккуратный face-fix только при необходимости. По FaceFusion и Higgsfield face swap Perplexity источников не дал.

Реальные примеры авторов [P]:
- Еженедельные AI-клипы: Kling для атмосферы, повторяющийся персонаж через Seedance 2.0 (один эталонный кадр на все шоты), монтаж кадр-в-кадр под трек https://www.reddit.com/r/KlingAI_Videos/comments/1slm341/
- Связка «Nano Banana Pro → Kling 3.0» https://www.reddit.com/r/KlingAI_Videos/comments/1rx17eo/
- Aze Alter (лист 4–6 ракурсов, ракурс выбирается под шот, затем Kling/Seedance), цитируется в https://aivideobootcamp.com/blog/cinematic-ai-video-prompts-2026/
- Гайд Kling по музыкальным клипам: https://kling.ai/feature/ai-music-video-generator
- Отдельных воркфлоу победителей Runway AIFF и Project Odyssey Perplexity **не подтвердил**, поэтому не цитирую.

---

## 7. Шаблоны промптов

- **Kling 4.0 Omni:** «@Image1 (or <<<masha_id>>>): preserve Masha's face, hair and outfit exactly. @Video1: reference only the camera movement, shot composition and pacing; do not copy the person or setting. New setting: … Masha's mouth stays closed, she does not speak or sing, lips do not move.»
- **Kling Motion Control:** короткий промпт про сцену и свет. Движение задаёт видео, внешность задаёт картинка или элемент.
- **Veo Ingredients:** «Using the provided images for Masha [and the setting], create a medium shot … camera slowly pushes in … Masha keeps her mouth closed, no speech.»
- **Frames to Video:** описывать переход и камеру между двумя кадрами («smooth 180-degree arc shot from … to …»).
- **Nano Banana swap:** см. раздел 4.

---

## 8. ToS и права (кратко; подробно разбирает другой исследователь) [P]

- Kling, Runway, Luma и Higgsfield требуют, чтобы у пользователя были права на загружаемые материалы. **Ответственность лежит на пользователе**, а платформы получают широкую лицензию на входные данные (Runway, в частности, для обучения моделей).
  - https://kling.ai/docs/user-policy · https://runway.com/terms-ofuse · https://luma.ai/content-policy · https://higgsfield.ai/trust
- Luma требует явного согласия человека на использование изображений реальных людей. BytePlus (Seedance) ограничивает референсы с реальными лицами.
- Google Generative AI Prohibited Use Policy запрещает нарушать чужие IP и приватность и использовать биометрию без согласия: https://policies.google.com/terms/generative-ai/use-policy
- ToS YouTube запрещают скачивать и переиспользовать контент без разрешения: https://kids.youtube.com/t/terms
- То, что видео используется лишь «как референс», права не даёт.
- **Практически.** Самые безопасные driving-видео — те, что вы сняли сами (себя или актёра с согласием), библиотека движений Kling или лицензированные стоки. Чужие клипы лучше использовать для разбора (тайминг, камера, раскадровка), а не загружать в генераторы. Kling 4.0 прямо рекламирует «recreation» чужих роликов, но права это не снимает.
