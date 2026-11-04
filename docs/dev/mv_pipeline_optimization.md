# Оптимизация пайплайна AI-музыкальных клипов — глубокий анализ

> **Дата:** 2026-10-10. **Источники:** Perplexity (deep research, medium context) + WebSearch (IP-Adapter/MV-workflow). Применительно к нашему пайплайну: `gen_scenes.sh` → `/api/image/generate` (t2i/i2i, reference_image) → `/api/tasks/simple` i2v (`agnes-video-v2.0`) → ffmpeg trim/concat/mux.
> **См. также:** `docs/dev/mv_style_consistency.md` (стандарт консистентности), `docs/dev/agnes_video_upstream_behavior.md` (поведение upstream).

## 1. Минимизация артефактов i2v

**Выводы:**
- Наша стратегия «статичная камера + минимальное движение» — правильная; дополнение: **одно микро-движение на клип** (не два-три), и описывать движение только то, что реально меняется относительно кейнфрейма.
- Клипы 10–18 с накапливают дрейф: если возможно генерировать короче, чем таргет + запас, а не максимум.
- Структура motion-промпта: (а) субъект/композиция — как в кейнфрейме; (б) свет — один стабильный источник; (в) движение — locked-off camera + 1–2 субтельных движения среды; (г) темпоральность: «smooth, coherent motion; stable edges and textures; consistent exposure and color».
- Лица в крупных планах: неподвижное нейтральное лицо, без речи и поворотов; при критичной идентичности — несколько коротких дублей и отбор чистого сегмента.

**Усиленный базовый negative prompt** (внедрено в `submit2.sh`, v2):
```
flicker, strobing, jitter, frame jumps, ghosting, temporal inconsistency,
morphing, warping, melting edges, crawling textures, shifting background,
changing facial features, distorted face, duplicate subject, extra limbs,
deformed hands, sudden lighting changes, walking, running, camera movement,
camera rotation, spinning, text, subtitles, logo, watermark
```

## 2. Консистентность персонажа/стиля

- **Character sheet** (канон + ракурсы: фронт/3-4/профиль/в рост/лицо) сильнее одного референса; ракурс референса подбирать под ракурс сцены. У нас: `character_ref.png` (scene_02, фронт) — работает; на будущее — добить sheet.
- **Style anchor** — отдельный референс стиля, отличный от референса героя (у нас стиль якорится style-блоком текста + бордюром в промпте).
- **Continuity block** — дословная фраза героя в каждом промпте (у нас: `the same hooded traveler in a long dark coat carrying a warm brass lantern as in the reference image`) — внедрено, дало единообразие в 7 сценах с 1 итерации.
- **Per-shot manifest** — prompt/negative/references/settings/output/in-out точки в JSONL/SQLite для воспроизводимости (у нас частично: `prompts_*.txt` + `shots_*.txt` + `batch*.log`; на будущее — единый manifest с хэшем запроса).
- **Объединяющий грейд** в сборке склеивает смешанные стили (LUT НЕ чинит различие дизайна персонажа, но выравнивает экспозицию/тон/текстуру):
```bash
ffmpeg -i in.mp4 -vf "eq=contrast=1.03:saturation=0.92:gamma=1.00,\
curves=all='0/0.02 0.25/0.24 0.75/0.77 1/0.98',\
noise=alls=4:allf=t+u,vignette=PI/5" -c:v libx264 -crf 18 -preset medium graded.mp4
# (стартовые значения; для постоянного лука — .cube + lut3d)
```
- Внедрено в `assemble2.sh` как финальный проход по нормализованным клипам.

## 3. Автоматический QC клипов (headless)

Порядок гейтов: decode/metadata → black/freeze/scdet → фликер/flow-выбросы → контакт-лист/VLM → человек.

```bash
ffmpeg -hide_banner -i clip.mp4 -vf \
"blackdetect=d=0.25:pix_th=0.08:pic_th=0.98,freezedetect=n=-45dB:d=1.0" \
-an -f null - 2> qc.log
```
- Чёрные интервалы > 0.25 с вне задуманных фейдов — на review; фризы > 1 с в «движущихся» сценах (для наших почти-статичных сцен гейт отключать/ослаблять).
- Luma-скачки между соседними кадрами: `signalstats` YAVG прыжок > 20–25% диапазона — кандидат на фликер.
- MAFD/SSIM соседних кадров: изолированные пики > 3× rolling median — review.
- Optical flow (OpenCV Farnebäck/RAFT): p95 величины потока > 2–3% ширины кадра на кадр — review (дождь/искры дают легитимное движение).
- Внутренние склейки: PySceneDetect / ffmpeg `scdet` — незапланированный cut = брак генерации.
- Внедрено: `qc_clip.sh` (blackdetect+freezedetect) вызывается из `assemble2.sh`.

## 4. Монтаж под бит и переходы

- Битмэп из финального аудио: librosa onset/aubio; крупные смены сцен на сильных долях, спокойные passage — полтакта/такт.
- **Hard cut по умолчанию** (crossfade на дефектах модели даёт double-exposure призраков); dissolve только по мотивации, 6–12 кадров при 24 fps, не поверх лиц.
- Match cut по направлению/цвету/силуэту/позиции субъекта — склейка читается намеренной.
- У нас: сетка склеек = границы секций песни (2.67 с такт при 90 BPM) — соответствует.

## 5. Оркестрация медленных/насыщенных очередей

- Малая капа очереди, spacing сабмитов (у нас 20 с + video-лимитер 1/мин), экспоненциальный backoff с джиттером на 429/5xx (уже в `agnes_video.py`).
- Идемпотентность: стабильный ID сцены + хэш(prompt+references+settings); перед сабмитом — проверка готового артефакта.
- Реестр задач (JSONL/SQLite): shot id, hash, время, provider job id, статус, retry, output, QC.
- Resume: по сохранённому job id; не пересабмитить «висящие» задачи.
- **Иммутабельное версионирование артефактов**: `scene_07/<hash>/raw.mp4` + manifest.json; аппрув через manifest/симлинк, не переименованием. У нас: `clips/` (v1) vs `clips2/` (v2), фолбэк при сборке.
- Разделение generation и finishing: approved-исходники замораживаются, пересобираются только затронутые сцены.

## Источники

- Perplexity research (сводка выше): invideo.io/faq (negative prompts), github.com/Poojan-Desai/r6-creator-ai ADR-006 (ffmpeg-сигналы), nemovideo.com (почему AI-видео выглядит фейково), OSideMedia/higgsfield negative-constraints, hailuoai.video (prompt engineering), forasoft.com (NR quality tools)
- WebSearch: [IP-Adapter (morphic.com)](https://morphic.com) · [ComfyUI IPAdapter walkthrough (ordinaryanimator.com)](https://ordinaryanimator.com) · [DomoAI MV workflow](https://www.domoai.app/make/post) · [Neural Frames](https://www.neuralframes.com/post) · [Midjourney Video docs](https://docs.midjourney.com/37460773864589-Video) · [Neolemon](https://www.neolemon.com/blog)

## Приоритеты (impact/effort для соло-пайплайна)

1. ✅ Короткие/простые генерации + одно движение на клип (уже так)
2. ✅ Character sheet/референс + continuity block (внедрено в v2)
3. ✅ blackdetect/freezedetect QC + контакт-листы (внедрено в assemble2.sh)
4. ✅ Унифицирующий грейд + зерно на финале (внедрено в assemble2.sh)
5. ✅ Версионирование v1/v2 + фолбэк при сборке (внедрено)
6. ⬜ Единый manifest с хэшами запросов (идемпотентный resubmit)
7. ⬜ flow/flicker-гейты (OpenCV) поверх black/freezedetect
8. ⬜ Битмэп-склейки точно на онсеты librosa вместо сетки по секциям
